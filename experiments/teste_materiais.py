"""Teste visual da biblioteca de materiais, numa cena temporária.

Rode DENTRO do Blender (aba Scripting → abrir este arquivo → Run Script),
ou peça ao Claude para executá-lo pelo MCP. Cria a cena "ANVIL_TESTE",
renderiza runs/teste_materiais.png com todos os presets nos dois estilos
e apaga tudo o que criou. A sua cena atual não é alterada.
"""
import math
import runpy
import traceback
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path(r"C:\Users\dimit\Documents\anvil_modeler")
lib = runpy.run_path(str(ROOT / "src" / "anvil_modeler" / "blender_lib.py"))
OUT = ROOT / "runs" / "teste_materiais.png"

before_mats = set(bpy.data.materials.keys())
scene = bpy.data.scenes.new("ANVIL_TESTE")
created_objs, created_data, errors = [], [], []
cols = 11
for row, style in enumerate(["realista", "cel-shading"]):
    g = {}
    exec(lib["prelude"](style), g)
    for i, p in enumerate(lib["PRESET_NAMES"]):
        try:
            me = bpy.data.meshes.new(f"T_{style}_{p}")
            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.4)
            bm.to_mesh(me)
            bm.free()
            for poly in me.polygons:
                poly.use_smooth = True
            ob = bpy.data.objects.new(me.name, me)
            scene.collection.objects.link(ob)
            created_objs.append(ob); created_data.append(me)
            ob.location = ((i % cols) * 1.0, -(row * 2 + i // cols) * 1.0, 0)
            g["anvil_assign"](ob, g["anvil_material"](p, name=f"T_{style}_{p}"))
            if style == "cel-shading":
                g["anvil_outline"](ob, 0.02)
        except Exception:
            errors.append(f"{style}/{p}: " + traceback.format_exc().splitlines()[-1])

cam = bpy.data.objects.new("T_cam", bpy.data.cameras.new("T_cam"))
scene.collection.objects.link(cam); created_objs.append(cam); created_data.append(cam.data)
cam.data.type = "ORTHO"; cam.data.ortho_scale = 11.5
cam.location = (5.0, -1.5, 20)
scene.camera = cam
studio = {}
exec(lib["STUDIO_LIB"], studio)
sun = studio["anvil_studio"](scene, sun_name="T_sun")
created_objs.append(sun); created_data.append(sun.data)
world = scene.world
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        scene.render.engine = eng
        break
    except TypeError:
        pass
scene.render.resolution_x, scene.render.resolution_y = 1100, 420
scene.render.filepath = str(OUT)

window = bpy.context.window
previous = window.scene if window else None
render_error = None
try:
    if window:
        window.scene = scene
    bpy.ops.render.render(write_still=True)
except Exception as e:
    render_error = str(e)
finally:
    if window and previous:
        window.scene = previous
    # limpeza por nome: no Blender 5.x remover o objeto já pode apagar a malha junto
    for ob in created_objs:
        try:
            bpy.data.objects.remove(ob, do_unlink=True)
        except ReferenceError:
            pass
    for coll in (bpy.data.meshes, bpy.data.cameras, bpy.data.lights):
        for d in list(coll):
            if d.name.startswith("T_"):
                coll.remove(d)
    for name in set(bpy.data.materials.keys()) - before_mats:
        bpy.data.materials.remove(bpy.data.materials[name])
    bpy.data.worlds.remove(world)
    bpy.data.scenes.remove(scene)

result = {"blender": bpy.app.version_string, "errors": errors, "render_error": render_error, "render": str(OUT)}
print(result)
