from langchain_openai import ChatOpenAI

from app.config import get_settings, is_ai_configured

_client: ChatOpenAI | None = None


def get_llm() -> ChatOpenAI | None:
    if not is_ai_configured():
        return None
    global _client
    if _client is None:
        settings = get_settings()
        _client = ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, temperature=0)
    return _client
