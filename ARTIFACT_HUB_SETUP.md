# Artifact Hub Setup Guide

This guide explains how to publish the Cloudflare Ingress Operator Helm chart to Artifact Hub.

## Prerequisites

1. GitHub repository with charts in `charts/` directory
2. GitHub Pages enabled for the repository
3. Artifact Hub account (https://artifacthub.io/)
4. Organization created on Artifact Hub (livepeer-org)

## Setup Steps

### 1. Enable GitHub Pages

1. Go to repository Settings → Pages
2. Source: Deploy from a branch
3. Branch: `gh-pages` / `root`
4. Save

The chart-releaser GitHub Action will automatically create and update the `gh-pages` branch.

### 2. Add Repository to Artifact Hub

1. Log in to Artifact Hub: https://artifacthub.io/
2. Go to Control Panel → Add Repository
3. Fill in the details:
   - **Name**: cloudflare-ingress-operator
   - **Display Name**: Cloudflare Ingress Operator
   - **URL**: https://livepeer.github.io/cloudflare-ingress-operator
   - **Kind**: Helm charts
   - **Organization**: livepeer-org
   - **Repository metadata file**: artifacthub-repo.yaml

4. Click "Add"

### 3. Get Repository ID

After adding the repository, go to the repository settings in Artifact Hub to get the Repository ID.

Update `artifacthub-repo.yaml`:

```yaml
repositoryID: <YOUR_REPOSITORY_ID>
owners:
  - name: livepeer-org
    email: sre@livepeer.org
```

### 4. Trigger First Release

To trigger the first chart release:

```bash
# Make a change to the chart
cd charts/cloudflare-ingress-operator
# Bump version in Chart.yaml or make a change

# Commit and push
git add .
git commit -m "feat: initial chart release"
git push origin main
```

The GitHub Action will:
1. Package the chart
2. Create a GitHub Release
3. Update the `gh-pages` branch with the chart index
4. Artifact Hub will automatically sync from GitHub Pages

### 5. Verify

1. Check GitHub Actions ran successfully
2. Verify `gh-pages` branch was created/updated
3. Check GitHub Releases for chart package
4. Wait ~5-10 minutes for Artifact Hub to sync
5. Visit: https://artifacthub.io/packages/helm/livepeer-org/cloudflare-ingress-operator

## Chart Versioning

Update the version in `charts/cloudflare-ingress-operator/Chart.yaml`:

```yaml
version: 0.1.0  # Increment this for each release
```

Follow Semantic Versioning:
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

## Testing Locally

Before pushing, test the chart:

```bash
# Lint
helm lint charts/cloudflare-ingress-operator

# Template
helm template cloudflare-ingress-operator charts/cloudflare-ingress-operator

# Package
helm package charts/cloudflare-ingress-operator

# Test install
helm install test-release charts/cloudflare-ingress-operator --dry-run --debug
```

## Troubleshooting

### Chart not appearing on Artifact Hub

1. Check GitHub Pages is enabled and `gh-pages` branch exists
2. Visit https://livepeer.github.io/cloudflare-ingress-operator/index.yaml to verify chart index
3. Check Artifact Hub repository settings
4. Wait 5-10 minutes for sync
5. Check repository metadata file is at root: `artifacthub-repo.yaml`

### GitHub Action failing

1. Check workflow permissions in repository settings
2. Ensure `gh-pages` branch has proper permissions
3. Review action logs for errors

## References

- [Artifact Hub Documentation](https://artifacthub.io/docs/)
- [Chart Releaser Action](https://github.com/helm/chart-releaser-action)
- [Helm Chart Best Practices](https://helm.sh/docs/chart_best_practices/)
