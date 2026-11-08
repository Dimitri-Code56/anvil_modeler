"""Cliente do MCP do Blender + snippets de cena usados pelo harness.

Mantém UMA sessão MCP aberta durante a execução do grafo (stdio),
em vez de abrir um processo novo a cada chamada de ferramenta.
"""
from __future__ import annotations

import json
import re
from contextlib import AsyncExitStack
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from .blender_lib import STUDIO_LIB


def to_blender_path(path: str) -> str:
    """No WSL, o Blender (Windows) precisa do caminho no formato do Windows."""
    import shutil
    import subprocess
    if shutil.which("wslpath"):
        try:
            return subprocess.check_output(["wslpath", "-w", path], text=True).strip()
        except Exception:
            pass
    return path


def collection_name(asset_name: str) -> str:
    return "ANVIL_" + re.sub(r"[^A-Za-z0-9_]", "_", asset_name)[:40]


def _to_text(result: Any) -> str:
    if isinstance(result, tuple):
        result = result[0]
    if isinstance(result, str):
        return result
    if isinstance(result, list):
        parts = []
        for item in result:
            if isinstance(item, dict):
                parts.append(item.get("text") or json.dumps(item, ensure_ascii=False))
            else:
                parts.append(getattr(item, "text", str(item)))
        return "\n".join(parts)
    return str(result)


def extract_json(text: str) -> dict | None:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


# Gira o veio da madeira para o eixo mais comprido de cada peça (perna: vertical; assento: na largura).
# O material é compartilhado, então criamos uma variante por eixo (ANVIL_wood__veioX/Y/Z).
WOOD_ALIGN = """
import bpy
_C = bpy.data.collections.get({coll!r})
for _o in (list(_C.all_objects) if _C else []):
    if _o.type != "MESH" or _o.hide_render:
        continue
    _d = _o.dimensions
    _ax = max(range(3), key=lambda i: _d[i])
    for _s in _o.material_slots:
        _m = _s.material
        if not _m or not _m.node_tree:
            continue
        _mp = next((n for n in _m.node_tree.nodes if n.label == "ANVIL_GRAIN"), None)
        if _mp is None:
            continue
        _want = [1.0, 1.0, 1.0]; _want[_ax] = 0.06
        if [round(v, 3) for v in _mp.inputs["Scale"].default_value] == _want:
            continue
        _nm = _m.name.split("__veio")[0] + "__veio" + "XYZ"[_ax]
        _m2 = bpy.data.materials.get(_nm)
        if _m2 is None:
            _m2 = _m.copy(); _m2.name = _nm
            next(n for n in _m2.node_tree.nodes if n.label == "ANVIL_GRAIN").inputs["Scale"].default_value = _want
        _s.material = _m2
"""


class BlenderClient:
    def __init__(self, servers: dict, server_name: str = "blender"):
        self._client = MultiServerMCPClient(servers)
        self._server_name = server_name
        self._stack = AsyncExitStack()
        self._tools: dict[str, Any] = {}

    async def __aenter__(self) -> "BlenderClient":
        session = await self._stack.enter_async_context(self._client.session(self._server_name))
        tools = await load_mcp_tools(session)
        self._tools = {t.name: t for t in tools}
        return self

    async def __aexit__(self, *exc) -> None:
        await self._stack.aclose()

    @property
    def tool_names(self) -> list[str]:
        return sorted(self._tools)

    async def call(self, name: str, **kwargs) -> str:
        tool = self._tools.get(name) or next(
            (t for k, t in self._tools.items() if k.endswith(name)), None
        )
        if tool is None:
            raise KeyError(f"Ferramenta '{name}' não encontrada. Disponíveis: {self.tool_names}")
        return _to_text(await tool.ainvoke(kwargs))

    # --- atalhos -----------------------------------------------------------
    async def execute(self, code: str) -> str:
        out = await self.call("execute_blender_code", code=code)
        _d = extract_json(out)
        if isinstance(_d, dict) and _d.get("status") == "error":
            raise RuntimeError(str(_d.get("message", out))[-3000:])
        if "Traceback (most recent call last)" in out or re.search(r"\b\w*Error:", out):
            raise RuntimeError(out[-3000:])
        return out

    async def search_docs(self, query: str, max_results: int = 2) -> str:
        return await self.call("search_api_docs", query=query, max_results=max_results, context=1)

    async def prepare_scene(self, asset_name: str) -> None:
        await self.execute(PREP_SCENE.format(coll=collection_name(asset_name)))

    async def render(self, asset_name: str, output_path: str, res: int) -> str:
        # Renderiza via código: a ferramenta render_viewport_to_path do MCP ignora a
        # pasta pedida e salva numa pasta temporária, então gravamos o arquivo nós mesmos.
        await self.execute(
            WOOD_ALIGN.format(coll=collection_name(asset_name))
            + STUDIO_LIB
            + STAGE_SCENE.format(coll=collection_name(asset_name), res=res)
            + RENDER_TO.format(path=to_blender_path(output_path), coll=collection_name(asset_name))
        )
        return output_path

    async def introspect(self, items: list[dict]) -> dict:
        """Confere no Blender aberto se cada item da API existe nesta versão e devolve os nomes reais."""
        safe = [
            {"kind": str(i.get("kind", "")), "name": str(i.get("name", ""))}
            for i in items if re.fullmatch(r"[A-Za-z0-9_.]{1,80}", str(i.get("name", "")))
        ][:30]
        code = "import json\nITEMS = json.loads(" + repr(json.dumps(safe)) + ")\n" + INTROSPECT
        d = extract_json(await self.execute(code)) or {}
        while isinstance(d, dict) and "items" not in d and isinstance(d.get("result"), dict):
            d = d["result"]
        return d

    async def metrics(self, asset_name: str) -> dict:
        out = await self.execute(METRICS.format(coll=collection_name(asset_name)))
        d = extract_json(out) or {"raw": out[:500]}
        while isinstance(d, dict) and "objects" not in d and isinstance(d.get("result"), dict):
            d = d["result"]
        return d


# ---------------------------------------------------------------------------
# Snippets executados no Blender. Tudo do asset vive numa coleção própria,
# que é limpa antes de cada tentativa — o resto da cena não é tocado.
# ---------------------------------------------------------------------------

PREP_SCENE = '''
import bpy
name = {coll!r}
coll = bpy.data.collections.get(name)
if coll is None:
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
for ob in list(coll.all_objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for me in list(bpy.data.meshes):
    if me.users == 0:
        bpy.data.meshes.remove(me)
lc = bpy.context.view_layer.layer_collection.children[name]
bpy.context.view_layer.active_layer_collection = lc
result = {{"ok": True}}
'''

STAGE_SCENE = '''
import bpy, math
from mathutils import Vector
asset = bpy.data.collections.get({coll!r})
kinds = {{"MESH", "CURVE", "SURFACE", "META", "FONT"}}
objs = [o for o in asset.all_objects if o.type in kinds] if asset else []
if not objs:
    raise RuntimeError("O script rodou mas não criou nenhum objeto visível (malha). Crie objetos do tipo MESH com dados de malha (bmesh ou primitivas) e ligue-os com bpy.context.collection.objects.link(obj).")
pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center = (mn + mx) / 2
radius = max((mx - mn).length / 2, 0.01)
stage = bpy.data.collections.get("ANVIL_STAGE")
if stage is None:
    stage = bpy.data.collections.new("ANVIL_STAGE")
    bpy.context.scene.collection.children.link(stage)
cam = bpy.data.objects.get("ANVIL_CAM")
if cam is None:
    cam = bpy.data.objects.new("ANVIL_CAM", bpy.data.cameras.new("ANVIL_CAM"))
    stage.objects.link(cam)
cam.data.lens = 50
# vista 3/4 mais baixa (câmera de "fotógrafo"), enquadramento justo
dist = radius / math.sin(cam.data.angle / 2) * 0.95
direction = Vector((0.85, -1.4, 0.42)).normalized()
cam.location = center + direction * dist
cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.clip_end = dist * 10
# chão neutro sob o asset: sombra de contato, sem horizonte cortando o quadro
ground = bpy.data.objects.get("ANVIL_GROUND")
if ground is None:
    gme = bpy.data.meshes.new("ANVIL_GROUND")
    gme.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [], [(0, 1, 2, 3)])
    ground = bpy.data.objects.new("ANVIL_GROUND", gme)
    stage.objects.link(ground)
    gmat = bpy.data.materials.get("ANVIL_GROUND_MAT") or bpy.data.materials.new("ANVIL_GROUND_MAT")
    gmat.use_nodes = True
    bsdf = next((n for n in gmat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.30, 0.30, 0.29, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.9
    gme.materials.append(gmat)
ground.location = (center.x, center.y, mn.z)
ground.scale = (radius * 40, radius * 40, 1)
scene = bpy.context.scene
anvil_studio(scene, stage_collection=stage)   # céu em degradê + sol nítido (STUDIO_LIB)
scene.camera = cam
scene.render.resolution_x = scene.render.resolution_y = {res}
scene.render.resolution_percentage = 100
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        scene.render.engine = eng
        break
    except TypeError:
        pass
result = {{"ok": True}}
'''

RENDER_TO = '''
import bpy, os
scene = bpy.context.scene
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = {path!r}
# só o asset e o estúdio aparecem no render; o resto da cena é escondido e depois restaurado
keep = set()
for name in ({coll!r}, "ANVIL_STAGE"):
    c = bpy.data.collections.get(name)
    if c:
        keep |= {{o.name for o in c.all_objects}}
hidden = [o for o in scene.objects if o.name not in keep and not o.hide_render]
for o in hidden:
    o.hide_render = True
try:
    bpy.ops.render.render(write_still=True)
finally:
    for o in hidden:
        o.hide_render = False
if not os.path.exists({path!r}):
    raise RuntimeError("Render não gerou o arquivo: " + {path!r})
result = {{"render": {path!r}, "hidden_during_render": len(hidden)}}
'''

METRICS = '''
import bpy, bmesh
asset = bpy.data.collections.get({coll!r})
# ignora cortadores e auxiliares escondidos no render (booleanas)
objs = [o for o in asset.all_objects if o.type == "MESH" and not o.hide_render] if asset else []
deps = bpy.context.evaluated_depsgraph_get()
verts = faces = tris = nonmanifold = raw_boxes = mods = 0
for o in objs:
    mods += len(o.modifiers)
    ev = o.evaluated_get(deps)
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    verts += len(bm.verts)
    faces += len(bm.faces)
    tris += sum(len(f.verts) - 2 for f in bm.faces)
    nonmanifold += sum(1 for e in bm.edges if not e.is_manifold)
    if len(bm.faces) <= 6:
        raw_boxes += 1
    bm.free()
    ev.to_mesh_clear()
mats = {{s.material.name for o in objs for s in o.material_slots if s.material}}
result = {{
    "objects": len(objs), "verts": verts, "faces": faces, "tris": tris,
    "nonmanifold_edges": nonmanifold, "raw_boxes": raw_boxes,
    "modifiers": mods, "materials": len(mats),
}}
'''


# Depois do script do modelo: objetos novos criados fora da coleção do asset (ex.: ligados direto
# na cena) são movidos para ela. Modelos pequenos erram isso com frequência.
ADOPT = """

# --- harness: adota objetos criados fora da coleção do asset ---
_anvil_c = bpy.data.collections.get({coll!r})
if _anvil_c is not None:
    for _o in list(bpy.data.objects):
        if _o.name not in __anvil_before and _anvil_c not in _o.users_collection:
            for _uc in list(_o.users_collection):
                _uc.objects.unlink(_o)
            _anvil_c.objects.link(_o)
"""

# Introspecção ao vivo: só getattr/enum do RNA, nunca eval dos nomes que vêm do modelo.
INTROSPECT = '''
import bpy, bmesh, difflib
def _close(name, pool):
    return difflib.get_close_matches(name, list(pool), n=3, cutoff=0.5)
MOD_TYPES = [e.identifier for e in bpy.types.Modifier.bl_rna.properties["type"].enum_items]
NODE_IDS = [n for n in dir(bpy.types) if n.startswith(("ShaderNode", "GeometryNode", "FunctionNode"))]
SKIP = {"rna_type", "name", "show_viewport", "show_render", "show_in_editmode", "show_on_cage",
        "show_expanded", "is_override_data", "use_apply_on_spline", "persistent_uid", "use_pin_to_last",
        "is_active"}
NODE_SKIP = SKIP | {"label", "location", "location_absolute", "width", "height", "color", "select",
        "show_options", "show_preview", "hide", "mute", "show_texture", "use_custom_color", "parent",
        "width_hidden", "warning_propagation", "dimensions", "internal_links"}
def _props(rna, skip=SKIP):
    return [p.identifier for p in rna.properties if p.identifier not in skip and not p.is_readonly
            and not p.identifier.startswith("bl_")][:25]
def _subclasses_with(tp, prop):
    found = []
    for n in dir(bpy.types):
        c = getattr(bpy.types, n, None)
        try:
            if c is not tp and isinstance(c, type) and issubclass(c, tp) and c.bl_rna.properties.get(prop) is not None:
                found.append(n)
        except Exception:
            pass
    return found[:5]
me = bpy.data.meshes.new("_anvil_probe"); ob = bpy.data.objects.new("_anvil_probe", me)
mat = bpy.data.materials.new("_anvil_probe"); mat.use_nodes = True
out = {"blender": bpy.app.version_string, "items": []}
try:
    for it in ITEMS:
        kind, name = it["kind"], it["name"]
        r = {"kind": kind, "name": name, "ok": False}
        try:
            if kind == "modifier":
                if name.upper() in MOD_TYPES:
                    m = ob.modifiers.new("p", name.upper())
                    r.update(ok=True, props=_props(m.bl_rna)); ob.modifiers.remove(m)
                else:
                    r["suggest"] = _close(name.upper(), MOD_TYPES)
            elif kind == "shader_node":
                if name in NODE_IDS and name.startswith("ShaderNode"):
                    n = mat.node_tree.nodes.new(name)
                    r.update(ok=True, inputs=[s.name for s in n.inputs], outputs=[s.name for s in n.outputs], props=_props(n.bl_rna, NODE_SKIP))
                    mat.node_tree.nodes.remove(n)
                else:
                    r["suggest"] = _close(name, NODE_IDS)
            elif kind == "operator":
                grp_name, _, op = name.replace("bpy.ops.", "").partition(".")
                grp = getattr(bpy.ops, grp_name, None)
                if grp is not None and op in dir(grp):
                    rna = getattr(grp, op).get_rna_type()
                    r.update(ok=True, params=[p.identifier for p in rna.properties if p.identifier != "rna_type"][:30])
                else:
                    r["suggest"] = _close(op, dir(grp)) if grp is not None else _close(grp_name, dir(bpy.ops))
            elif kind == "bmesh_op":
                nm = name.replace("bmesh.ops.", "")
                if hasattr(bmesh.ops, nm):
                    r.update(ok=True, doc=(getattr(bmesh.ops, nm).__doc__ or "")[:500])
                else:
                    r["suggest"] = _close(nm, dir(bmesh.ops))
            elif kind in ("enum", "property"):
                cls, _, prop = name.partition(".")
                tp = getattr(bpy.types, cls, None)
                p = tp.bl_rna.properties.get(prop) if tp is not None else None
                if p is None:
                    subs = _subclasses_with(tp, prop) if tp is not None else []
                    if subs:
                        r["error"] = "existe nas subclasses: " + ", ".join(subs) + " (use o objeto do tipo certo)"
                        r["suggest"] = [s + "." + prop for s in subs]
                    else:
                        r["suggest"] = _close(cls, dir(bpy.types)) if tp is None else _close(prop, [q.identifier for q in tp.bl_rna.properties])
                elif kind == "enum" and p.type == "ENUM":
                    vals = [e.identifier for e in p.enum_items]
                    if cls == "RenderSettings" and prop == "engine":
                        vals = sorted(set(vals) | {getattr(c, "bl_idname", None) for c in bpy.types.RenderEngine.__subclasses__()} - {None} | {"BLENDER_WORKBENCH"})
                    r.update(ok=True, values=vals)
                    if len(vals) <= 1:
                        r["note"] = "enum dinâmico: a lista pode estar incompleta sem contexto"
                else:
                    r.update(ok=True, type=p.type)
            else:
                r["error"] = "tipo desconhecido"
        except Exception as e:
            r["error"] = str(e)[:200]
        out["items"].append(r)
finally:
    bpy.data.objects.remove(ob); bpy.data.meshes.remove(me); bpy.data.materials.remove(mat)
result = out
'''


# Afasta a coleção do asset no eixo X conforme o modo (baseline, skills_only, loop_only, full),
# para as versões ficarem lado a lado na cena. Não afeta o render (a câmera enquadra cada coleção).
OFFSET = '''
import bpy
from mathutils import Vector
c = bpy.data.collections.get({coll!r})
objs = [o for o in c.all_objects if o.parent is None] if c else []
if objs:
    xs = [(o.matrix_world @ Vector(b)).x for o in objs if o.type == "MESH" for b in o.bound_box] or [0.0]
    width = max(xs) - min(xs)
    for o in objs:
        o.location.x += {slot} * max(width, 0.1) * 1.4
result = {{"moved": len(objs)}}
'''
