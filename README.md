# NKP Demo RAG

A **sample RAG application** for demonstrating NKP AI catalog composability. It depends on [Weaviate](https://www.weaviate.io/), indexes sample documents, and provides a simple query UI.

## Documentation

- **[Architecture & RAG Overview](docs/ARCHITECTURE.md)** — Code flow, RAG concepts, and how this demo works

## Purpose

This app showcases:

- **Catalog dependency flow** — Enable Weaviate first, then enable this app
- **In-cluster discovery** — Connects to Weaviate via Kubernetes DNS
- **RAG pattern** — Document storage and retrieval (keyword search for minimal deps)

## Prerequisites

- **Weaviate** must be enabled in the same NKP workspace before enabling this app
- Deploy from the [NKP AI Applications Catalog](https://github.com/nutanix-cloud-native/nkp-ai-applications-catalog)

## Usage

1. Enable **Weaviate** from the NKP UI
2. Wait for Weaviate to be ready
3. Enable **Demo RAG** from the NKP UI
4. Open the app URL (LoadBalancer or via Launch button)
5. Try queries like "NKP", "Weaviate", or "RAG"

## Sample Documents

The app indexes these sample docs on first run:

- **NKP Overview** — Nutanix Kubernetes Platform
- **Weaviate Overview** — Vector database
- **RAG Overview** — Retrieval-Augmented Generation

## Configuration

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `WEAVIATE_URL` | `http://weaviate.weaviate.svc.cluster.local:80` | Weaviate REST API URL |

Override via Helm values if your Weaviate instance uses a different namespace or release name.

## Development

### Build and run locally

```bash
pip install -r src/requirements.txt
export WEAVIATE_URL=http://localhost:8080  # or your Weaviate URL
python src/app.py
```

### Build container and Helm chart

```bash
make build
make release VERSION=1.0.0
```

### CI/CD (GitHub Actions)

The workflow runs on **every pull request** to `main` and on **tag pushes**:

| Trigger | Docker Image | Helm Chart |
|---------|--------------|------------|
| PR to `main` | `ghcr.io/deepak-muley/demo-rag:0.0.0-pr.<PR_NUMBER>` | `oci://ghcr.io/deepak-muley/charts` (version `0.0.0-pr.<PR_NUMBER>`) |
| Tag push `v*` | `ghcr.io/deepak-muley/demo-rag:<VERSION>` and `:latest` | `oci://ghcr.io/deepak-muley/charts` (version from tag) |

**Release a new version:**

```bash
git tag v1.0.0
git push origin v1.0.0
```

Artifacts are published to [GitHub Container Registry](https://github.com/deepak-muley/nkp-demo-rag/pkgs/container/demo-rag) and [GitHub Packages](https://github.com/deepak-muley/nkp-demo-rag/packages).

## Catalog Entry

This app is registered in the NKP AI Applications Catalog as `demo-rag`:

- **Catalog path:** `applications/demo-rag/1.0.0/`
- **Source:** [github.com/deepak-muley/nkp-demo-rag](https://github.com/deepak-muley/nkp-demo-rag)

## License

MIT
