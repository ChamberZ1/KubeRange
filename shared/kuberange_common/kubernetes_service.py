from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
import uuid

def _load_k8s_config():
    try:
        config.load_incluster_config()
    except config.ConfigException:
        try:
            config.load_kube_config()
        except config.ConfigException:
            raise RuntimeError(
                "Could not load Kubernetes config: neither in-cluster nor local kubeconfig found"
            )

# function to create a pod for a lab session
def create_lab_pod(lab_name: str, image: str, port: int):

    _load_k8s_config()

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
    try:
        v1.create_namespaced_pod(namespace="default", body=pod)
    except ApiException as e:
        raise RuntimeError(f"Kubernetes error creating pod: {e.status} {e.reason}") from e

    # TODO: replace with a real Service/Ingress URL once networking layer is set up
    url = f"http://localhost:{port}"

    return pod_name, url

# function to delete a pod by name
def delete_lab_pod(pod_name: str):

    _load_k8s_config()

    v1 = client.CoreV1Api()
    try:
        v1.delete_namespaced_pod(name=pod_name, namespace="default")
    except ApiException as e:
        if e.status == 404:
            return  # pod already gone, treat as success
        raise RuntimeError(f"Kubernetes error deleting pod: {e.status} {e.reason}") from e
