# KubeRange
I LEARN KUBERNET FOR JAWB

## Diagram
View [KubeRange.pdf](KubeRange.pdf)

## K8s
Kubernetes (K8s) is a container orchestration platform — it automates deploying, scaling, and managing containerized applications.

**The problem it solves**

Modern applications are composed of multiple services such as frontend, backend, and databases, each typically running in its own container. In a real environment, these containers must be deployed across machines, restarted if they fail, scaled up or down based on demand, and kept updated without downtime. Networking between services must also remain reliable even as individual containers are created or destroyed.

Managing this manually does not scale. It quickly becomes operationally complex, error-prone, and difficult to maintain.

Kubernetes solves this by providing a control plane that continuously ensures the system matches a desired state. You declare what should be running and how it should behave, and Kubernetes handles scheduling, scaling, self-healing, service discovery, and rolling updates automatically

**Core concepts**

1) Cluster - the entire Kubernetes environment, made up of machines called Nodes
2) Node - an individual machine (VM or physical) where pods actually run
3) Pod - the smallest unit; wraps one or more containers that run together
4) Deployment - tells Kubernetes what to run, how many replicas, and how to handle updates. Manages pods for a given component
5) Service (K8s object) - a stable network endpoint (DNS name + IP) that routes traffic to the right pods, since pods are ephemeral and their IPs change
6) Namespace - a way to logically partition a cluster (e.g. prod vs dev)
