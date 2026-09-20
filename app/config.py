from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    chunk_size: int = 100
    chunk_overlap: int = 10
    embedding_model: str = "all-MiniLM-L6-v2"
    chroma_persist_dir: str = "./data/chroma_db"
    collection_name: str = "rag_documents"

settings = Settings()
