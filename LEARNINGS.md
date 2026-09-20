Learnings & Design Notes

Detailed notes on bugs hit, how they were diagnosed, and design decisions made while building this project. Kept separate from the README so the README stays quick to skim.

Bugs found and fixed
1. Chunker backward-progress bug

Symptom: the sliding-window chunker could, in rare cases, move its start position backward instead of forward, risking an infinite loop or negative string indexing.

Root cause: when searching backward from the end of a chunk window for a natural break point (paragraph break, sentence end, space), an early match very close to the window's start would set end to a tiny value. Then start = end - chunk_overlap could compute to a position before the original start.

Fix: only accept a found boundary if it falls past a minimum threshold (50% of chunk_size) into the search window. If no boundary clears that threshold, fall back to the raw chunk_size cutoff.

Verification: printed start on every loop iteration across a real multi-paragraph test string and confirmed it strictly increased with no repeats or backward jumps. Also verified overlap was real by comparing the tail of chunk N against the head of chunk N+1 and confirming the shared substring actually matched.

2. ChromaDB dimension lock-in

Symptom: InvalidArgumentError: Collection expecting embedding with dimension of 3, got 384 when trying to add real embeddings.

Root cause: a Chroma collection permanently fixes its expected vector dimensionality based on the first data ever inserted into it. Earlier testing had inserted placeholder 3-dimensional vectors into the same persistent collection (./data/chroma_db) to sanity-check the .add() API. Because PersistentClient writes to disk, that test data didn't disappear between script runs — it silently locked in dimension 3 for the whole collection.

Fix: client.delete_collection(name=...) to remove the stale collection, then let get_or_create_collection recreate it fresh so it correctly locks in 384 dimensions from real embedding data.

Broader lesson: "persistent" storage cuts both ways — data survives between runs (good), but leftover test/junk data also survives and needs deliberate cleanup. Built a reset_collection() utility as a result.

3. Stale data accumulating across test runs

Symptom: collection.count() kept returning far more chunks than expected (e.g. 14–15 instead of 1–2), and search results included irrelevant fragments ("The stock", "ck market") from earlier, unrelated test runs.

Root cause: every add_chunks() call during iterative development added to the same persistent collection without ever clearing prior test data. IDs were namespaced by source filename, so re-using a source name (e.g. finance.txt) across multiple runs with different chunk sizes could also leave a mix of chunk counts from different runs coexisting.

Fix: call reset_collection() before running a controlled test, and actually check collection.count() against a predicted value rather than assuming a run succeeded just because it produced no errors.

4. Python late-binding default arguments

Symptom: wiring settings.chunk_size in as a function's default argument value looked correct, but wouldn't reflect changes to settings made after the module was imported.

Root cause: Python evaluates default argument values once, at function definition time — not on every call. def f(x=settings.value): bakes in whatever settings.value was at import time, permanently, until the process restarts.

Fix: use None as the default, and read the live settings value from inside the function body instead:

python
def add_chunks(text, source, chunk_size=None, chunk_overlap=None):
    chunk_size = chunk_size or settings.chunk_size
    ...

Related gotcha noted but not yet an issue: x or default treats 0 as "not provided" too, since 0 is falsy in Python. Not a problem here since chunk_size <= 0 is already rejected elsewhere with a clear error, but worth remembering as a general pattern trap (x if x is not None else default is more precise when 0 is a valid input).

Design decisions
Why a hand-written chunker instead of a library splitter: the goal was understanding why chunking works the way it does (embedding input limits, boundary preservation, overlap), not just getting a working pipeline. A library splitter would have hidden that reasoning.
Why pydantic-settings over plain module-level constants: verified directly that setting an environment variable (e.g. CHUNK_SIZE=999) before running the app was picked up automatically with zero code changes — a plain constants file can't do this without extra plumbing. This matters for Docker/CI environments later, where config often needs to be overridden without touching source code.
Why local embeddings instead of an API from the start: zero cost while iterating and testing repeatedly during development; the embedding layer is designed to be swappable later if higher-quality (but paid) embeddings are wanted.
Retrieval quality observations

Empirically compared chunk sizes on the same source text:

chunk_size=10: produced fragmented, often mid-word chunks (e.g. "ck market" — half of "stock market"). Retrieval on these returned technically-matching but semantically useless fragments.
chunk_size=300–1000: produced coherent chunks; search queries phrased very differently from the source text (e.g. "how do you measure if a RAG answer is trustworthy?" against source text about "faithfulness and answer relevancy") still correctly retrieved the relevant chunk — confirming retrieval is working on semantic meaning, not keyword overlap.
Distance-vs-similarity: Chroma's default distance metric is squared L2, not cosine similarity directly. For normalized vectors, the two are related by squared_L2_distance = 2 - 2 × cosine_similarity — derived by hand to convert a reported Chroma distance back into an intuitive cosine similarity score.