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

# Polls the k8s API until the LoadBalancer service is assigned an ingress IP/hostname.
# This requires `minikube tunnel` to be running on macOS Docker driver.
def _wait_for_lb_ingress(v1, svc_name: str, timeout: int = 120) -> str:
    deadline = time.time() + timeout
    while time.time() < deadline:
        svc = v1.read_namespaced_service(name=svc_name, namespace="default")
        ingress_list = svc.status.load_balancer.ingress if svc.status.load_balancer else None
        if ingress_list:
            ip = ingress_list[0].ip or ingress_list[0].hostname
            if ip:
                return ip
        time.sleep(2)
    raise RuntimeError(
        f"LoadBalancer {svc_name} did not receive an ingress IP within {timeout}s. "
        "Make sure `minikube tunnel` is running in a separate terminal."
    )

# Decides how to build reachable URL for lab.
# Local (not in-cluster): `minikube service <svc-name> --url` so the Mac can reach it via Docker driver tunnel.
# In-cluster: wait for LoadBalancer ingress IP assigned by `minikube tunnel`, then return http://<ip>:<port>.
def _get_service_url(svc_name: str, pod_name: str, v1, port: int) -> str:
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
            print(f"Warning: minikube tunnel timed out for {svc_name}, falling back to LB ingress")
        except Exception as e:
            print(f"Warning: minikube service URL failed ({e}), falling back to LB ingress")

    # In-cluster: wait for minikube tunnel to assign an external IP to the LoadBalancer service
    lb_ip = _wait_for_lb_ingress(v1, svc_name)
    return f"http://{lb_ip}:{port}"

# function to create a pod and LoadBalancer service for a lab session
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

    # create a LoadBalancer service that selects pods with the unique session label.
    # LoadBalancer type is required so that `minikube tunnel` can assign an external IP
    # reachable from macOS when using the Docker driver.
    # Privileged ports (< 1024) can't be bound by minikube tunnel on macOS, so expose
    # them on port+8000 externally (e.g. port 80 → 8080, port 443 → 8443).
    external_port = port + 8000 if port < 1024 else port
    svc = client.V1Service(
        metadata=client.V1ObjectMeta(name=svc_name),
        spec=client.V1ServiceSpec(
            type="LoadBalancer",
            selector={"session": pod_name},
            ports=[client.V1ServicePort(port=external_port, target_port=port)]
        )
    )
    try:
        v1.create_namespaced_service(namespace="default", body=svc)
    except ApiException as e:
        try:
            v1.delete_namespaced_pod(name=pod_name, namespace="default")
        except ApiException:
            pass
        raise RuntimeError(f"Kubernetes error creating service: {e.status} {e.reason}") from e

    _wait_for_pod_running(v1, pod_name)
    url = _get_service_url(svc_name, pod_name, v1, external_port)

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
