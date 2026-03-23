from kubernetes import client, config
import uuid

# function to create a pod for a lab session
def create_lab_pod(lab_name: str, image: str, port: int):
    
    # load kubeconfig - connects to the minikube cluster
    try:
        config.load_incluster_config()  # for when the FastAPI app is running inside the cluster
    except config.ConfigException:
        config.load_kube_config()
    
    # create a unique pod name
    unique_id = str(uuid.uuid4())[:8]  # generate a unique ID
    pod_name = f"{lab_name.lower().replace(' ', '-')}-{unique_id}"  # e.g. "python-lab-1a2b3c4d"
    lab_label = lab_name.lower().replace(' ', '-')
    
    # define the pod
    pod = client.V1Pod(  # K8s API object that represents a pod
        metadata=client.V1ObjectMeta(
            name=pod_name,
            labels={"app": "kuberange-lab", "lab": lab_label}  
        ),
        spec=client.V1PodSpec( 
            containers=[
                client.V1Container(
                    name=pod_name,
                    image=image,
                    ports=[client.V1ContainerPort(container_port=port)]
                )
            ]
        )
    )

    # create the pod in kubernetes
    v1 = client.CoreV1Api()
    v1.create_namespaced_pod(namespace="default", body=pod)

    # build the URL - Needs refinement
    url = f"http://localhost:{port}"

    return pod_name, url

# function to delete a pod by name
def delete_lab_pod(pod_name: str):
    
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()

    v1 = client.CoreV1Api()
    v1.delete_namespaced_pod(
        name=pod_name,
        namespace="default"
    )