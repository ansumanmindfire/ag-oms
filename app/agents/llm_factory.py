"""Centralized LLM Factory for routing models across Gemini, Groq, and OpenRouter."""

from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from app.config import settings, logger


def get_llm(temperature: float = 0.1) -> Any:
    """Instantiate and return the LLM based on configured LLM_PROVIDER and LLM_MODEL.

    Supported Providers:
    1. openrouter
    2. groq
    3. gemini / google
    """
    provider = settings.LLM_PROVIDER.lower().strip()
    model_name = settings.LLM_MODEL.strip()

    # OpenRouter routing
    if provider == "openrouter":
        logger.info(f"Initializing OpenRouter LLM: '{model_name}'")
        return ChatOpenAI(
            model=model_name,
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            temperature=temperature,
        )

    # Groq routing
    if provider == "groq":
        logger.info(f"Initializing Groq LLM: '{model_name}'")
        return ChatGroq(
            model=model_name,
            groq_api_key=settings.GROQ_API_KEY,
            temperature=temperature,
        )

    # Gemini routing
    logger.info(f"Initializing Gemini LLM: '{model_name}'")
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=temperature,
    )
