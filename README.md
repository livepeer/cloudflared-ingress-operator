# Cloudflare Ingress Operator

A Kubernetes operator that watches for `cloudflared.io/*` annotations on Services and Ingresses, and dynamically updates the cloudflared ConfigMap's ingress rules.

## Overview

This operator enables dynamic ingress rule management for cloudflared tunnels. Instead of manually updating the cloudflared ConfigMap every time you want to expose a new service, simply annotate your Service or Ingress resource with `cloudflared.io/*` annotations, and the operator will automatically update the tunnel configuration.

Perfect for use with ArgoCD and GitOps workflows!

## Features

- **Automatic Discovery**: Watches Services and Ingresses across namespaces
- **Annotation-Based**: Simple annotation syntax for configuring routes
- **Dynamic Updates**: Automatically updates cloudflared ConfigMap when resources change
- **Multi-Namespace Support**: Watch specific namespaces or all namespaces
- **GitOps Friendly**: Works seamlessly with ArgoCD and other GitOps tools

## Quick Start

### Deploy with Helm

```bash
# Add the Helm repository
helm repo add cloudflare-ingress-operator https://livepeer.github.io/cloudflare-ingress-operator
helm repo update

# Install the chart
helm install cloudflare-ingress-operator cloudflare-ingress-operator/cloudflare-ingress-operator \
  --set cloudflared.namespace=default \
  --set cloudflared.configMapName=cloudflared
```

Or install directly from this repository:

```bash
helm install cloudflare-ingress-operator ./charts/cloudflare-ingress-operator \
  --set cloudflared.namespace=default \
  --set cloudflared.configMapName=cloudflared
```

### Annotate Your Services

Add annotations to your Service to expose it through cloudflared:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  annotations:
    cloudflared.io/hostname: "app.example.com"
spec:
  selector:
    app: my-app
  ports:
  - port: 8080
```

That's it! The operator will automatically detect the `cloudflared.io/*` annotation and add the ingress rule to cloudflared.

## Supported Annotations

| Annotation | Required | Description | Example |
|------------|----------|-------------|---------|
| `cloudflared.io/hostname` | Yes | Hostname to route | `"app.example.com"` |
| `cloudflared.io/service` | No | Service URL (auto-generated if omitted) | `"http://svc:8080"` |
| `cloudflared.io/path` | No | Path-based routing | `"/api/*"` |
| `cloudflared.io/origin-request` | No | Origin request config (YAML) | See [examples](example-service.yaml) |

**Note**: The operator automatically detects any `cloudflared.io/*` annotation - you don't need an `enabled` flag. If you add any cloudflared annotation, the operator assumes you want routing enabled.

## Building the Image

```bash
# Build locally
docker build -t livepeer/cloudflare-ingress-operator:latest .

# Build multi-platform
docker buildx build --platform linux/amd64,linux/arm64 \
  -t livepeer/cloudflare-ingress-operator:latest \
  --push .
```

## Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run operator (requires kubeconfig)
export CLOUDFLARED_NAMESPACE=default
export CONFIGMAP_NAME=cloudflared
export WATCH_ALL_NAMESPACES=true
python src/operator.py
```

### Project Structure

```
.
├── src/
│   └── operator.py          # Main operator logic
├── .github/
│   └── workflows/
│       └── docker-build.yaml # CI/CD workflow
├── Dockerfile               # Container image
├── requirements.txt         # Python dependencies
├── example-service.yaml     # Usage examples
└── README.md
```

## CI/CD

The GitHub Actions workflow automatically:
- Builds multi-platform Docker images (amd64, arm64)
- Pushes to Docker Hub on commits to `main`
- Creates tagged releases for version tags (`v*`)
- Validates PRs without pushing

### Required Secrets

Configure these in GitHub repository settings:
- `DOCKERHUB_USERNAME` - Docker Hub username
- `DOCKERHUB_TOKEN` - Docker Hub access token

## How It Works

1. The operator watches for Services and Ingresses with any `cloudflared.io/*` annotations
2. For each annotated resource, it generates an ingress rule based on the annotations
3. It updates the cloudflared ConfigMap with all discovered ingress rules
4. Cloudflared automatically reloads when the ConfigMap changes

## Permissions

The operator requires:
- **ClusterRole** (if watching all namespaces): `get`, `list`, `watch` on Services and Ingresses
- **Role** (in cloudflared namespace): `get`, `list`, `watch`, `update`, `patch` on the cloudflared ConfigMap
- **Role** (in watched namespaces): `get`, `list`, `watch` on Services and Ingresses

## License

MIT

## Related Projects

- [infra-helm-charts](https://github.com/livepeer/infra-helm-charts) - Helm chart for deploying this operator
- [cloudflared](https://github.com/cloudflare/cloudflared) - Cloudflare Tunnel client
