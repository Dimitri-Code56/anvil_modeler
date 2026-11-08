from __future__ import annotations

import base64
import mimetypes
from functools import lru_cache
from pathlib import Path

from langchain.chat_models import init_chat_model

from .config import settings


@lru_cache(maxsize=8)
def get_llm(model: str | None = None, max_tokens: int = 16000, provider: str | None = None, temperature: float = 0.2):
    """Modelo de chat por provedor: anthropic (API) ou ollama (local, precisa de `pip install -e ".[local]"`)."""
    provider = provider or settings.provider
    model = model or settings.model
    if provider == "ollama":
        # num_predict = limite de tokens de saída; contexto maior para caber skills + ficha de API
        return init_chat_model(model, model_provider="ollama", base_url=settings.ollama_url,
                               num_predict=min(max_tokens, 6000), num_ctx=settings.num_ctx, temperature=temperature)
    # modelos recentes da Anthropic não aceitam `temperature` (erro 400 "Extra inputs are not permitted");
    # a variação entre tentativas fica só para os modelos locais
    return init_chat_model(model, model_provider=provider, max_tokens=max_tokens)


def structured(llm, schema, provider: str | None = None):
    """Saída estruturada: modelos locais vão melhor com JSON Schema do que com chamada de ferramenta."""
    # Ollama: JSON Schema funciona melhor que tool calling. Anthropic: os modelos 5.5 não aceitam mais
    # "forçar" a chamada de ferramenta (aviso do langchain-anthropic no Opus 5.5), então usamos a saída
    # estruturada nativa por JSON Schema também.
    return llm.with_structured_output(schema, method="json_schema")


def image_block(path: str | Path) -> dict:
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    data = base64.b64encode(Path(path).read_bytes()).decode()
    return {"type": "image", "source_type": "base64", "data": data, "mime_type": mime}


def text_of(message) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(b.get("text", "") for b in content if isinstance(b, dict))
