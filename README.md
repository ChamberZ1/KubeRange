# KubeRange
A Kubernetes and Docker-based platform that spins up vulnerable web applications (DVWA, Juice Shop) as isolated lab environments for practicing web exploitation. Includes a lightweight EFK stack implementation for SIEM experience - collect and analyze attack logs generated during each lab session.

## Startup

**Prerequisites:** Docker Desktop running, minikube installed, kubectl installed.

**First time (or after `minikube delete`):**
```bash
minikube start --cpus=4 --memory=4096
./scripts/deploy.sh        # builds images, applies all manifests, prints frontend + Kibana URLs
```

**Normal startup (cluster already exists):**
```bash
minikube start
minikube tunnel            # Terminal 1 — keep running; required for lab pod URLs to work
```
Frontend and Kibana URLs:
```bash
minikube service frontend-service --url
minikube service kibana-service --url
```

---

## Teardown

**Pause (preserves all state — pods, DB, logs):**
```bash
# Ctrl+C the minikube tunnel terminal
minikube stop
```
Resume with `minikube start` + `minikube tunnel`. No need to re-run `deploy.sh`.

**Full reset (wipes everything — fresh DB, IDs start at 1):**
```bash
minikube delete
minikube start --cpus=4 --memory=4096
./scripts/deploy.sh
```

Note: the worker automatically cleans up expired lab pods and services while running. If a lab is active when you run `minikube stop`, the worker will clean it up on its next cycle when minikube restarts.

---

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

## Observability — Log Collection

KubeRange uses a Filebeat → Elasticsearch → Kibana pipeline to collect and visualize attack logs from running lab pods (DVWA, Juice Shop). This lets you see HTTP requests, login attempts, and other activity generated during a lab session.

**Components**

- **Filebeat** - a lightweight log shipper that runs as a DaemonSet (one pod per node). It uses Kubernetes autodiscover to detect new lab pods automatically and tail their container logs. Filtered to pods with label `app: kuberange-lab` so it only collects lab traffic, not internal cluster noise.
- **Elasticsearch** - stores and indexes the log events shipped by Filebeat. Logs land in a daily index (`kuberange-labs-YYYY.MM.DD`) so you can filter by date. Importantly, logs are shipped in real-time as the lab runs — so when a lab pod expires and is deleted after 30 minutes, its logs are already in Elasticsearch and remain queryable. You can run multiple lab sessions in a day and review all of them in Kibana afterward. The only way logs are lost is if the Elasticsearch pod itself restarts (see limitations below).
- **Kibana** - web UI for searching and visualizing the indexed logs. Connect it to the Elasticsearch index and you can query requests by IP, path, status code, etc. Similar to how a SOC analyst would use a SIEM.

**How this deviates from a standard ELK stack**

A production ELK deployment typically uses Logstash (the "L") between Filebeat and Elasticsearch for parsing, filtering, and transforming log events before indexing. KubeRange ships Filebeat directly to Elasticsearch (no Logstash), implementing the EFK stack — the lighter alternative to ELK that's well-suited for container environments. This is fine for local dev — the raw container logs are still fully searchable in Kibana. The tradeoff is that log parsing (e.g. extracting structured fields from Apache access log lines) requires either Elasticsearch ingest pipelines or Filebeat processors rather than Logstash config.

Other local-dev simplifications vs production:

- TLS and authentication disabled on Elasticsearch (`xpack.security.enabled: false`)
- Elasticsearch JVM heap capped at 1GB (sized for a 4GB minikube instance)
- No persistent volume — log history is lost if the Elasticsearch pod restarts. In production you'd add a PersistentVolumeClaim so Elasticsearch data survives pod restarts. It was omitted here because minikube's default storage provisioner requires configuring a hostPath volume pointing to a directory inside the minikube VM — extra setup that adds complexity without adding learning value for a local dev environment.
- Filebeat filtered to lab pods only, not full cluster observability

---

## Future Work

**User authentication** - currently anyone can access the platform. A users table and login system would unlock per-user session history, multi-user support, and meaningful pod naming (e.g. `dvwa-username` instead of `dvwa-6afc0926`).

**Ingress controller** - right now services are exposed via NodePort/LoadBalancer through `minikube tunnel`, resulting in multiple `127.0.0.1:<random_port>` URLs. An Ingress controller would consolidate everything behind a single host (e.g. `kuberange.local`), with path-based routing to the frontend, backend, and Kibana. Lab pods would get subdomain-based URLs (e.g. `dvwa-abc123.kuberange.local`) via dynamically created Ingress rules. This is most valuable when deploying to a real cluster (EKS, GKE) — on minikube it adds complexity without much practical benefit.

**Namespaces** - currently everything runs in the `default` namespace. Separating into `labs`, `platform`, and `observability` namespaces would give cleaner RBAC scoping and make `kubectl` output easier to read.

**More lab types** - add more intentionally vulnerable applications beyond DVWA and Juice Shop.

**Persistent Elasticsearch storage** - add a PersistentVolumeClaim to Elasticsearch so logs survive pod restarts.
