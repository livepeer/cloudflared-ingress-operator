# cloudflared-ingress-operator
Kubernetes operator that watches for `cloudflared.io/*` annotations and dynamically updates cloudflared ConfigMap ingress rules

## Usage
```shell
helm repo add cloudflared-ingress-operator https://livepeer.github.io/cloudflared-ingress-operator
helm repo update
helm install cloudflared-ingress-operator cloudflared-ingress-operator/cloudflared-ingress-operator
```

Or to find the latest version, either check the [repo's releases](https://github.com/livepeer/cloudflared-ingress-operator/releases), or run:
```shell
helm search repo cloudflared-ingress-operator
```
