# RAG Q&A System
 
A Retrieval-Augmented Generation (RAG) pipeline built from scratch, one
component at a time, to understand every layer rather than gluing together
a framework.
 
## Status: Week 1 complete — Ingestion & Retrieval
 
- **Document loader** (`app/core/document_loader.py`) — extracts plain text
  from PDF, TXT, and CSV files via a dispatch-table pattern.
- **Chunker** (`app/core/chunker.py`) — hand-written, boundary-aware text
  splitter with configurable size/overlap.
- **Embeddings** (`app/core/embeddings.py`) — free, local embeddings via
  `sentence-transformers/all-MiniLM-L6-v2`, model cached for reuse.
- **Vector store** (`app/core/vector_store.py`) — ChromaDB wrapper for
  storing embeddings with source/position metadata and semantic search.
- **Config** (`app/config.py`) — centralized settings via
  `pydantic-settings`, overridable via environment variables.
## Why these choices
 
| Decision | Reasoning |
|---|---|
| Local embeddings, not an API | Zero cost while learning; swappable later |
| Hand-written chunker | Understanding overlap/boundary logic over importing a pre-built splitter |
| `pydantic-settings` | Confirmed env-var overrides work — useful for Docker/CI later |
| Chroma (local) | No signup/server needed to start; may migrate to Qdrant later |
 
## Setup
 
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
 
## Usage
 
```python
from app.core.vector_store import add_chunks, search, reset_collection
 
reset_collection()  # clear old data if needed
add_chunks("your document text here", source="my_doc.txt")
 
results = search("your question here", top_k=3)
for r in results:
    print(r)
```
 
## Highlights
 
- Diagnosed and fixed a ChromaDB dimension-lock issue, a chunker
  backward-progress bug, and a Python late-binding defaults bug — see
  [LEARNINGS.md](LEARNINGS.md) for details.
- Empirically verified that overly small chunks (`chunk_size=10`) produce
  fragmented, low-quality retrieval, while 300–1000 character chunks stay
  semantically coherent.
## Project structure
 
```
rag-qa-system/
├── app/
│   ├── config.py               # centralized settings
│   └── core/
│       ├── document_loader.py  # PDF/TXT/CSV -> raw text
│       ├── chunker.py          # raw text -> overlapping chunks
│       ├── embeddings.py       # text -> vectors (local model, cached)
│       └── vector_store.py     # Chroma wrapper: add/search/reset
├── data/sample_docs/
├── requirements.txt
└── .env.example
