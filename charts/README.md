# Cloudflare Ingress Operator Helm Charts

This directory contains the official Helm chart for the Cloudflare Ingress Operator.

## Installation

### Add the Helm repository

```bash
helm repo add cloudflare-ingress-operator https://livepeer.github.io/cloudflare-ingress-operator
helm repo update
```

### Install the chart

```bash
helm install cloudflare-ingress-operator cloudflare-ingress-operator/cloudflare-ingress-operator \
  --set cloudflared.namespace=default \
  --set cloudflared.configMapName=cloudflared
```

## Chart Repository

The charts are hosted on GitHub Pages and automatically published via GitHub Actions when changes are pushed to the `main` branch.

- **Repository URL**: https://livepeer.github.io/cloudflare-ingress-operator
- **Artifact Hub**: https://artifacthub.io/packages/search?org=livepeer-org

## Development

To test the chart locally:

```bash
# Lint the chart
helm lint charts/cloudflare-ingress-operator

# Template the chart
helm template cloudflare-ingress-operator charts/cloudflare-ingress-operator

# Install locally
helm install cloudflare-ingress-operator charts/cloudflare-ingress-operator \
  --set cloudflared.namespace=default
```

## Versioning

Charts follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)
