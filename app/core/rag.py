from app.core.vector_store import search
from app.core.generator import generate_answer

def answer_question(question: str, top_k: int = 3) -> tuple[str, list[str]]:
    context_chunks = search(question, top_k=top_k)

    #remove weak or irrelevant chunks based on distance threshold 
    new_context_chunks = [chunk for chunk in context_chunks if chunk["distance"] <= 1.5]

    if not new_context_chunks:
        return "I don't have enough information to answer that.", []
    
    answer = generate_answer(question, new_context_chunks)

    # build a sources list/string from new_context_chunks and append to answer
    unique_sources = list(set(chunk["source"] for chunk in new_context_chunks))
    
    return answer, unique_sources
