# Learnings & Design Notes
 
Detailed notes on bugs hit, how they were diagnosed, and design decisions
made while building this project. Kept separate from the README so the
README stays quick to skim.
 
## Bugs found and fixed
 
### 1. Chunker backward-progress bug
 
**Symptom:** the sliding-window chunker could, in rare cases, move its
`start` position *backward* instead of forward, risking an infinite loop
or negative string indexing.
 
**Root cause:** when searching backward from the end of a chunk window for
a natural break point (paragraph break, sentence end, space), an early
match very close to the window's start would set `end` to a tiny value.
Then `start = end - chunk_overlap` could compute to a position *before*
the original `start`.
 
**Fix:** only accept a found boundary if it falls past a minimum threshold
(50% of `chunk_size`) into the search window. If no boundary clears that
threshold, fall back to the raw `chunk_size` cutoff.
 
**Verification:** printed `start` on every loop iteration across a real
multi-paragraph test string and confirmed it strictly increased with no
repeats or backward jumps. Also verified overlap was real by comparing the
tail of chunk N against the head of chunk N+1 and confirming the shared
substring actually matched.
 
### 2. ChromaDB dimension lock-in
 
**Symptom:** `InvalidArgumentError: Collection expecting embedding with
dimension of 3, got 384` when trying to add real embeddings.
 
**Root cause:** a Chroma collection permanently fixes its expected vector
dimensionality based on the *first* data ever inserted into it. Earlier
testing had inserted placeholder 3-dimensional vectors into the same
persistent collection (`./data/chroma_db`) to sanity-check the `.add()`
API. Because `PersistentClient` writes to disk, that test data didn't
disappear between script runs — it silently locked in dimension 3 for the
whole collection.
 
**Fix:** `client.delete_collection(name=...)` to remove the stale
collection, then let `get_or_create_collection` recreate it fresh so it
correctly locks in 384 dimensions from real embedding data.
 
**Broader lesson:** "persistent" storage cuts both ways — data survives
between runs (good), but leftover test/junk data also survives and needs
deliberate cleanup. Built a `reset_collection()` utility as a result.
 
### 3. Stale data accumulating across test runs
 
**Symptom:** `collection.count()` kept returning far more chunks than
expected (e.g. 14–15 instead of 1–2), and search results included
irrelevant fragments (`"The stock"`, `"ck market"`) from earlier,
unrelated test runs.
 
**Root cause:** every `add_chunks()` call during iterative development
added to the same persistent collection without ever clearing prior test
data. IDs were namespaced by source filename, so re-using a source name
(e.g. `finance.txt`) across multiple runs with different chunk sizes could
also leave a mix of chunk counts from different runs coexisting.
 
**Fix:** call `reset_collection()` before running a controlled test, and
actually check `collection.count()` against a predicted value rather than
assuming a run succeeded just because it produced no errors.
 
### 4. Python late-binding default arguments
 
**Symptom:** wiring `settings.chunk_size` in as a function's default
argument value looked correct, but wouldn't reflect changes to `settings`
made after the module was imported.
 
**Root cause:** Python evaluates default argument values **once, at
function definition time** — not on every call. `def f(x=settings.value):`
bakes in whatever `settings.value` was at import time, permanently, until
the process restarts.
 
**Fix:** use `None` as the default, and read the live `settings` value
from inside the function body instead:
```python
def add_chunks(text, source, chunk_size=None, chunk_overlap=None):
    chunk_size = chunk_size or settings.chunk_size
    ...
```
 
**Related gotcha noted but not yet an issue:** `x or default` treats `0`
as "not provided" too, since `0` is falsy in Python. Not a problem here
since `chunk_size <= 0` is already rejected elsewhere with a clear error,
but worth remembering as a general pattern trap (`x if x is not None else
default` is more precise when `0` is a valid input).
 
## Design decisions
 
- **Why a hand-written chunker instead of a library splitter:** the goal
  was understanding *why* chunking works the way it does (embedding input
  limits, boundary preservation, overlap), not just getting a working
  pipeline. A library splitter would have hidden that reasoning.
- **Why `pydantic-settings` over plain module-level constants:** verified
  directly that setting an environment variable (e.g. `CHUNK_SIZE=999`)
  before running the app was picked up automatically with zero code
  changes — a plain constants file can't do this without extra plumbing.
  This matters for Docker/CI environments later, where config often needs
  to be overridden without touching source code.
- **Why local embeddings instead of an API from the start:** zero cost
  while iterating and testing repeatedly during development; the
  embedding layer is designed to be swappable later if higher-quality
  (but paid) embeddings are wanted.
## Retrieval quality observations
 
Empirically compared chunk sizes on the same source text:
- `chunk_size=10`: produced fragmented, often mid-word chunks (e.g.
  `"ck market"` — half of "stock market"). Retrieval on these returned
  technically-matching but semantically useless fragments.
- `chunk_size=300–1000`: produced coherent chunks; search queries phrased
  very differently from the source text (e.g. "how do you measure if a
  RAG answer is trustworthy?" against source text about "faithfulness and
  answer relevancy") still correctly retrieved the relevant chunk —
  confirming retrieval is working on semantic meaning, not keyword
  overlap.
- Distance-vs-similarity: Chroma's default distance metric is squared L2,
  not cosine similarity directly. For normalized vectors, the two are
  related by `squared_L2_distance = 2 - 2 × cosine_similarity` — derived
  by hand to convert a reported Chroma `distance` back into an intuitive
  cosine similarity score.

  Week 2: Generation & API
5. Grounding instructions behave differently for "irrelevant context" vs. "empty context"

Symptom: a question with no relevant stored content sometimes produced a fully hallucinated answer (e.g. a detailed pasta carbonara recipe from training knowledge) despite an explicit prompt instruction saying "answer using ONLY the context below."

Root cause, found in two stages:

First suspected the distance-based relevance filter (distance <= 1.5) was letting weak matches through. Investigated by printing the actual embedding vectors and re-running searches cleanly — this ruled out a filtering bug and also caught a stale-terminal-output red herring: two different queries appeared to produce an identical distance value, which turned out to be old output pasted alongside a new run, not a real result. Lesson: always verify printed output actually came from the code being discussed, especially across multiple terminal runs.
With the filter confirmed correct, found the real cause: when new_context_chunks is genuinely empty, generate_answer() still gets called with an empty list, producing a prompt with a blank context section. The LLM does not reliably treat "context section is empty" the same as "context is irrelevant" — it tends to fall back to answering from training knowledge when given nothing, even with an explicit grounding instruction in the prompt.

Fix: don't rely on the LLM to detect a zero-context situation. Add a deterministic check in answer_question() that short-circuits and returns the refusal message before calling the LLM at all, whenever no chunks survive the relevance filter:

python
if not new_context_chunks:
    return "I don't have enough information to answer that.", []

Broader lesson: this is the same principle as the source-citation design decision below — anywhere a fact can be determined with certainty in code, don't outsource that decision to the LLM's judgment, since LLM behavior on edge cases (especially empty/near-empty input) is inherently less predictable than explicit logic.

6. Return-type consistency across all branches of a function

Symptom: a function type-hinted as -> tuple[str, list[str]] returned a plain str on one branch and an actual tuple on another, which would crash any caller unpacking the result (answer, sources = ...).

Root cause: Python type hints are documentation, not enforcement — nothing prevents a function from violating its own declared return type on a branch that's easy to overlook (in this case, the early-return "no context" branch, added after the main logic was already working).

Fix: manually audited every return statement in the function and made sure each one matched the declared shape.

Design decisions (Week 2 additions)
Why source citations are appended in code (answer_question), not requested from the LLM in the prompt: the exact set of retrieved chunks (and their source files) is already known with certainty in Python before the LLM is ever called. Asking the LLM to self-report which sources it used risks hallucinated or misattributed citations, for no benefit — it's strictly worse than a value already available deterministically.
Why generate_answer() doesn't handle source formatting or empty-context short-circuiting itself: keeping it scoped to "context + question → answer" keeps it independently testable and reusable (e.g. directly callable for future evaluation work) without unrelated formatting or control-flow logic mixed in.
Why the FastAPI response returns answer and sources as separate structured fields, not one combined string: a plain string return was fine for direct Python calls, but over an HTTP API boundary, a consumer (frontend, another service) would have to parse sources back out of free text — fragile and unnecessary when Pydantic can just declare the real shape of the data.
Why Ollama (local) during development, with an OpenAI-compatible client: the openai Python package is a client library that speaks a now-common request/response format, not something tied to OpenAI's own servers. Ollama implements that same format, so the exact same client code works locally for free during development, and can point at a hosted provider (e.g. Groq) later by only changing base_url and model name — relevant because free hosting tiers used for deployment don't have the compute to self-host an LLM the way a local machine can.