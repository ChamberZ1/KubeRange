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

Hiearchy: `Container < Pod < Node < Cluster`
1) Cluster - the entire Kubernetes environment, made up of machines called Nodes.
2) Node - an individual machine (VM or physical) where pods actually run.
3) Pod - wraps one or more containers that run together and share the same network/storage.
4) Container - holds the code package for a "microservice", a component of the full application.
5) Deployment - Pod manager that tells Kubernetes what pod to run, how many, handle updates, and restart pods if they crash.
6) Service - Virtual routing rule that exposes a pod to other pods or external traffic. It creates a stable network endpoint (DNS name + port) that routes traffic to the right pods, since pods are ephemeral and their IPs change.
7) Namespace - a way to logically partition a cluster (e.g. prod vs dev)
8) ConfigMap - stores non-sensitive configuration data (scripts, env vars, config files) that pods can consume
9) Secret - same as ConfigMap but for sensitive data (passwords, tokens), stored with base64 encoding
10) ServiceAccount + Role-Based Access Control (RBAC) - gives pods an identity and defines what K8s API resources they're allowed to access
