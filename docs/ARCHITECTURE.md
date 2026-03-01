# NKP Demo RAG — Architecture & RAG Overview

This document explains what RAG is, how it works in general, and how this demo application implements a simplified retrieval flow.

---

## What is RAG?

**RAG (Retrieval-Augmented Generation)** is a technique that augments large language models (LLMs) with external knowledge. Instead of relying solely on the model’s training data, RAG:

1. **Retrieves** relevant documents from a knowledge base
2. **Augments** the user’s prompt with that context
3. **Generates** an answer using the LLM, grounded in the retrieved content

### Why RAG?

| Problem | How RAG Helps |
|---------|---------------|
| **Hallucinations** | LLMs can invent facts. RAG grounds answers in real documents. |
| **Stale knowledge** | Model training is fixed. RAG lets you add/update docs without retraining. |
| **Private data** | LLMs don’t know your internal docs. RAG injects them at query time. |
| **Cost** | Fine-tuning is expensive. RAG is cheaper and easier to maintain. |

---

## RAG Flow (General)

A typical RAG pipeline looks like this:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OFFLINE: Indexing Phase                             │
└─────────────────────────────────────────────────────────────────────────────┘

  Documents  ──►  Chunk  ──►  Embed  ──►  Vector DB (e.g. Weaviate)
                                    │
                                    └──► Store: (chunk_text, vector)

┌─────────────────────────────────────────────────────────────────────────────┐
│                         ONLINE: Query Phase                                 │
└─────────────────────────────────────────────────────────────────────────────┘

  User Query  ──►  Embed  ──►  Vector Search  ──►  Top-K Chunks
                                        │
                                        ▼
                              Build Prompt: [chunks] + [query]
                                        │
                                        ▼
                              LLM  ──►  Generated Answer
```

### Steps in Detail

1. **Chunking** — Split documents into smaller pieces (e.g. paragraphs, 512 tokens).
2. **Embedding** — Convert each chunk into a vector (embedding) using a model.
3. **Indexing** — Store chunks and vectors in a vector database.
4. **Query embedding** — Convert the user’s question into a vector.
5. **Retrieval** — Find the most similar chunks (e.g. cosine similarity).
6. **Prompt construction** — Combine retrieved chunks with the user query.
7. **Generation** — Send the prompt to an LLM and return the answer.

---

## This Demo: Simplified Retrieval Flow

This app is a **retrieval-only demo**. It shows the “R” in RAG: storing documents and retrieving them by relevance. It does **not** include:

- Vector embeddings
- An LLM for answer generation

It uses **keyword search** instead of semantic search, so it works without an embedding model or vectorizer.

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Startup / First Request                                                     │
└─────────────────────────────────────────────────────────────────────────────┘

  ensure_collection()
       │
       ├──► Check if Weaviate has "DemoDocs" collection
       │
       ├──► If not: create schema (title, content)
       │
       └──► Index sample_docs/*.txt into Weaviate

┌─────────────────────────────────────────────────────────────────────────────┐
│  User Submits Query (e.g. "NKP")                                             │
└─────────────────────────────────────────────────────────────────────────────┘

  search(query)
       │
       ├──► GraphQL: Get all docs from DemoDocs (limit 10)
       │
       ├──► Filter: keep docs where query appears in content (keyword match)
       │
       └──► Return top 3 matches with title + snippet (first 300 chars)

  Fallback: if no matches, return first 3 docs
```

---

## Code Flow

### Entry Points

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET, POST | Main UI; GET shows form, POST runs search |
| `/health` | GET | Liveness/readiness; checks Weaviate connectivity |

### Main Functions

```
index()                    # Flask route handler
  │
  ├── ensure_collection()  # One-time setup: create schema + index docs
  │     ├── weaviate_get("/v1/schema")
  │     ├── weaviate_post("/v1/schema", {...})
  │     └── weaviate_post("/v1/objects", {...}) for each sample doc
  │
  ├── search(query)       # If user submitted a query
  │     ├── GraphQL: Get { DemoDocs { title content } }
  │     ├── Filter by keyword (query in content)
  │     └── Return list of {title, content_snippet}
  │
  └── render_template_string(HTML, ...)
```

### Key Components

| Component | Role |
|-----------|------|
| `WEAVIATE_URL` | Weaviate REST/GraphQL base URL (default: in-cluster DNS) |
| `COLLECTION_NAME` | `"DemoDocs"` — Weaviate class for documents |
| `ensure_collection()` | Idempotent setup: create collection and index `sample_docs/*.txt` |
| `search(query)` | Fetch docs via GraphQL, filter by keyword, return top 3 |
| `weaviate_get` / `weaviate_post` | Thin wrappers over `requests` for Weaviate API |

### Sample Documents

| File | Content |
|------|---------|
| `nkp-overview.txt` | Nutanix Kubernetes Platform, GitOps, AI catalog |
| `weaviate-overview.txt` | Weaviate vector DB, hybrid search, RAG |
| `rag-overview.txt` | RAG concept, chunking, embeddings, grounding |

---

## Data Flow Diagram

```
                    ┌──────────────────┐
                    │   User Browser   │
                    └────────┬─────────┘
                             │ HTTP GET/POST
                             ▼
                    ┌──────────────────┐
                    │  Flask (app.py)   │
                    │  Port 8080       │
                    └────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
  ensure_collection()   search(query)      /health
         │                   │                   │
         │                   │                   │
         └───────────────────┴───────────────────┘
                             │
                             │ REST / GraphQL
                             ▼
                    ┌──────────────────┐
                    │    Weaviate      │
                    │  (vector store)  │
                    │  DemoDocs class  │
                    └──────────────────┘
```

---

## Extending to Full RAG

To turn this into a full RAG system, you would add:

1. **Embedding model** — e.g. `sentence-transformers` or Weaviate’s vectorizer
2. **Vector indexing** — Store embeddings in Weaviate instead of plain keyword search
3. **Semantic search** — Use `nearText` or similar for similarity search
4. **LLM integration** — e.g. vLLM, Ollama, or OpenAI API
5. **Prompt template** — e.g. “Answer based on: {chunks}\n\nQuestion: {query}”

The NKP AI catalog provides Weaviate (vector DB) and vLLM/Ollama (LLM serving), so a full RAG stack can be composed from the catalog.

---

## References

- [RAG Overview](https://arxiv.org/abs/2005.11401) — Lewis et al.
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [NKP AI Applications Catalog](https://github.com/nutanix-cloud-native/nkp-ai-applications-catalog)
