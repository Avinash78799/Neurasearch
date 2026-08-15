"""
NeuraSearch – Model Registry
Unified model factory supporting local Ollama models (offline privacy) and
high-performance cloud providers (Groq Llama 3.3 70B, OpenAI GPT-4o, DeepSeek, OpenRouter).
"""

import logging
from typing import Optional
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.chat_models import ChatOpenAI
from config import settings

logger = logging.getLogger("neurasearch.core.model_registry")

_llm = None
_embeddings = None


def get_llm(provider: Optional[str] = None):
    """Retrieve or initialize the active LLM instance based on provider settings.

    Supported providers:
    - 'groq': Free tier LPU inference with Llama 3.3 70B (350+ tokens/sec)
    - 'openai': GPT-4o / GPT-4o-mini
    - 'deepseek': DeepSeek-V3 / DeepSeek-R1
    - 'openrouter': OpenRouter unified API
    - 'ollama': Local Ollama instance (default)
    """
    global _llm
    active_provider = (provider or settings.llm_provider or "ollama").lower().strip()

    # If Groq is configured or selected
    if active_provider == "groq" or (settings.groq_api_key and active_provider != "ollama"):
        api_key = settings.groq_api_key or "gsk_dummy"
        model_name = settings.groq_model or "llama-3.3-70b-versatile"
        logger.info("Initializing Groq cloud LLM provider (model=%s)", model_name)
        return ChatOpenAI(
            openai_api_key=api_key,
            openai_api_base="https://api.groq.com/openai/v1",
            model_name=model_name,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_num_predict,
        )

    # If OpenAI is configured or selected
    if active_provider == "openai" and settings.openai_api_key:
        logger.info("Initializing OpenAI cloud LLM provider (model=%s)", settings.openai_model)
        return ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            model_name=settings.openai_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_num_predict,
        )

    # If DeepSeek is configured or selected
    if active_provider == "deepseek" and settings.deepseek_api_key:
        logger.info("Initializing DeepSeek cloud LLM provider (model=%s)", settings.deepseek_model)
        return ChatOpenAI(
            openai_api_key=settings.deepseek_api_key,
            openai_api_base="https://api.deepseek.com/v1",
            model_name=settings.deepseek_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_num_predict,
        )

    # Default: Local Ollama
    if _llm is None or active_provider == "ollama":
        logger.info("Initializing local Ollama ChatOllama instance (model=%s, url=%s)", 
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
