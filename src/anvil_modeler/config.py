from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

# Cada modo liga/desliga partes do harness. É isso que o benchmark compara.
MODES: dict[str, dict[str, bool]] = {
    "baseline":    {"use_skills": False, "use_rag": False, "use_loop": False, "use_agent": False},
    "skills_only": {"use_skills": True,  "use_rag": True,  "use_loop": False, "use_agent": False},
    "loop_only":   {"use_skills": False, "use_rag": False, "use_loop": True,  "use_agent": False},
    "full":        {"use_skills": True,  "use_rag": True,  "use_loop": True,  "use_agent": False},
    # o modelo monta o asset chamando as ferramentas do anvil-tools, peça por peça
    "agente":      {"use_skills": True,  "use_rag": False, "use_loop": False, "use_agent": True},
}


# Preço por milhão de tokens (USD): entrada, saída, escrita de cache, leitura de cache.
# Haiku 5.5: faixa de pedidos com até 100k tokens (os do Anvil ficam bem abaixo disso).
# Modelos locais (Ollama) custam 0. Para outro modelo: ANVIL_PRICE="entrada,saida[,cache_w,cache_r]".
PRICES: dict[str, tuple[float, float, float, float]] = {
    "claude-haiku-5-5": (0.10, 0.50, 0.125, 0.01),
    # Opus 5.5: entrada/saída/leitura de cache publicados; escrita de cache estimada em 1,25x a entrada
    "claude-opus-5-5": (4.00, 20.00, 5.00, 0.20),
}


def price_for(model: str, provider: str | None = None) -> tuple[float, float, float, float] | None:
    env = os.getenv("ANVIL_PRICE")
    if env:
        v = [float(x) for x in env.split(",")]
        return tuple((v + [0.0, 0.0])[:4])  # type: ignore[return-value]
    for k, p in PRICES.items():
        if model.startswith(k):
            return p
    if provider == "ollama" or ":" in model:  # nomes do Ollama têm ":" (qwen2.5-coder:7b)
        return (0.0, 0.0, 0.0, 0.0)
    return None


@dataclass
class Settings:
    # provedor por papel: "anthropic" (API) ou "ollama" (modelo local); dá para misturar
    provider: str = os.getenv("ANVIL_PROVIDER", "anthropic")
    judge_provider: str = os.getenv("ANVIL_JUDGE_PROVIDER", os.getenv("ANVIL_PROVIDER", "anthropic"))
    fast_provider: str = os.getenv("ANVIL_FAST_PROVIDER", os.getenv("ANVIL_PROVIDER", "anthropic"))
    model: str = os.getenv("ANVIL_MODEL", "claude-sonnet-5-5")
    judge_model: str = os.getenv("ANVIL_JUDGE_MODEL", os.getenv("ANVIL_MODEL", "claude-sonnet-5-5"))
    # modelo barato para tarefas simples (prompt do concept)
    fast_model: str = os.getenv("ANVIL_FAST_MODEL", "claude-haiku-5-5")
    image_backend: str = os.getenv("ANVIL_IMAGE_BACKEND", "sdxl_turbo")
    max_iters: int = int(os.getenv("ANVIL_MAX_ITERS", "3"))
    # modo agente: limite de rodadas de chamada de ferramenta
    agent_max_steps: int = int(os.getenv("ANVIL_AGENT_STEPS", "40"))
    # perfil do modelo no modo agente: "fraco" (ferramentas de alto nível + conferências e consertos do
    # harness) ou "forte" (escreve o próprio bpy via executar_python, sem muletas). "auto": API = forte, Ollama = fraco
    perfil: str = os.getenv("ANVIL_PERFIL", "auto")
    # alvo da modelagem: "jogo" (orçamento de tempo real) ou "completo" (render/portfólio, mais denso)
    alvo: str = os.getenv("ANVIL_ALVO", "jogo")
    # teto de custo do modo agente por run, em US$ (0 = sem teto); ao passar, o agente para e o asset é renderizado como está
    max_usd: float = float(os.getenv("ANVIL_MAX_USD", "0"))

    def model_profile(self) -> str:
        if self.perfil in ("forte", "fraco"):
            return self.perfil
        return "fraco" if self.provider == "ollama" else "forte"
    # juiz visual: "off" desliga (o loop passa a corrigir só erros técnicos)
    judge_enabled: bool = os.getenv("ANVIL_JUDGE", "on").lower() != "off"
    # contexto do modelo local (memória de vídeo): 12k cabe com um modelo de 7B em 6 GB
    num_ctx: int = int(os.getenv("ANVIL_NUM_CTX", "12288"))
    # endereço do servidor Ollama (ex.: rodando no WSL e acessado pelo Windows)
    ollama_url: str = os.getenv("ANVIL_OLLAMA_URL", "http://localhost:11434")
    default_style: str = os.getenv("ANVIL_STYLE", "realista")
    render_res: int = int(os.getenv("ANVIL_RENDER_RES", "768"))
    approve_score: float = 4.0
    runs_dir: Path = field(default_factory=lambda: Path(os.getenv("ANVIL_RUNS_DIR", ROOT / "runs")).resolve())
    skills_dir: Path = ROOT / "skills"
    # assistente de perguntas (RAG agêntico): modelo barato por padrão (o "rápido"); embeddings locais no Ollama
    blender_version: str = os.getenv("ANVIL_BLENDER_VERSION", "5.2")
    rag_provider: str = os.getenv("ANVIL_RAG_PROVIDER", os.getenv("ANVIL_FAST_PROVIDER", os.getenv("ANVIL_PROVIDER", "anthropic")))
    rag_model: str = os.getenv("ANVIL_RAG_MODEL", os.getenv("ANVIL_FAST_MODEL", "claude-haiku-5-5"))
    embed_model: str = os.getenv("ANVIL_EMBED_MODEL", "nomic-embed-text")
    docs_dir: Path = ROOT / "data" / "docs"
    index_dir: Path = ROOT / "data" / "index"
    memory_db: Path = ROOT / "data" / "memoria.sqlite"
    chat_mcp: bool = os.getenv("ANVIL_CHAT_MCP", "on").lower() != "off"
    mcp_config: Path = field(default_factory=lambda: Path(os.getenv("ANVIL_MCP_CONFIG", ROOT / "config" / "mcp_servers.json")))

    def mcp_servers(self) -> dict:
        if not self.mcp_config.exists():
            raise FileNotFoundError(
                f"{self.mcp_config} não existe. Copie config/mcp_servers.json.example "
                "e preencha com o command/args do MCP do Blender (o mesmo do Claude Desktop)."
            )
        return json.loads(self.mcp_config.read_text(encoding="utf-8"))


settings = Settings()
