"""Biblioteca injetada no Blender antes de cada script gerado.

O modelo só chama `anvil_material("car_paint", color=...)`, `anvil_assign(...)`
e `anvil_outline(...)`. Os nós de shader ficam aqui, testados, em vez de
serem reescritos (e errados) pelo modelo a cada tentativa. O estilo muda o
material automaticamente via ANVIL_STYLE.
"""
from __future__ import annotations

MATERIAL_LIB = r'''
import bpy

def _anvil_in(node, *names):
    for n in names:
        if n in node.inputs:
            return node.inputs[n]
    return None

def _anvil_set(node, value, *names):
    s = _anvil_in(node, *names)
    if s is not None:
        s.default_value = value

def _anvil_shade(c, k):
    return tuple(max(0.0, min(1.0, v * k)) for v in c[:3]) + (1.0,)

# preset: (cor base, metallic, roughness, extras)
ANVIL_PRESETS = {
    "car_paint":     ((0.60, 0.05, 0.05), 0.5, 0.25, {"coat": 1.0}),
    "painted_metal": ((0.45, 0.42, 0.35), 0.4, 0.45, {"noise": 0.15}),
    "worn_metal":    ((0.35, 0.33, 0.30), 0.9, 0.55, {"noise": 0.35}),
    "steel":         ((0.55, 0.56, 0.58), 1.0, 0.35, {}),
    "chrome":        ((0.90, 0.90, 0.90), 1.0, 0.05, {}),
    "aluminum":      ((0.80, 0.80, 0.82), 1.0, 0.30, {}),
    "dark_metal":    ((0.08, 0.08, 0.09), 0.9, 0.45, {}),
    "glass":         ((0.90, 0.95, 1.00), 0.0, 0.02, {"transmission": 1.0}),
    "tinted_glass":  ((0.15, 0.20, 0.22), 0.0, 0.05, {"transmission": 0.8}),
    "rubber":        ((0.03, 0.03, 0.03), 0.0, 0.85, {}),
    "plastic":       ((0.20, 0.20, 0.20), 0.0, 0.40, {}),
    "wood":          ((0.35, 0.20, 0.10), 0.0, 0.60, {"wood": True}),
    "brick":         ((0.50, 0.20, 0.12), 0.0, 0.85, {"brick": True}),
    "concrete":      ((0.55, 0.55, 0.52), 0.0, 0.90, {"noise": 0.20}),
    "plaster":       ((0.85, 0.82, 0.75), 0.0, 0.80, {"noise": 0.05}),
    "roof_tile":     ((0.45, 0.15, 0.08), 0.0, 0.70, {"noise": 0.15}),
    "stone":         ((0.45, 0.43, 0.40), 0.0, 0.85, {"noise": 0.30}),
    "fabric":        ((0.30, 0.30, 0.40), 0.0, 0.95, {}),
    "leather":       ((0.25, 0.12, 0.06), 0.0, 0.55, {}),
    "emissive":      ((1.00, 0.60, 0.20), 0.0, 0.50, {"emission": 5.0}),
    "soil":          ((0.30, 0.22, 0.15), 0.0, 0.95, {"noise": 0.30}),
    "foliage":       ((0.12, 0.30, 0.08), 0.0, 0.70, {"noise": 0.25}),
    # superfícies biológicas e tecidos
    "fur_short":     ((0.42, 0.33, 0.25), 0.0, 0.90, {"noise": 0.25, "sheen": 1.0}),
    "skin":          ((0.78, 0.57, 0.45), 0.0, 0.50, {"noise": 0.06, "subsurface": 0.2}),
    "scales":        ((0.30, 0.38, 0.18), 0.0, 0.50, {"scales": True}),
    "denim":         ((0.15, 0.21, 0.34), 0.0, 0.80, {"twill": True, "sheen": 0.3}),
}

def _anvil_ramp(nt, fac_socket, dark, light, pos=(0.35, 0.65)):
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = pos
    ramp.color_ramp.elements[0].color = dark
    ramp.color_ramp.elements[1].color = light
    nt.links.new(fac_socket, ramp.inputs["Fac"])
    return ramp

def _anvil_coords(nt, wall=False):
    """Coordenadas do objeto em METROS (texturas com tamanho real, não esticadas).
    wall=True usa (X+Y, Z): tijolo correto em paredes viradas para X ou para Y."""
    tc = nt.nodes.new("ShaderNodeTexCoord")
    if not wall:
        return tc.outputs["Object"]
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    nt.links.new(sep.outputs["X"], add.inputs[0])
    nt.links.new(sep.outputs["Y"], add.inputs[1])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(add.outputs[0], comb.inputs["X"])
    nt.links.new(sep.outputs["Z"], comb.inputs["Y"])
    return comb.outputs[0]

def _anvil_color_source(nt, base, extra):
    """Socket de cor com textura procedural (ou None se cor lisa)."""
    if extra.get("brick"):
        tex = nt.nodes.new("ShaderNodeTexBrick")
        nt.links.new(_anvil_coords(nt, wall=True), tex.inputs["Vector"])
        _anvil_set(tex, _anvil_shade(base, 1.0), "Color1")
        _anvil_set(tex, _anvil_shade(base, 0.70), "Color2")
        _anvil_set(tex, _anvil_shade(tuple(0.5 + 0.5 * v for v in base), 0.85), "Mortar")
        _anvil_set(tex, 1.0, "Scale")
        _anvil_set(tex, 0.22, "Brick Width")     # tijolo real: 22 x 7,5 cm
        _anvil_set(tex, 0.075, "Row Height")
        _anvil_set(tex, 0.01, "Mortar Size")
        return tex.outputs["Color"]
    if extra.get("wood"):
        # veio de madeira: coordenadas esticadas ao longo do veio (nó ANVIL_GRAIN; o harness
        # gira o veio para o comprimento de cada peça antes do render) + fibras finas + manchas suaves
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.label = "ANVIL_GRAIN"
        nt.links.new(_anvil_coords(nt), mp.inputs["Vector"])
        mp.inputs["Scale"].default_value = (1.0, 1.0, 0.06)     # veio ao longo de Z por padrão
        fib = nt.nodes.new("ShaderNodeTexNoise")               # fibras finas
        nt.links.new(mp.outputs["Vector"], fib.inputs["Vector"])
        _anvil_set(fib, 120.0, "Scale"); _anvil_set(fib, 12.0, "Detail"); _anvil_set(fib, 0.7, "Roughness")
        ring = nt.nodes.new("ShaderNodeTexWave")               # anéis largos e irregulares
        nt.links.new(mp.outputs["Vector"], ring.inputs["Vector"])
        _anvil_set(ring, 3.0, "Scale"); _anvil_set(ring, 12.0, "Distortion"); _anvil_set(ring, 3.0, "Detail")
        _anvil_set(ring, 2.0, "Detail Scale")
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
        nt.links.new(ring.outputs["Fac"], mul.inputs[0]); mul.inputs[1].default_value = 0.35
        add = nt.nodes.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"
        nt.links.new(fib.outputs["Fac"], add.inputs[0]); add.inputs[1].default_value = 0.65
        nt.links.new(mul.outputs[0], add.inputs[2])
        bump = nt.nodes.new("ShaderNodeBump")                  # relevo leve das fibras
        bump.label = "ANVIL_BUMP"
        _anvil_set(bump, 0.12, "Strength"); _anvil_set(bump, 0.0015, "Distance")
        nt.links.new(add.outputs[0], bump.inputs["Height"])
        return _anvil_ramp(nt, add.outputs[0], _anvil_shade(base, 0.55), _anvil_shade(base, 1.15), pos=(0.38, 0.68)).outputs["Color"]
    if extra.get("scales"):
        tex = nt.nodes.new("ShaderNodeTexVoronoi")
        try:
            tex.feature = "DISTANCE_TO_EDGE"
        except Exception:
            pass
        nt.links.new(_anvil_coords(nt), tex.inputs["Vector"])
        _anvil_set(tex, 60.0, "Scale")
        return _anvil_ramp(nt, tex.outputs["Distance"], _anvil_shade(base, 0.35), _anvil_shade(base, 1.1), pos=(0.0, 0.12)).outputs["Color"]
    if extra.get("twill"):
        tex = nt.nodes.new("ShaderNodeTexWave")
        try:
            tex.bands_direction = "DIAGONAL"
        except Exception:
            pass
        nt.links.new(_anvil_coords(nt), tex.inputs["Vector"])
        _anvil_set(tex, 250.0, "Scale")
        _anvil_set(tex, 1.0, "Distortion")
        return _anvil_ramp(nt, tex.outputs["Fac"], _anvil_shade(base, 0.8), _anvil_shade(tuple(0.35 + 0.65 * v for v in base), 1.0), pos=(0.45, 0.75)).outputs["Color"]
    if extra.get("noise"):
        tex = nt.nodes.new("ShaderNodeTexNoise")
        nt.links.new(_anvil_coords(nt), tex.inputs["Vector"])
        _anvil_set(tex, 8.0, "Scale")
        _anvil_set(tex, 6.0, "Detail")
        k = 1.0 - extra["noise"]
        return _anvil_ramp(nt, tex.outputs["Fac"], _anvil_shade(base, k), _anvil_shade(base, 1.0)).outputs["Color"]
    return None

_ANVIL_ALIASES = {
    "madeira": "wood", "metal": "painted_metal", "aco": "steel", "aço": "steel", "cromo": "chrome",
    "aluminio": "aluminum", "alumínio": "aluminum", "vidro": "glass", "borracha": "rubber",
    "plastico": "plastic", "plástico": "plastic", "tecido": "fabric", "couro": "leather",
    "pedra": "stone", "tijolo": "brick", "concreto": "concrete", "reboco": "plaster", "telha": "roof_tile",
    "pele": "skin", "pelo": "fur_short", "pelos": "fur_short", "escama": "scales", "escamas": "scales",
    "jeans": "denim", "folha": "foliage", "folhagem": "foliage", "terra": "soil", "luz": "emissive",
}


def _anvil_resolve_preset(p):
    if p in ANVIL_PRESETS:
        return p
    k = str(p).strip().lower().replace(" ", "_").replace("-", "_")
    return k if k in ANVIL_PRESETS else _ANVIL_ALIASES.get(k, p)


def anvil_material(*args, preset=None, color=None, name=None, metallic=None, roughness=None, **_ignorado):
    """Cria (ou reaproveita) um material a partir de um preset da biblioteca.

    Uso: anvil_material("wood") ou anvil_material("Assento", preset="wood", color=(r, g, b)).
    color: (r, g, b) entre 0 e 1 para trocar a cor base do preset.
    O resultado se adapta a ANVIL_STYLE ("realista" ou "cel-shading").
    """
    if args:
        if preset is None:
            preset = args[0]
            if len(args) > 1 and color is None and isinstance(args[1], (tuple, list)):
                color = args[1]
        elif name is None:
            name = args[0]
    color = color or _ignorado.get("cor")
    preset = _anvil_resolve_preset(preset)
    if preset not in ANVIL_PRESETS:
        raise ValueError(f"Preset '{preset}' não existe. Opções: {sorted(ANVIL_PRESETS)}")
    base, met, rough, extra = ANVIL_PRESETS[preset]
    base = tuple(color[:3]) if color else base
    met = met if metallic is None else metallic
    rough = rough if roughness is None else roughness
    name = name or ("ANVIL_" + preset)
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mat.diffuse_color = _anvil_shade(base, 1.0)

    if globals().get("ANVIL_STYLE") == "cel-shading":
        diffuse = nt.nodes.new("ShaderNodeBsdfDiffuse")
        _anvil_set(diffuse, _anvil_shade(base, 1.0), "Color")
        to_rgb = nt.nodes.new("ShaderNodeShaderToRGB")
        nt.links.new(diffuse.outputs[0], to_rgb.inputs[0])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        cr = ramp.color_ramp
        cr.interpolation = "CONSTANT"
        cr.elements[0].position, cr.elements[0].color = 0.0, _anvil_shade(base, 0.35)
        cr.elements[1].position, cr.elements[1].color = 0.25, _anvil_shade(base, 0.7)
        e = cr.elements.new(0.6)
        e.color = _anvil_shade(base, 1.0 if met < 0.5 else 1.25)
        nt.links.new(to_rgb.outputs["Color"], ramp.inputs["Fac"])
        emit = nt.nodes.new("ShaderNodeEmission")
        nt.links.new(ramp.outputs["Color"], emit.inputs["Color"])
        _anvil_set(emit, extra.get("emission", 1.0), "Strength")
        nt.links.new(emit.outputs[0], out.inputs["Surface"])
        return mat

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    src = _anvil_color_source(nt, base, extra)
    if src is not None:
        nt.links.new(src, bsdf.inputs["Base Color"])
    else:
        _anvil_set(bsdf, _anvil_shade(base, 1.0), "Base Color")
    _anvil_set(bsdf, met, "Metallic")
    _anvil_set(bsdf, rough, "Roughness")
    _bump = next((n for n in nt.nodes if n.label == "ANVIL_BUMP"), None)
    if _bump is not None:
        nt.links.new(_bump.outputs["Normal"], bsdf.inputs["Normal"])
    if extra.get("sheen"):
        _anvil_set(bsdf, extra["sheen"], "Sheen Weight", "Sheen")
        _anvil_set(bsdf, 0.5, "Sheen Roughness")
    if extra.get("subsurface"):
        _anvil_set(bsdf, extra["subsurface"], "Subsurface Weight", "Subsurface")
        _anvil_set(bsdf, (1.0, 0.35, 0.2), "Subsurface Radius")
        _anvil_set(bsdf, 0.01, "Subsurface Scale")
    if extra.get("coat"):
        _anvil_set(bsdf, extra["coat"], "Coat Weight", "Clearcoat")
    if extra.get("transmission"):
        _anvil_set(bsdf, extra["transmission"], "Transmission Weight", "Transmission")
    if extra.get("emission"):
        _anvil_set(bsdf, _anvil_shade(base, 1.0), "Emission Color", "Emission")
        _anvil_set(bsdf, extra["emission"], "Emission Strength")
    return mat

def anvil_assign(obj, mat, face_indices=None):
    """Aplica o material ao objeto inteiro ou só às faces indicadas."""
    mats = obj.data.materials
    if mat.name not in [m.name for m in mats if m]:
        mats.append(mat)
    idx = [m.name if m else None for m in mats].index(mat.name)
    if hasattr(obj.data, "polygons"):
        polys = obj.data.polygons
        targets = range(len(polys)) if face_indices is None else face_indices
        for i in targets:
            polys[i].material_index = idx
    return idx

def anvil_outline(obj, thickness=0.01):
    """Contorno preto estilo quadrinhos (casco invertido com backface culling)."""
    mat = bpy.data.materials.get("ANVIL_outline")
    if mat is None:
        mat = bpy.data.materials.new("ANVIL_outline")
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        emit = nt.nodes.new("ShaderNodeEmission")
        _anvil_set(emit, (0.0, 0.0, 0.0, 1.0), "Color")
        nt.links.new(emit.outputs[0], out.inputs["Surface"])
        mat.use_backface_culling = True
    obj.data.materials.append(mat)
    mod = obj.modifiers.new("ANVIL_outline", "SOLIDIFY")
    mod.thickness = thickness
    mod.offset = 1.0
    mod.use_flip_normals = True
    mod.use_rim = False
    mod.material_offset = len(obj.data.materials) - 1
    return mod
'''


def prelude(style: str) -> str:
    """Código colado antes do script gerado: define o estilo e a biblioteca."""
    return f"ANVIL_STYLE = {style!r}\n" + MATERIAL_LIB


PRESET_NAMES = [
    "car_paint", "painted_metal", "worn_metal", "steel", "chrome", "aluminum", "dark_metal",
    "glass", "tinted_glass", "rubber", "plastic", "wood", "brick", "concrete", "plaster",
    "roof_tile", "stone", "fabric", "leather", "emissive", "soil", "foliage",
    "fur_short", "skin", "scales", "denim",
]


# Estúdio de render: céu em degradê com horizonte (reflexo para metais e vidro)
# e sol de borda nítida (faixas limpas no cel-shading). Usado pelo harness no
# render de cada tentativa e pelo teste de materiais.
STUDIO_LIB = r'''
import bpy, math

def anvil_studio(scene, sun_name="ANVIL_SUN", stage_collection=None):
    w = bpy.data.worlds.get("ANVIL_WORLD") or bpy.data.worlds.new("ANVIL_WORLD")
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    rng = nt.nodes.new("ShaderNodeMapRange")
    rng.inputs["From Min"].default_value = -1.0
    rng.inputs["From Max"].default_value = 1.0
    nt.links.new(sep.outputs["Z"], rng.inputs["Value"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position, cr.elements[0].color = 0.47, (0.04, 0.04, 0.045, 1.0)   # chão
    cr.elements[1].position, cr.elements[1].color = 0.51, (0.85, 0.85, 0.88, 1.0)    # horizonte claro
    top = cr.elements.new(0.9)
    top.color = (0.30, 0.36, 0.48, 1.0)                                             # céu
    nt.links.new(rng.outputs["Result"], ramp.inputs["Fac"])
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 0.8
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    scene.world = w

    sun = bpy.data.objects.get(sun_name)
    if sun is None:
        sun = bpy.data.objects.new(sun_name, bpy.data.lights.new(sun_name, type="SUN"))
        (stage_collection or scene.collection).objects.link(sun)
    sun.data.energy = 3.0
    sun.data.angle = math.radians(1.0)       # sombra nítida
    sun.rotation_euler = (math.radians(50), 0, math.radians(35))
    return sun
'''
