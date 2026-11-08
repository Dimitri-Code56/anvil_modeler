"""Testa o servidor anvil-tools pelo protocolo MCP, como o agente vai usar.

Uso (WSL, venv ativo, Blender aberto com a ponte MCP):  python scripts/testar_ferramentas.py
Monta uma mesinha só com ferramentas e renderiza.
"""
import asyncio
import json

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from anvil_modeler.config import settings


async def main() -> None:
    cfg = {"anvil": settings.mcp_servers()["anvil"]}
    client = MultiServerMCPClient(cfg)
    async with client.session("anvil") as session:
        tools = {t.name: t for t in await load_mcp_tools(session)}
        print(f"{len(tools)} ferramentas:", ", ".join(sorted(tools)))

        async def call(name, **kw):
            out = await tools[name].ainvoke(kw)
            print(f"  {name}: {str(out)[:160]}")
            return out

        await call("iniciar_asset", nome="mesinha_teste")
        await call("caixa", nome="tampo", tamanho=[0.6, 0.4, 0.03], posicao=[0, 0, 0.5], chanfro=0.006, material="wood", cor=[0.45, 0.28, 0.15])
        await call("revolucao", nome="perna", perfil=[[0.02, 0], [0.025, 0.05], [0.018, 0.25], [0.022, 0.45], [0.025, 0.485]], posicao=[0.26, -0.16, 0], material="wood", cor=[0.4, 0.25, 0.13])
        await call("espelhar", nome="perna", eixo="X", novo_nome="perna_e")
        await call("espelhar", nome="perna", eixo="Y", novo_nome="perna_t")
        await call("espelhar", nome="perna_e", eixo="Y", novo_nome="perna_te")
        await call("listar_objetos")
        await call("metricas")
        await call("renderizar")


if __name__ == "__main__":
    asyncio.run(main())
