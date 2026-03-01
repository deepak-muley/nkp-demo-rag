#!/usr/bin/env python3
"""
NKP Demo RAG — sample RAG application demonstrating catalog composability.
Depends on Weaviate. Indexes sample docs and provides a simple query UI.
Uses Weaviate REST API for minimal dependencies.
"""
import os
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

WEAVIATE_URL = os.environ.get("WEAVIATE_URL", "http://weaviate.weaviate.svc.cluster.local:80").rstrip("/")
COLLECTION_NAME = "DemoDocs"

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>NKP Demo RAG</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 600px; margin: 2rem auto; padding: 1rem; }
    .status { padding: 1rem; border-radius: 8px; margin: 1rem 0; }
    .ok { background: #d4edda; color: #155724; }
    .err { background: #f8d7da; color: #721c24; }
    h1 { color: #333; }
    input, button { padding: 0.5rem 1rem; font-size: 1rem; }
    .results { margin-top: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 8px; }
    code { background: #f4f4f4; padding: 0.2em 0.4em; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>NKP Demo RAG</h1>
  <p>Sample RAG app demonstrating catalog composability. Uses <strong>Weaviate</strong> for document storage.</p>
  <div class="status {{ status_class }}">{{ message }}</div>
  <form method="post" action="/">
    <input type="text" name="query" placeholder="Ask a question (e.g. NKP, Weaviate, RAG)..." value="{{ query }}" style="width: 70%;">
    <button type="submit">Search</button>
  </form>
  {% if results %}
  <div class="results">
    <h3>Results</h3>
    {% for r in results %}
    <p><strong>{{ r.title }}</strong><br>{{ r.content }}</p>
    {% endfor %}
  </div>
  {% endif %}
</body>
</html>
"""


def weaviate_get(path):
    """GET request to Weaviate."""
    r = requests.get(f"{WEAVIATE_URL}{path}", timeout=10)
    r.raise_for_status()
    return r.json() if r.content else {}


def weaviate_post(path, json=None):
    """POST request to Weaviate."""
    r = requests.post(f"{WEAVIATE_URL}{path}", json=json or {}, timeout=10)
    r.raise_for_status()
    return r.json() if r.content else {}


def ensure_collection():
    """Create collection and index sample docs if needed."""
    # Check if collection exists
    try:
        schema = weaviate_get("/v1/schema")
        if any(c["class"] == COLLECTION_NAME for c in schema.get("classes", [])):
            return
    except Exception:
        pass

    # Create schema
    weaviate_post("/v1/schema", {
        "class": COLLECTION_NAME,
        "properties": [
            {"name": "title", "dataType": ["text"]},
            {"name": "content", "dataType": ["text"]},
        ],
    })

    # Index sample docs
    docs_dir = Path(__file__).parent / "sample_docs"
    if docs_dir.exists():
        for f in docs_dir.glob("*.txt"):
            content = f.read_text()
            title = f.stem.replace("-", " ").title()
            weaviate_post("/v1/objects", {
                "class": COLLECTION_NAME,
                "properties": {"title": title, "content": content},
            })


def search(query: str, limit: int = 3):
    """Fetch docs and filter by keyword (simple, works without vectorizer)."""
    gql = f"""
    {{
      Get {{
        {COLLECTION_NAME} (limit: 10) {{
          title
          content
        }}
      }}
    }}
    """
    try:
        r = requests.post(
            f"{WEAVIATE_URL}/v1/graphql",
            json={"query": gql},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        items = data.get("data", {}).get("Get", {}).get(COLLECTION_NAME, [])
        q = query.lower().strip()
        results = []
        for x in items:
            content = x.get("content", "")
            title = x.get("title", "")
            snippet = content[:300] + "..." if len(content) > 300 else content
            if not q or q in content.lower():
                results.append({"title": title, "content": snippet})
            if len(results) >= limit:
                break
        return results
    except Exception:
        return []


@app.route("/", methods=["GET", "POST"])
def index():
    query = request.form.get("query", "") if request.method == "POST" else ""
    results = []
    status_class = "ok"
    message = "Weaviate: Connected"

    try:
        ensure_collection()
        if query:
            results = search(query)
        if not results and query:
            results = search("", limit=3)  # Fallback: return any docs
    except Exception as e:
        status_class = "err"
        message = f"Weaviate: Not reachable. Enable Weaviate in the workspace first. ({e})"

    return render_template_string(
        HTML,
        status_class=status_class,
        message=message,
        query=query,
        results=results,
    )


@app.route("/health")
def health():
    try:
        r = requests.get(f"{WEAVIATE_URL}/v1/.well-known/ready", timeout=5)
        ok = r.status_code == 200
        return jsonify({"weaviate": "ok" if ok else "unreachable"}), 200 if ok else 503
    except Exception:
        return jsonify({"weaviate": "unreachable"}), 503


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
