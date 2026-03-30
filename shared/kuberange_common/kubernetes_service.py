import os
import select
import subprocess
import shutil
import time
import uuid
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

# tracks minikube tunnel processes by pod_name (only used on macOS Docker driver)
_tunnel_processes: dict[str, subprocess.Popen] = {}

# Loads k8s creds so python client can authenticate with the cluster.
def _load_k8s_config():
    try:
        config.load_incluster_config()  # Tries in-cluster config first (when running as a pod in k8s)
    except config.ConfigException:
        try:
            config.load_kube_config()
        except config.ConfigException:
            raise RuntimeError(
                "Could not load Kubernetes config: neither in-cluster nor local kubeconfig found"
            )

# Poll k8s API every 3s until pod reaches `Running` or fails or timeout.
# This is to ensure that when we return the lab URL, the pod is actually ready.
def _wait_for_pod_running(v1, pod_name: str, timeout: int = 300):
    """Block until the pod phase is Running or timeout is reached."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        pod = v1.read_namespaced_pod(name=pod_name, namespace="default")
        phase = pod.status.phase
        print(f"Pod {pod_name} phase: {phase}")
        if phase == "Running":
            return
        if phase in ("Failed", "Unknown"):
            raise RuntimeError(f"Pod {pod_name} entered phase {phase}")
        time.sleep(3)
    raise RuntimeError(f"Pod {pod_name} did not reach Running state within {timeout}s")

# Asks the k8s API for node's IP
# Used to build lab URL when running in-cluster
def _get_node_ip():
    v1 = client.CoreV1Api()
    nodes = v1.list_node()
    for addr_type in ("ExternalIP", "InternalIP"):
        for node in nodes.items:
            for addr in node.status.addresses:
                if addr.type == addr_type:
                    return addr.address
    raise RuntimeError("Could not determine node IP address")

# Decides how to build reachable URL for lab
# Local: `minikube service <svc-name> --url` (so my mac can reach the sservice when using Docker driver)
# In-cluster: `http://<node-ip>:<node-port>` (skips minikube since backend pod is already inside cluster network)
def _get_service_url(svc_name: str, pod_name: str, node_port: int) -> str:
    """
    Local dev (not in-cluster): use `minikube service --url` tunnel so the URL is
    reachable from macOS when using the Docker driver.
    In-cluster: use the node IP directly (requires `minikube tunnel` on macOS Docker driver).
    """
    in_cluster = "KUBERNETES_SERVICE_HOST" in os.environ

    if not in_cluster and shutil.which("minikube"):
        try:
            proc = subprocess.Popen(
                ["minikube", "service", svc_name, "-n", "default", "--url"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            deadline = time.time() + 60
            while time.time() < deadline:
                remaining = max(0.1, deadline - time.time())
                ready, _, _ = select.select([proc.stdout], [], [], remaining)
                if ready:
                    line = proc.stdout.readline().strip()
                    if line.startswith("http"):
                        _tunnel_processes[pod_name] = proc
                        return line
                if proc.poll() is not None:
                    break
            proc.kill()
            print(f"Warning: minikube tunnel timed out for {svc_name}, falling back to node IP")
        except Exception as e:
            print(f"Warning: minikube service URL failed ({e}), falling back to node IP")

    node_ip = _get_node_ip()
    return f"http://{node_ip}:{node_port}"

# function to create a pod and NodePort service for a lab session
def create_lab_pod(lab_name: str, image: str, port: int):

    _load_k8s_config()

    # generate unique pod name
    unique_id = str(uuid.uuid4())[:8]
    pod_name = f"{lab_name.lower().replace(' ', '-')}-{unique_id}"
    lab_label = lab_name.lower().replace(' ', '-')
    svc_name = f"{pod_name}-svc"

    # Create k8s Pod obj with a unique session label so the service can select it exclusively
    pod = client.V1Pod(
        metadata=client.V1ObjectMeta(
            name=pod_name,
            labels={"app": "kuberange-lab", "lab": lab_label, "session": pod_name}
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

    v1 = client.CoreV1Api()
    try:
        v1.create_namespaced_pod(namespace="default", body=pod)
    except ApiException as e:
        raise RuntimeError(f"Kubernetes error creating pod: {e.status} {e.reason}") from e

    # create a NodePort service that selects pods with the unique session label
    svc = client.V1Service(
        metadata=client.V1ObjectMeta(name=svc_name),
        spec=client.V1ServiceSpec(
            type="NodePort",
            selector={"session": pod_name},
            ports=[client.V1ServicePort(port=port, target_port=port)]
        )
    )
    try:
        created_svc = v1.create_namespaced_service(namespace="default", body=svc)
    except ApiException as e:
        try:
            v1.delete_namespaced_pod(name=pod_name, namespace="default")
        except ApiException:
            pass
        raise RuntimeError(f"Kubernetes error creating service: {e.status} {e.reason}") from e

    node_port = created_svc.spec.ports[0].node_port
    _wait_for_pod_running(v1, pod_name)
    url = _get_service_url(svc_name, pod_name, node_port)

    return pod_name, url

# function to delete a pod and its associated service by pod name
# called when user stops lab or lab expires
def delete_lab_pod(pod_name: str):

    _load_k8s_config()

    # kill minikube tunnel if one was started for this session
    if pod_name in _tunnel_processes:
        _tunnel_processes[pod_name].terminate()
        del _tunnel_processes[pod_name]

    v1 = client.CoreV1Api()
    try:
        v1.delete_namespaced_pod(name=pod_name, namespace="default")
    except ApiException as e:
        if e.status != 404:  # already gone
            raise RuntimeError(f"Kubernetes error deleting pod: {e.status} {e.reason}") from e

    # delete associated service
    svc_name = f"{pod_name}-svc"
    try:
        v1.delete_namespaced_service(name=svc_name, namespace="default")
    except ApiException as e:
        if e.status != 404:
            raise RuntimeError(f"Kubernetes error deleting service: {e.status} {e.reason}") from e
