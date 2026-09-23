# RAG Q&A System
 
A Retrieval-Augmented Generation (RAG) pipeline built from scratch, one
component at a time, to understand every layer rather than gluing together
a framework.
 
## Status: Week 2 complete — Retrieval, Grounded Generation & API
 
- **Document loader** (`app/core/document_loader.py`) — extracts plain text
  from PDF, TXT, and CSV files via a dispatch-table pattern.
- **Chunker** (`app/core/chunker.py`) — hand-written, boundary-aware text
  splitter with configurable size/overlap.
- **Embeddings** (`app/core/embeddings.py`) — free, local embeddings via
  `sentence-transformers/all-MiniLM-L6-v2`, model cached for reuse.
- **Vector store** (`app/core/vector_store.py`) — ChromaDB wrapper for
  storing embeddings with source/position metadata and semantic search.
- **Generator** (`app/core/generator.py`) — grounded answer generation via
  an OpenAI-compatible LLM client; runs against a local Ollama model
  (Llama 3.1) for free, zero-cost development, swappable to a hosted
  inference API for production.
- **RAG pipeline** (`app/core/rag.py`) — ties retrieval and generation
  together: retrieves relevant chunks, filters weak matches by distance
  threshold, generates a grounded answer, and returns structured source
  citations.
- **API** (`app/main.py`, `app/api/routes/qa.py`) — FastAPI service
  exposing the pipeline over HTTP with request/response validation via
  Pydantic models.
- **Config** (`app/config.py`) — centralized settings via
  `pydantic-settings`, overridable via environment variables.
## Why these choices
 
| Decision | Reasoning |
|---|---|
| Local embeddings, not an API | Zero cost while learning; swappable later |
| Hand-written chunker | Understanding overlap/boundary logic over importing a pre-built splitter |
| `pydantic-settings` | Confirmed env-var overrides work — useful for Docker/CI later |
| Chroma (local) | No signup/server needed to start; may migrate to Qdrant later |
| Local Ollama + OpenAI-compatible client | Free during development; the client code is provider-agnostic, so swapping to a hosted API (e.g. Groq) for deployment is a config change, not a rewrite |
| Deterministic empty-context short-circuit | LLM grounding instructions are unreliable when given zero context; checking in code before calling the LLM is more robust than trusting prompt wording |
| Structured API response (answer + sources as separate fields) | Easier for any consumer (frontend, script) to use than parsing sources out of a combined string |
 
## Setup
 
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
 
You'll also need [Ollama](https://ollama.com) installed separately (not a
Python package) and a model pulled:
```bash
ollama pull llama3.1:8b
```
 
## Usage
 
### As a library
 
```python
from app.core.rag import answer_question
 
answer, sources = answer_question("your question here", top_k=3)
print(answer)
print(sources)
```
 
### As an API
 
```bash
uvicorn app.main:app --reload
```
Then open `http://127.0.0.1:8000/docs` for an interactive testing UI, or:
```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "your question here", "top_k": 3}'
```
Returns:
```json
{"answer": "...", "sources": ["your_doc.txt"]}
```
 
## Highlights
 
- Diagnosed and fixed a ChromaDB dimension-lock issue, a chunker
  backward-progress bug, and a Python late-binding defaults bug — see
  [LEARNINGS.md](LEARNINGS.md) for details.
- Empirically verified that overly small chunks (`chunk_size=10`) produce
  fragmented, low-quality retrieval, while 300–1000 character chunks stay
  semantically coherent.
- Found that LLM grounding instructions reliably prevent hallucination
  when *irrelevant* context is present, but are unreliable when context is
  *empty* — fixed with a deterministic code-level check rather than a
  prompt tweak. Full writeup in [LEARNINGS.md](LEARNINGS.md).
## Project structure
 
```
rag-qa-system/
├── app/
│   ├── config.py               # centralized settings
│   ├── main.py                 # FastAPI app entrypoint
│   ├── api/
│   │   └── routes/
│   │       └── qa.py           # /ask endpoint + request/response models
│   └── core/
│       ├── document_loader.py  # PDF/TXT/CSV -> raw text
│       ├── chunker.py          # raw text -> overlapping chunks
│       ├── embeddings.py       # text -> vectors (local model, cached)
│       ├── vector_store.py     # Chroma wrapper: add/search/reset
│       ├── generator.py        # grounded LLM answer generation
│       └── rag.py              # retrieval + generation + citations
├── data/sample_docs/
├── requirements.txt
└── .env.example
```