"""Mostra os detalhes (resposta, evidência e trace) dos casos escolhidos da última rodada.

    python scripts/detalhar_casos.py          # os casos que falharam na última rodada
    python scripts/detalhar_casos.py 3,5,6    # casos específicos
"""
import json
import sys
from pathlib import Path

MARCA = {True: "✅", False: "❌", None: "⏭️ não executado"}

caminho = Path(__file__).resolve().parents[1] / "data" / "avaliacao_casos.json"
dados = json.loads(caminho.read_text(encoding="utf-8"))
print(f"Rodada de {dados['data']} — modelo {dados['modelo']}\n")

escolha = sys.argv[1] if len(sys.argv) > 1 else None
if escolha:
    nums = {int(x) for x in escolha.split(",")}
else:
    nums = {c["n"] for c in dados["casos"] if not c["ok"] and c["ok"] is not None} or \
           {c["n"] for c in dados["casos"] if c["ok"] is not True}

for c in dados["casos"]:
    if c["n"] not in nums:
        continue
    print("=" * 70)
    print(f"caso {c['n']} — {c['nome']}   {MARCA[c['ok']]}")
    print("-" * 70)
    print("EVIDÊNCIA:")
    for e in c.get("evidencia") or []:
        print("  -", e)
    print("-" * 70)
    print("RESPOSTA OBTIDA:")
    print(c.get("obtido") or "(vazio)")
    print("-" * 70)
    print("TRACE:")
    for t in c.get("trace") or []:
        print("  *", t)
    print()
