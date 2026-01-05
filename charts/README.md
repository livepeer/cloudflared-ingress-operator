# Cloudflared Ingress Operator Helm Charts

This directory contains the official Helm chart for the Cloudflared Ingress Operator.

## Installation

### Add the Helm repository

```bash
helm repo add cloudflared-ingress-operator https://livepeer.github.io/cloudflared-ingress-operator
helm repo update
```

### Install the chart

```bash
helm install cloudflared-ingress-operator cloudflared-ingress-operator/cloudflared-ingress-operator \
  --set cloudflared.namespace=cloudflared \
  --set cloudflared.configMapName=cloudflared-config
```

## Chart Repository

The charts are hosted on GitHub Pages and automatically published via GitHub Actions when changes are pushed to the `main` branch.

- **Repository URL**: https://livepeer.github.io/cloudflared-ingress-operator
- **Artifact Hub**: https://artifacthub.io/packages/search?org=livepeer-org

## Development

To test the chart locally:

```bash
# Lint the chart
helm lint charts/cloudflared-ingress-operator

# Template the chart
helm template cloudflared-ingress-operator charts/cloudflared-ingress-operator

# Install locally
helm install cloudflared-ingress-operator charts/cloudflared-ingress-operator \
  --set cloudflared.namespace=cloudflared
```

## Versioning

Charts follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)
