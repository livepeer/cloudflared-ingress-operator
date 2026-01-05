# Cloudflare Ingress Operator

Helm chart for deploying the Cloudflare Ingress Operator - a Kubernetes operator that watches for `cloudflared.io/*` annotations on Services and Ingresses, and dynamically updates the cloudflared ConfigMap's ingress rules.

> **Note**: This is the Helm chart repository. For the operator source code, see [cloudflare-ingress-operator](https://github.com/livepeer/cloudflare-ingress-operator).

## Overview

This operator enables dynamic ingress rule management for cloudflared tunnels. Instead of manually updating the cloudflared ConfigMap every time you want to expose a new service, simply annotate your Service or Ingress resource with `cloudflared.io/*` annotations, and the operator will automatically update the tunnel configuration.

Perfect for use with ArgoCD and GitOps workflows!

## Features

- **Automatic Discovery**: Watches Services and Ingresses across namespaces
- **Annotation-Based**: Simple annotation syntax for configuring routes
- **Dynamic Updates**: Automatically updates cloudflared ConfigMap when resources change
- **Multi-Namespace Support**: Watch specific namespaces or all namespaces
- **GitOps Friendly**: Works seamlessly with ArgoCD and other GitOps tools

## Installation

### Prerequisites

- Kubernetes cluster
- Cloudflared helm chart deployed (from `../cloudflared`)
- Helm 3.x

### Deploy the Operator

```bash
# Install the helm chart
helm install cloudflare-ingress-operator . \
  --set cloudflared.namespace=default \
  --set cloudflared.configMapName=cloudflared
```

The operator image is automatically built and published to Docker Hub via GitHub Actions. See the [operator repository](https://github.com/livepeer/cloudflare-ingress-operator) for source code and build details.

### Configuration

Edit `values.yaml` to configure:

```yaml
# Cloudflared ConfigMap location
cloudflared:
  namespace: default              # Namespace where cloudflared is deployed
  configMapName: cloudflared      # Name of the cloudflared ConfigMap

# Watch settings
watch:
  allNamespaces: true             # Watch all namespaces
  namespaces: []                  # Or specific namespaces: [default, production]

# Operator image
operator:
  image:
    repository: livepeer/cloudflare-ingress-operator
    tag: "0.1.0"
```

## Usage

### Annotating Services

Add the following annotations to your Service to expose it through cloudflared:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  namespace: production
  annotations:
    cloudflared.io/hostname: "app.example.com"
    # Optional: custom service URL (auto-generated if omitted)
    cloudflared.io/service: "http://my-app.production.svc.cluster.local:8080"
    # Optional: path-based routing
    cloudflared.io/path: "/api/*"
    # Optional: origin request configuration (YAML string)
    cloudflared.io/origin-request: |
      connectTimeout: 30s
      noTLSVerify: false
spec:
  selector:
    app: my-app
  ports:
  - port: 8080
    targetPort: 8080
```

The operator automatically detects any `cloudflared.io/*` annotation - you don't need an `enabled` flag.

### Annotating Ingresses

You can also annotate Ingress resources:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app-ingress
  namespace: production
  annotations:
    cloudflared.io/hostname: "app.example.com"
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-app
            port:
              number: 8080
```

## Supported Annotations

| Annotation | Required | Description | Example |
|------------|----------|-------------|---------|
| `cloudflared.io/hostname` | Yes | Hostname to route | `"app.example.com"` |
| `cloudflared.io/service` | No | Service URL (auto-generated if omitted) | `"http://svc:8080"` |
| `cloudflared.io/path` | No | Path-based routing | `"/api/*"` |
| `cloudflared.io/origin-request` | No | Origin request config (YAML) | See below |

**Note**: The operator automatically detects any `cloudflared.io/*` annotation - you don't need an `enabled` flag.

### Origin Request Configuration

The `cloudflared.io/origin-request` annotation accepts YAML-formatted cloudflared origin request settings:

```yaml
annotations:
  cloudflared.io/origin-request: |
    connectTimeout: 30s
    tlsTimeout: 10s
    noTLSVerify: false
    disableChunkedEncoding: false
    bastionMode: false
    proxyType: ""
    httpHostHeader: "my-app.internal"
```

See [Cloudflare docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/configuration/ingress#origin-configurations) for all available options.

## How It Works

1. The operator watches for Services and Ingresses with any `cloudflared.io/*` annotations
2. For each annotated resource, it generates an ingress rule based on the annotations
3. It updates the cloudflared ConfigMap with all discovered ingress rules
4. Cloudflared automatically reloads when the ConfigMap changes (via reloader.stakater.com)

## Example: ArgoCD Application

Deploy an app with cloudflared routing via ArgoCD:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/myorg/my-app
    targetRevision: main
    path: k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

In your app's `k8s/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  annotations:
    cloudflared.io/hostname: "my-app.example.com"
spec:
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
```

When ArgoCD deploys this, the operator will automatically add the ingress rule to cloudflared!

## RBAC Permissions

The operator requires the following permissions:

- **ClusterRole** (if `watch.allNamespaces: true`):
  - `get`, `list`, `watch` on `services` and `ingresses` (all namespaces)

- **Role** (in cloudflared namespace):
  - `get`, `list`, `watch`, `update`, `patch` on the cloudflared ConfigMap

- **Role** (if `watch.allNamespaces: false`):
  - `get`, `list`, `watch` on `services` and `ingresses` (specified namespaces)

## Troubleshooting

### Check operator logs

```bash
kubectl logs -l app.kubernetes.io/name=cloudflare-ingress-operator -f
```

### Verify RBAC permissions

```bash
# Check if operator can read services
kubectl auth can-i list services --as=system:serviceaccount:default:cloudflare-ingress-operator -n production

# Check if operator can update ConfigMap
kubectl auth can-i update configmap/cloudflared --as=system:serviceaccount:default:cloudflare-ingress-operator -n default
```

### View current ingress rules

```bash
kubectl get configmap cloudflared -n default -o yaml
```

## Development

See the [cloudflare-ingress-operator](https://github.com/livepeer/cloudflare-ingress-operator) repository for:
- Operator source code
- Building and testing the operator
- Contributing guidelines

This repository contains:
- `templates/` - Helm chart templates
- `values.yaml` - Configuration values
- `Chart.yaml` - Chart metadata

## License

MIT
