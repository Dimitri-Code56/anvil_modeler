"""Geradores de código bpy das ferramentas do anvil-tools.

Cada função recebe parâmetros simples (medidas em metros, listas de pontos) e devolve um trecho
de Python para rodar no Blender, já testado. Os parâmetros entram no código como JSON (dados),
nunca como código: o modelo não consegue injetar instruções por aqui.

Convenções: Z para cima, a frente do objeto olha para -Y, chão em z = 0, medidas em metros.
Os trechos assumem que a biblioteca de materiais (blender_lib.prelude) foi colada antes.
"""
from __future__ import annotations

import json
import re

NAME_RE = re.compile(r"^[A-Za-z0-9_\-]{1,60}$")


def nome_valido(nome: str) -> str:
    if not NAME_RE.match(str(nome)):
        raise ValueError(f"Nome inválido: {nome!r}. Use só letras, números, _ ou - (até 60).")
    return str(nome)


def _p(**params) -> str:
    return "import json\nP = json.loads(" + repr(json.dumps(params)) + ")\n"


COMMON = """
import bpy, bmesh, math
from mathutils import Vector, Matrix, Euler
C = bpy.data.collections.get(P["colecao"])
if C is None:
    raise RuntimeError("Asset não iniciado: chame iniciar_asset primeiro.")

def _link(name, data):
    old = bpy.data.objects.get(name)
    if old is not None:
        if C not in old.users_collection:
            raise RuntimeError("Já existe um objeto chamado " + name + " fora deste asset. Use outro nome.")
        bpy.data.objects.remove(old, do_unlink=True)
    ob = bpy.data.objects.new(name, data)
    C.objects.link(ob)
    return ob

def _get(name):
    ob = bpy.data.objects.get(name)
    if ob is None or C not in ob.users_collection:
        nomes = [o.name for o in C.objects if not o.hide_render]
        raise RuntimeError("Objeto " + str(name) + " não existe neste asset. Objetos: " + ", ".join(nomes[:30]))
    return ob

def _bbox(ob):
    cs = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return [min(c[i] for c in cs) for i in range(3)], [max(c[i] for c in cs) for i in range(3)]

def _info(ob):
    bpy.context.view_layer.update()
    d = ob.dimensions
    lo, hi = _bbox(ob)
    return {"objeto": ob.name, "dimensoes_m": [round(d.x, 3), round(d.y, 3), round(d.z, 3)],
            "posicao": [round(v, 3) for v in ob.matrix_world.translation],
            "z_de_ate": [round(lo[2], 3), round(hi[2], 3)]}

def _mat(ob, material, cor):
    if material:
        nm = "ANVIL_" + material + ("" if not cor else "_" + "_".join(str(round(c, 2)) for c in cor[:3]))
        anvil_assign(ob, anvil_material(material, color=cor, name=nm))

def _finish(ob, chanfro, material, cor, angulo=None):
    if chanfro and chanfro > 0:
        m = ob.modifiers.new("Chanfro", "BEVEL"); m.width = chanfro; m.segments = 2; m.limit_method = "ANGLE"
        for f in ob.data.polygons: f.use_smooth = True
        ob.modifiers.new("Normais", "WEIGHTED_NORMAL").keep_sharp = True
    elif angulo is not None and hasattr(ob.data, "polygons"):
        for f in ob.data.polygons: f.use_smooth = True
        if hasattr(ob.data, "set_sharpness_by_angle"):
            ob.data.set_sharpness_by_angle(angle=math.radians(angulo))
    _mat(ob, material, cor)
    return _info(ob)

def _place(ob, posicao, rot):
    ob.location = posicao
    ob.rotation_euler = [math.radians(a) for a in rot]
"""

_PLANES = """
AX = {"XZ": 1, "XY": 2, "YZ": 0}[P["plano"]]
def to3(u, v, w):
    if AX == 1: return (u, w, v)
    if AX == 2: return (u, v, w)
    return (w, u, v)
"""


def perfil_extrudado(colecao, nome, pontos, espessura, plano="XZ", posicao=(0, 0, 0),
                     rotacao_graus=(0, 0, 0), chanfro=0.005, material=None, cor=None) -> str:
    nome_valido(nome)
    if len(pontos) < 3:
        raise ValueError("O perfil precisa de pelo menos 3 pontos [u, v].")
    if plano not in ("XZ", "XY", "YZ"):
        raise ValueError("plano deve ser XZ (vista de frente), XY (vista de cima) ou YZ (vista de lado).")
    return _p(colecao=colecao, nome=nome, pontos=[list(map(float, p[:2])) for p in pontos], espessura=float(espessura),
              plano=plano, posicao=list(posicao), rot=list(rotacao_graus), chanfro=chanfro, material=material, cor=cor) \
        + COMMON + _PLANES + """
bm = bmesh.new()
h = P["espessura"] / 2
vs = [bm.verts.new(to3(u, v, -h)) for u, v in P["pontos"]]
face = bm.faces.new(vs)
r = bmesh.ops.extrude_face_region(bm, geom=[face])
nv = [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]
bmesh.ops.translate(bm, vec=to3(0, 0, P["espessura"]), verts=nv)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new(P["nome"]); bm.to_mesh(me); bm.free()
ob = _link(P["nome"], me)
_place(ob, P["posicao"], P["rot"])
result = _finish(ob, P["chanfro"], P["material"], P["cor"])
"""


def caixa(colecao, nome, tamanho, posicao=(0, 0, 0), rotacao_graus=(0, 0, 0), chanfro=0.005,
          material=None, cor=None) -> str:
    nome_valido(nome)
    return _p(colecao=colecao, nome=nome, tamanho=list(map(float, tamanho)), posicao=list(posicao),
              rot=list(rotacao_graus), chanfro=chanfro, material=material, cor=cor) + COMMON + """
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Diagonal((*P["tamanho"], 1.0)))
me = bpy.data.meshes.new(P["nome"]); bm.to_mesh(me); bm.free()
ob = _link(P["nome"], me)
_place(ob, P["posicao"], P["rot"])
result = _finish(ob, P["chanfro"], P["material"], P["cor"])
"""


def cilindro(colecao, nome, raio, altura, posicao=(0, 0, 0), eixo="Z", raio_topo=None, segmentos=32,
             rotacao_graus=(0, 0, 0), chanfro=0.003, material=None, cor=None) -> str:
    nome_valido(nome)
    if eixo not in ("X", "Y", "Z"):
        raise ValueError("eixo deve ser X, Y ou Z.")
    return _p(colecao=colecao, nome=nome, raio=float(raio), altura=float(altura), posicao=list(posicao), eixo=eixo,
              raio_topo=None if raio_topo is None else float(raio_topo), segmentos=max(8, int(segmentos)),
              rot=list(rotacao_graus), chanfro=chanfro, material=material, cor=cor) + COMMON + """
bm = bmesh.new()
rt = P["raio"] if P["raio_topo"] is None else P["raio_topo"]
R = {"Z": Matrix.Identity(4), "X": Matrix.Rotation(math.radians(90), 4, "Y"), "Y": Matrix.Rotation(math.radians(90), 4, "X")}[P["eixo"]]
bmesh.ops.create_cone(bm, cap_ends=True, segments=P["segmentos"], radius1=P["raio"], radius2=rt, depth=P["altura"], matrix=R)
me = bpy.data.meshes.new(P["nome"]); bm.to_mesh(me); bm.free()
ob = _link(P["nome"], me)
_place(ob, P["posicao"], P["rot"])
result = _finish(ob, P["chanfro"], P["material"], P["cor"], angulo=40)
"""


def revolucao(colecao, nome, perfil, posicao=(0, 0, 0), segmentos=24, rotacao_graus=(0, 0, 0),
              material=None, cor=None) -> str:
    nome_valido(nome)
    if len(perfil) < 2:
        raise ValueError("O perfil de revolução precisa de pelo menos 2 pontos [raio, altura].")
    return _p(colecao=colecao, nome=nome, perfil=[[max(0.0, float(r)), float(z)] for r, z in (p[:2] for p in perfil)],
              posicao=list(posicao), segmentos=max(8, int(segmentos)), rot=list(rotacao_graus),
              material=material, cor=cor) + COMMON + """
prof = P["perfil"]
if prof[0][0] > 0: prof = [[0.0, prof[0][1]]] + prof
if prof[-1][0] > 0: prof = prof + [[0.0, prof[-1][1]]]
bm = bmesh.new()
vs = [bm.verts.new((r, 0.0, z)) for r, z in prof]
es = [bm.edges.new((vs[k], vs[k + 1])) for k in range(len(vs) - 1)]
bmesh.ops.spin(bm, geom=vs + es, axis=(0, 0, 1), cent=(0, 0, 0), angle=2 * math.pi, steps=P["segmentos"], use_merge=True)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new(P["nome"]); bm.to_mesh(me); bm.free()
ob = _link(P["nome"], me)
_place(ob, P["posicao"], P["rot"])
result = _finish(ob, 0, P["material"], P["cor"], angulo=35)
"""


def tubo_por_curva(colecao, nome, pontos, raio, suave=True, material=None, cor=None) -> str:
    nome_valido(nome)
    if len(pontos) < 2:
        raise ValueError("A curva precisa de pelo menos 2 pontos [x, y, z].")
    return _p(colecao=colecao, nome=nome, pontos=[list(map(float, p[:3])) for p in pontos], raio=float(raio),
              suave=bool(suave), material=material, cor=cor) + COMMON + """
cu = bpy.data.curves.new(P["nome"], "CURVE")
cu.dimensions = "3D"; cu.bevel_depth = P["raio"]; cu.bevel_resolution = 4; cu.use_fill_caps = True
pts = P["pontos"]
if P["suave"]:
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(len(pts) - 1)
    for bp, co in zip(sp.bezier_points, pts):
        bp.co = co; bp.handle_left_type = bp.handle_right_type = "AUTO"
else:
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, co in zip(sp.points, pts):
        p.co = (*co, 1.0)
ob = _link(P["nome"], cu)
_mat(ob, P["material"], P["cor"])
result = _info(ob)
"""


def cortar(colecao, alvo, forma, tamanho=None, raio=None, altura=None, posicao=(0, 0, 0),
           rotacao_graus=(0, 0, 0), eixo="Z") -> str:
    nome_valido(alvo)
    if forma not in ("caixa", "cilindro"):
        raise ValueError("forma deve ser caixa ou cilindro.")
    return _p(colecao=colecao, alvo=alvo, forma=forma, tamanho=tamanho, raio=raio, altura=altura,
              posicao=list(posicao), rot=list(rotacao_graus), eixo=eixo) + COMMON + """
alvo = _get(P["alvo"])
bm = bmesh.new()
if P["forma"] == "caixa":
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Diagonal((*P["tamanho"], 1.0)))
else:
    R = {"Z": Matrix.Identity(4), "X": Matrix.Rotation(math.radians(90), 4, "Y"), "Y": Matrix.Rotation(math.radians(90), 4, "X")}[P["eixo"]]
    bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=P["raio"], radius2=P["raio"], depth=P["altura"], matrix=R)
k = len([o for o in C.objects if o.name.startswith(alvo.name + "_corte")])
me = bpy.data.meshes.new(alvo.name + "_corte"); bm.to_mesh(me); bm.free()
cut = _link(alvo.name + "_corte" + str(k), me)
_place(cut, P["posicao"], P["rot"])
cut.hide_render = True; cut.display_type = "WIRE"
b = alvo.modifiers.new("Corte" + str(k), "BOOLEAN"); b.operation = "DIFFERENCE"; b.object = cut; b.solver = "EXACT"
if hasattr(alvo.modifiers, "move"):
    alvo.modifiers.move(len(alvo.modifiers) - 1, 0)
result = _info(alvo)
"""


def espelhar(colecao, nome, eixo="X", novo_nome=None) -> str:
    nome_valido(nome)
    novo = nome_valido(novo_nome or (nome + "_espelho"))
    return _p(colecao=colecao, nome=nome, eixo=eixo, novo=novo) + COMMON + """
src = _get(P["nome"])
i = {"X": 0, "Y": 1, "Z": 2}[P["eixo"]]
ob = src.copy(); ob.data = src.data.copy(); ob.name = P["novo"]
old = bpy.data.objects.get(P["novo"])
if old is not None and old != ob and C in old.users_collection:
    bpy.data.objects.remove(old, do_unlink=True); ob.name = P["novo"]
C.objects.link(ob)
loc = list(ob.location); loc[i] = -loc[i]; ob.location = loc
sc = list(ob.scale); sc[i] = -sc[i]; ob.scale = sc
result = _info(ob)
"""


def repetir(colecao, nome, quantidade, deslocamento) -> str:
    nome_valido(nome)
    return _p(colecao=colecao, nome=nome, quantidade=max(2, int(quantidade)), desloc=list(map(float, deslocamento))) + COMMON + """
ob = _get(P["nome"])
a = ob.modifiers.new("Repetir", "ARRAY"); a.count = P["quantidade"]
a.use_relative_offset = False; a.use_constant_offset = True; a.constant_offset_displace = P["desloc"]
if hasattr(ob.modifiers, "move"):
    ob.modifiers.move(len(ob.modifiers) - 1, 0)
result = _info(ob)
"""


def aplicar_material(colecao, nome, material, cor=None) -> str:
    nome_valido(nome)
    return _p(colecao=colecao, nome=nome, material=material, cor=cor) + COMMON + """
ob = _get(P["nome"])
ob.data.materials.clear()
_mat(ob, P["material"], P["cor"])
result = {"objeto": ob.name, "material": P["material"]}
"""


def suavizar(colecao, nome, nivel=2) -> str:
    nome_valido(nome)
    return _p(colecao=colecao, nome=nome, nivel=max(1, min(3, int(nivel)))) + COMMON + """
ob = _get(P["nome"])
s = ob.modifiers.new("Suavizar", "SUBSURF"); s.levels = P["nivel"]; s.render_levels = P["nivel"]
if hasattr(ob.data, "polygons"):
    for f in ob.data.polygons: f.use_smooth = True
result = _info(ob)
"""


def remover(colecao, nome) -> str:
    nome_valido(nome)
    return _p(colecao=colecao, nome=nome) + COMMON + """
ob = _get(P["nome"])
bpy.data.objects.remove(ob, do_unlink=True)
result = {"removido": P["nome"]}
"""


def listar_objetos(colecao) -> str:
    return _p(colecao=colecao) + COMMON + """
bpy.context.view_layer.update()
itens = []
for o in C.all_objects:
    if o.hide_render: continue
    d = o.dimensions
    itens.append({"objeto": o.name, "tipo": o.type, "posicao": [round(v, 3) for v in o.matrix_world.translation],
                  "dimensoes_m": [round(d.x, 3), round(d.y, 3), round(d.z, 3)],
                  "materiais": [m.name for m in getattr(o.data, "materials", []) if m]})
result = {"objetos": itens}
"""


def massa_organica(colecao, nome, partes, detalhe=None, suavidade=10, textura=0.0, material=None, cor=None) -> str:
    """Formas orgânicas: elipsoides sobrepostos fundidos numa superfície contínua (remesh + suavização)."""
    nome_valido(nome)
    if not partes:
        raise ValueError("Passe ao menos uma parte: {centro: [x,y,z], raios: [rx,ry,rz], rotacao_graus: [..]}.")
    norm = []
    for pt in partes:
        c = list(map(float, pt.get("centro", [0, 0, 0])))[:3]
        r = list(map(float, pt.get("raios", [0.05, 0.05, 0.05])))[:3]
        g = list(map(float, pt.get("rotacao_graus", [0, 0, 0])))[:3]
        norm.append({"c": c, "r": r, "g": g})
    return _p(colecao=colecao, nome=nome, partes=norm, detalhe=detalhe, suav=max(0, int(suavidade)),
              textura=float(textura), material=material, cor=cor) + COMMON + """
bm = bmesh.new()
lo = [1e9] * 3; hi = [-1e9] * 3
for pt in P["partes"]:
    M = Matrix.Translation(pt["c"]) @ Euler([math.radians(a) for a in pt["g"]]).to_matrix().to_4x4() @ Matrix.Diagonal((*pt["r"], 1.0))
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=1.0, matrix=M)
    for i in range(3):
        lo[i] = min(lo[i], pt["c"][i] - max(pt["r"])); hi[i] = max(hi[i], pt["c"][i] + max(pt["r"]))
me = bpy.data.meshes.new(P["nome"]); bm.to_mesh(me); bm.free()
ob = _link(P["nome"], me)
size = max(hi[i] - lo[i] for i in range(3))
voxel = P["detalhe"] or max(0.0015, size / 90.0)
r = ob.modifiers.new("Fundir", "REMESH"); r.mode = "VOXEL"; r.voxel_size = voxel; r.use_smooth_shade = True
if P["suav"] > 0:
    s = ob.modifiers.new("Suavizar", "SMOOTH"); s.factor = 0.9; s.iterations = P["suav"]
if P["textura"] > 0:
    tx = bpy.data.textures.get("ANVIL_textura_organica") or bpy.data.textures.new("ANVIL_textura_organica", "CLOUDS")
    tx.noise_scale = max(0.002, size / 80.0)
    d = ob.modifiers.new("Textura", "DISPLACE"); d.texture = tx; d.strength = P["textura"]; d.mid_level = 0.5
_mat(ob, P["material"], P["cor"])
result = _info(ob)
"""


def mover(colecao, nome, posicao, rotacao_graus=None) -> str:
    nome_valido(nome)
    return _p(colecao=colecao, nome=nome, posicao=posicao, rot=rotacao_graus) + COMMON + """
ob = _get(P["nome"])
ob.location = P["posicao"]
if P["rot"] is not None:
    ob.rotation_euler = [math.radians(a) for a in P["rot"]]
result = _info(ob)
"""


def caixas_mundo(colecao) -> str:
    """Caixa envolvente de cada peça no mundo (com modificadores), para a conferência de geometria."""
    return _p(colecao=colecao) + COMMON + """
bpy.context.view_layer.update()
itens = []
for o in C.all_objects:
    if o.hide_render or o.type not in {"MESH", "CURVE"}:
        continue
    lo, hi = _bbox(o)
    itens.append({"objeto": o.name, "min": [round(v, 4) for v in lo], "max": [round(v, 4) for v in hi],
                  "materiais": [m.name for m in getattr(o.data, "materials", []) if m]})
result = {"objetos": itens}
"""
