from openai import OpenAI

def generate_answer(question: str, context_chunks: list[dict]) -> str:
    context_block = "\n\n".join(chunk["text"] for chunk in context_chunks)
    prompt = f"You are a helpful assistant. Answer the question using ONLY the context below.\nif the answer isn't in the context, say 'I don't have enough information to answer that.'\n\nquestion: {question}\n\ncontext:\n{context_block}\n\nanswer:"
    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    response = client.chat.completions.create(
        model="llama3.1:8b",
        messages=[{"role": "user", "content": prompt}],
    )
    answer = response.choices[0].message.content
    return answer
