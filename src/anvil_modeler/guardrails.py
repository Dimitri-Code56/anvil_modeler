"""Validação estática do código gerado antes de rodar no Blender.

O agente executa Python arbitrário no Blender do usuário, então isto
não é opcional: bloqueia IO, imports fora da whitelist e operações
que salvam/fecham/resetam o arquivo ou apagam coisas fora da coleção.
"""
from __future__ import annotations

import ast

ALLOWED_IMPORTS = {"bpy", "bmesh", "mathutils", "math", "random", "itertools", "functools", "collections"}
FORBIDDEN_CALLS = {"exec", "eval", "compile", "open", "__import__", "globals", "breakpoint", "input"}
FORBIDDEN_PREFIXES = (
    "bpy.ops.wm",              # salvar, abrir, sair, resetar
    "bpy.ops.script",
    "bpy.ops.preferences",
    "bpy.ops.object.delete",   # o harness já limpa a coleção do asset
    "bpy.data.objects.remove",
    "bpy.data.collections.remove",
    "bpy.utils.register",
    "bpy.app.handlers",
    "bpy.ops.export",
    "bpy.ops.import",
)
FORBIDDEN_ATTRS = {"__subclasses__", "__globals__", "__builtins__", "__code__", "__dict__"}
MAX_CHARS = 40_000


def _dotted(node: ast.AST) -> str:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def repair_code(code: str) -> tuple[str, list[str]]:
    """Conserta erros previsíveis em vez de só recusar.

    Hoje: remove definições de funções anvil_* (a biblioteca já está carregada;
    modelos pequenos insistem em reescrevê-las).
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code, []
    defs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    notes, drop = [], set()
    for d in defs:
        if d.name.startswith("anvil_"):
            drop.add(d.name); notes.append(f"removida a redefinição de {d.name} (já vem da biblioteca)")
        elif d.name not in used:
            drop.add(d.name); notes.append(f"removida a função {d.name}, que nunca é chamada")
    if not drop:
        return code, []
    tree.body = [n for n in tree.body if not (isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in drop)]
    return ast.unparse(tree), notes


def check_code(code: str, armadilhas: bool = True) -> str | None:
    """Retorna None se o código passou, ou a descrição do problema."""
    if not code.strip():
        return "Código vazio."
    if len(code) > MAX_CHARS:
        return f"Código grande demais ({len(code)} caracteres; limite {MAX_CHARS})."
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"SyntaxError na linha {e.lineno}: {e.msg}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in ALLOWED_IMPORTS:
                    return f"Import não permitido: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] not in ALLOWED_IMPORTS:
                return f"Import não permitido: {node.module}"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                return f"Chamada proibida: {node.func.id}()"
        if isinstance(node, ast.Attribute):
            if node.attr in FORBIDDEN_ATTRS:
                return f"Atributo proibido: {node.attr}"
            name = _dotted(node)
            if any(name == p or name.startswith(p + ".") for p in FORBIDDEN_PREFIXES):
                return f"Operação proibida: {name}"
    if not armadilhas:
        return None
    # armadilhas conhecidas: todas de uma vez, com a correção explicada,
    # para o modelo não consertar uma por tentativa
    problems: list[str] = []
    funcs = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    called = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    top_level_work = [n for n in tree.body if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Import, ast.ImportFrom, ast.ClassDef))
                      and not (isinstance(n, ast.Expr) and isinstance(getattr(n, "value", None), ast.Constant))]
    redefinidas = [f for f in funcs if f.startswith("anvil_")]
    if redefinidas:
        problems.append(f"{', '.join(redefinidas)} já existe na biblioteca carregada antes do script; NÃO redefina, só chame "
                        "(mat = anvil_material('wood', color=(0.5, 0.3, 0.2)); anvil_assign(obj, mat)).")
    if funcs and not (set(funcs) & called):
        problems.append("o script só DEFINE funções (" + ", ".join(funcs[:5]) + ") e nunca as chama; chame a função principal "
                        "no nível de cima (fora de if __name__) e termine com result = {...}.")
    for n in tree.body:
        if isinstance(n, ast.If) and "__name__" in ast.dump(n.test):
            problems.append("código dentro de if __name__ == '__main__' não roda no Blender; chame as funções no nível de cima.")
            break
    if not top_level_work:
        problems.append("o script não executa nada no nível de cima; chame as funções que criam os objetos.")
    bm_vars = {tg.id for n in ast.walk(tree) if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)
               and _dotted(n.value.func) == "bmesh.new" for tg in n.targets if isinstance(tg, ast.Name)}
    seen = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            name = _dotted(node)
            if name in seen:
                continue
            if name == "bmesh.from_edit_mesh" or name == "bmesh.update_edit_mesh":
                seen.add(name)
                problems.append(f"{name} exige modo de edição e falha aqui; use bm = bmesh.new(); bm.from_mesh(obj.data); "
                                "...; bm.to_mesh(obj.data); bm.free().")
            elif name.startswith("bpy.ops.mesh.") and not name.startswith("bpy.ops.mesh.primitive_"):
                seen.add(name)
                problems.append(f"{name} é operador de edição de malha (exige modo de edição); use bmesh.ops.* "
                                "(ex.: bmesh.ops.extrude_face_region) ou modificadores.")
            elif node.attr == "from_pydata" and isinstance(node.value, ast.Name) and node.value.id in bm_vars:
                seen.add(name)
                problems.append(f"{node.value.id} é um BMesh, e BMesh não tem from_pydata (isso é de Mesh); use "
                                "me = bpy.data.meshes.new('n'); me.from_pydata(verts, [], faces), ou bm.verts.new / bm.faces.new.")
        elif isinstance(node, ast.Call) and _dotted(node.func).startswith("bpy.ops.mesh.primitive_"):
            for kw in node.keywords:
                if kw.arg == "size" and isinstance(kw.value, (ast.Tuple, ast.List)):
                    problems.append("primitive_*_add(size=...) aceita UM número; crie com size=1 e depois "
                                    "obj.scale = (x, y, z), ou passe scale=(x, y, z) no operador.")
                    break
    if problems:
        return "Armadilhas encontradas (corrija TODAS):\n" + "\n".join(f"{k}. {p}" for k, p in enumerate(problems, 1))
    return None
