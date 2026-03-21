# KubeRange
I LEARN KUBERNET FOR JAWB

## Diagram
View [KubeRange.pdf](KubeRange.pdf)

## K8s
Kubernetes (K8s) is a container orchestration platform — it automates deploying, scaling, and managing containerized applications.

**The problem it solves**

You have an app made of multiple services (frontend, backend, database, etc.), each running in Docker containers. Manually managing those containers across multiple machines — keeping them running, scaling them up, updating them — doesn't scale. Kubernetes handles all of that for you.

**Core concepts**

Cluster — the entire Kubernetes environment, made up of machines called Nodes
Node — an individual machine (VM or physical) where pods actually run
Pod — the smallest unit; wraps one or more containers that run together
Deployment — tells Kubernetes what to run, how many replicas, and how to handle updates. Manages pods for a given component
Service (K8s object) — a stable network endpoint (DNS name + IP) that routes traffic to the right pods, since pods are ephemeral and their IPs change
Namespace — a way to logically partition a cluster (e.g. prod vs dev)
