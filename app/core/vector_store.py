import chromadb
from app.core.chunker import chunk_text
from app.core.embeddings import embed_texts
from app.config import settings

print(settings.chunk_size)
client = chromadb.PersistentClient(path=settings.chroma_persist_dir)

collection = client.get_or_create_collection(name=settings.collection_name)

#function to add chunks to chromadb
def add_chunks(text, source, chunk_size=None, chunk_overlap=None):
    chunks = chunk_text(
                text, 
                chunk_size=chunk_size or settings.chunk_size, 
                chunk_overlap=chunk_overlap or settings.chunk_overlap
            )
    chunk_list = [chunk[0] for chunk in chunks]  # Extract only the text from the tuples
    chunk_embeddings = embed_texts(chunk_list)
    collection.add(
        ids=[str(source) + "_" + str(i) for i in range(len(chunks))],
        embeddings=chunk_embeddings,
        documents=chunk_list,
        metadatas=[{"source": source, "start": chunk[1], "end": chunk[2]} for chunk in chunks]
    )


def search(query, top_k):
    query_embedding = embed_texts([query])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    return [{"text": doc,
            "source":meta["source"],
            "start":meta["start"],
            "end":meta["end"],
            "distance":dist
            } for doc, meta, dist in zip(
                results['documents'][0], 
                results['metadatas'][0], 
                results['distances'][0]
                )]

def reset_collection():
    client.delete_collection(name=settings.collection_name)
    global collection
    collection = client.get_or_create_collection(name=settings.collection_name)

reset_collection()

add_chunks("The stock market saw significant volatility today as investors reacted to inflation data.", source="finance.txt")
print(collection.count())   
results = search("What happened in financial markets?", top_k=2)
for r in results:
    print(r)