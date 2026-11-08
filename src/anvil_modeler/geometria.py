"""Conferência de geometria do asset: regras fixas que o harness aplica no lugar do modelo.

Modelos pequenos erram a conta de onde cada peça fica (centro x base, peça embaixo do chão,
peça solta no ar). Aqui, a partir das caixas envolventes de cada peça no mundo, geramos a lista
de problemas em português, já com a correção numérica sugerida.
"""
from __future__ import annotations

import re

TOL = 0.01  # 1 cm


def _touch(a: dict, b: dict) -> bool:
    return all(a["min"][i] <= b["max"][i] + TOL and b["min"][i] <= a["max"][i] + TOL for i in range(3))


def _inside(a: dict, b: dict) -> bool:
    t = 0.002  # 2 mm: só acusa quando a peça some mesmo dentro da outra
    return all(a["min"][i] >= b["min"][i] - t and a["max"][i] <= b["max"][i] + t for i in range(3))


def _xy_overlap(a: dict, b: dict) -> bool:
    return all(a["min"][i] <= b["max"][i] + TOL and b["min"][i] <= a["max"][i] + TOL for i in range(2))


def plan_dims(text: str | None) -> list[float] | None:
    nums = [float(n.replace(",", ".")) for n in re.findall(r"\d+(?:[.,]\d+)?", str(text or ""))]
    return nums[:3] if len(nums) >= 3 else None


def check(objs: list[dict], dims: list[float] | None = None, posicoes: dict | None = None) -> list[str]:
    """objs: [{"objeto", "min": [x,y,z], "max": [x,y,z], "materiais": [...]}]. Devolve os problemas."""
    posicoes = posicoes or {}
    problems: list[str] = []
    if not objs:
        return ["nenhuma peça criada ainda"]

    def z_hint(name: str, delta: float) -> str:
        p = posicoes.get(name)
        if p and len(p) == 3:
            return f": use mover(nome='{name}', posicao=[{p[0]:.3f}, {p[1]:.3f}, {p[2] + delta:.3f}])"
        return f": mova {abs(delta):.2f} m para {'cima' if delta > 0 else 'baixo'}"

    for o in objs:
        zmin, zmax = o["min"][2], o["max"][2]
        if zmin < -TOL:
            problems.append(f"{o['objeto']} está {-zmin:.2f} m abaixo do chão (z de {zmin:.2f} a {zmax:.2f})"
                            + z_hint(o["objeto"], -zmin))

    # peças apoiadas: as que tocam o chão e tudo que encosta nelas, em cadeia
    grounded = {o["objeto"] for o in objs if o["min"][2] <= TOL}
    changed = True
    while changed:
        changed = False
        for o in objs:
            if o["objeto"] not in grounded and any(_touch(o, g) for g in objs if g["objeto"] in grounded):
                grounded.add(o["objeto"]); changed = True
    for o in objs:
        if o["objeto"] in grounded:
            continue
        below = [b for b in objs if b is not o and _xy_overlap(o, b) and b["max"][2] <= o["min"][2] + TOL]
        msg = f"{o['objeto']} está solto no ar (z de {o['min'][2]:.2f} a {o['max'][2]:.2f}) e não encosta em nada apoiado"
        if below:
            top = max(below, key=lambda b: b["max"][2])
            gap = o["min"][2] - top["max"][2]
            msg += f"; o vão até {top['objeto']} é {gap:.2f} m" + z_hint(o["objeto"], -gap)
        else:
            msg += z_hint(o["objeto"], -o["min"][2])
        problems.append(msg)

    for a in objs:
        for b in objs:
            if a is not b and _inside(a, b) and not _inside(b, a):
                problems.append(f"{a['objeto']} está inteira dentro de {b['objeto']} e não aparece")
                break

    if dims:
        lo = [min(o["min"][i] for o in objs) for i in range(3)]
        hi = [max(o["max"][i] for o in objs) for i in range(3)]
        size = [hi[i] - lo[i] for i in range(3)]
        want_h, got_h = dims[2], size[2]
        if want_h > 0 and not 0.75 <= got_h / want_h <= 1.33:
            problems.append(f"o asset tem {got_h:.2f} m de altura; o plano pede {want_h:.2f} m")
        want_w, got_w = max(dims[0], dims[1]), max(size[0], size[1])
        if want_w > 0 and not 0.7 <= got_w / want_w <= 1.4:
            problems.append(f"o asset tem {got_w:.2f} m na maior medida horizontal; o plano pede {want_w:.2f} m")

    mats = {m for o in objs for m in o.get("materiais", [])}
    if len(objs) >= 4 and len(mats) <= 1:
        problems.append("todas as peças usam o mesmo material/tom; use aplicar_material com cor para diferenciar "
                        "peças (ex.: pernas mais escuras que o assento)")
    return problems[:8]


# Orçamento de triângulos (malha final, com modificadores) por alvo e categoria do plano.
# jogo: PC/console com câmera isométrica (faixas de referência de mercado; mobile ~5x menos).
# completo: render/portfólio; sem teto rígido na indústria, estas faixas mantêm o Blender fluido.
BUDGETS: dict[str, dict[str, tuple[int, int]]] = {
    "jogo": {
        "prop": (500, 5_000), "hard_surface": (1_000, 10_000), "organic": (1_000, 10_000),
        "architecture": (2_000, 20_000), "environment": (1_000, 10_000),
        "vehicle": (10_000, 40_000), "character": (15_000, 40_000),
    },
    "completo": {
        "prop": (5_000, 100_000), "hard_surface": (20_000, 200_000), "organic": (20_000, 300_000),
        "architecture": (50_000, 500_000), "environment": (20_000, 300_000),
        "vehicle": (100_000, 1_000_000), "character": (100_000, 1_000_000),
    },
}


def budget_for(alvo: str, category: str | None) -> tuple[int, int]:
    table = BUDGETS.get(alvo, BUDGETS["jogo"])
    return table.get(category or "prop", table["prop"])


def _n(v: int) -> str:
    return f"{v:,}".replace(",", ".")


def budget_line(alvo: str, category: str | None) -> str:
    lo, hi = budget_for(alvo, category)
    nome = "JOGO (tempo real, Unity)" if alvo == "jogo" else "MODELAGEM COMPLETA (render/portfólio)"
    return (f"Alvo: {nome}. Orçamento para a categoria {category or 'prop'}: {_n(lo)}–{_n(hi)} triângulos na "
            "malha final (com modificadores). Confira com `metricas` (campo tris).")


def budget_check(tris: int | None, alvo: str, category: str | None) -> str | None:
    if not tris:
        return None
    lo, hi = budget_for(alvo, category)
    if tris > hi:
        return (f"{_n(tris)} triângulos: acima do orçamento de {alvo} ({_n(hi)}). Reduza segmentos de bevel e de "
                "cilindros, o nível de SUBSURF ou use DECIMATE nas peças que menos aparecem")
    if tris < lo * 0.5:
        return f"{_n(tris)} triângulos: abaixo do esperado para {alvo} ({_n(lo)}+); o asset deve estar simples ou facetado demais"
    return None
