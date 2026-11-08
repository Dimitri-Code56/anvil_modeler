from anvil_modeler.guardrails import check_code


def test_codigo_valido_passa():
    code = "import bpy, bmesh\nfrom mathutils import Vector\nbpy.ops.mesh.primitive_cube_add(size=1)\nresult = {}"
    assert check_code(code) is None


def test_bloqueia_import_fora_da_whitelist():
    assert "Import" in check_code("import os\nos.remove('x')")


def test_bloqueia_salvar_arquivo():
    assert "proibida" in check_code("import bpy\nbpy.ops.wm.save_mainfile()")


def test_bloqueia_apagar_objetos():
    assert "proibida" in check_code("import bpy\nbpy.data.objects.remove(bpy.data.objects[0])")


def test_bloqueia_exec_e_open():
    assert check_code("exec('print(1)')")
    assert check_code("open('C:/x.txt', 'w')")


def test_syntax_error():
    assert "SyntaxError" in check_code("def (:")
