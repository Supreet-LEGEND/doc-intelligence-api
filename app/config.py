from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "AI Document Intelligence API"
    debug: bool = True
    
    upload_dir: str = "data/uploads"
    index_dir: str = "data/index"
    
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    faiss_index_type: str = "IndexFlatIP"
    
    top_k: int = 5
    similarity_threshold: float = 0.7
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()