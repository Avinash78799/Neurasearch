import logging
from langchain_ollama import ChatOllama, OllamaEmbeddings
from config import settings

logger = logging.getLogger("neurasearch.core.model_registry")

_llm = None
_embeddings = None

def get_llm() -> ChatOllama:
    """Retrieve or initialize the global ChatOllama instance (lazy singleton)."""
    global _llm
    if _llm is None:
        logger.info("Initializing global ChatOllama instance (model=%s, url=%s)", 
                    settings.ollama_llm_model, settings.ollama_base_url)
        _llm = ChatOllama(
            model=settings.ollama_llm_model,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature,
            num_predict=settings.llm_num_predict,
            num_ctx=settings.llm_num_ctx,
        )
    return _llm

def get_embeddings() -> OllamaEmbeddings:
    """Retrieve or initialize the global OllamaEmbeddings instance (lazy singleton)."""
    global _embeddings
    if _embeddings is None:
        logger.info("Initializing global OllamaEmbeddings instance (model=%s, url=%s)", 
                    settings.ollama_embed_model, settings.ollama_base_url)
        _embeddings = OllamaEmbeddings(
            model=settings.ollama_embed_model,
            base_url=settings.ollama_base_url,
        )
    return _embeddings
