---
name: arquitetura
description: "Construções (casas, prédios, cômodos, muros, escadas): receita com as ferramentas para fundação, paredes com espessura, empena, aberturas por cortar, molduras, telhado, varanda e escada, com escala humana real."
---
# Arquitetura

## Escala humana
Pé-direito 2,6–3,0 m · porta 0,9 × 2,1 m · janela 1,2 × 1,2 m com peitoril a 1,0 m · degrau 0,17 × 0,28 m ·
parede externa 0,2–0,3 m · beiral 0,3–0,6 m.

## Receita: casa (modo agente)
1. `iniciar_asset`. Planta retangular: largura em X, profundidade em Y, frente em -Y.
2. Fundação: `caixa` um pouco maior que a planta, 0,3–0,8 m de altura, material `stone`/`concrete`.
3. Paredes da frente e do fundo **com empena**: `perfil_extrudado` no plano XZ (pentágono: base, topo da
   parede, cumeeira), espessura 0,2, posicionadas em y = ±profundidade/2.
4. Paredes laterais: `caixa` com 0,2 de espessura, encostando nas da frente e do fundo.
5. Aberturas: `cortar` (caixa) em cada porta e janela, atravessando só a parede.
6. Molduras e peitoris: `caixa` finas em volta das aberturas (`plaster`/`wood`); vidros: `caixa` de 1 cm
   dentro do vão com `glass`; porta: `caixa` de madeira recuada.
7. Telhado: `perfil_extrudado` no plano XZ com o desenho das duas águas em espessura (paralelogramos
   seguindo a inclinação), espessura = profundidade + 2 × beiral, `roof_tile`.
8. Detalhes: chaminé (`caixa`), varanda (piso `caixa`, colunas `revolucao`/`cilindro` + `repetir`, guarda-corpo
   `caixa` + `repetir`), escada (`caixa` + `repetir` com deslocamento [0, -0,28, -0,17]), calhas (`tubo_por_curva`).
9. Materiais: paredes `brick`/`plaster`, telhado `roof_tile`, esquadrias `wood`/`aluminum`. Conferência.

---

## Modo script (referência para quem escreve código bpy)

## Escala humana (use como referência)
Pé-direito 2.6–3.0 m · porta 0.9 × 2.1 m · janela 1.2 × 1.2 m com peitoril a 1.0 m · degrau 0.17 m de altura × 0.28 m de piso · parede externa 0.2–0.3 m, interna 0.12–0.15 m · laje 0.15 m.

## Construção
1. **Planta primeiro:** defina o contorno da planta como polígono 2D; paredes = contorno extrudado para dentro com a espessura (`bmesh.ops.inset_region` na face da planta, depois extrude para cima no pé-direito). Não monte paredes com cubos soltos.
2. **Aberturas:** portas e janelas como cortadores `BOOLEAN DIFFERENCE` na parede; depois adicione batente/moldura e vidro (`glass`) dentro do vão.
3. **Telhado:** duas águas = perfil triangular extrudado no comprimento com beiral de 0.3–0.6 m além das paredes; espessura real (0.1–0.2 m). Telhas: array de faixas ou textura do material `roof_tile`.
4. **Base e chão:** fundação/rodapé de 0.2–0.5 m saliente; calçada ou piso ao redor ancora o prédio no terreno.
5. **Detalhes que vendem realismo:** calhas, soleiras, vergas sobre janelas, chaminé, degraus na entrada. Variar levemente alinhamento evita aspecto de maquete.
6. **Materiais típicos:** paredes `brick`/`plaster`/`concrete`, telhado `roof_tile`, esquadrias `wood` ou `aluminum`, vidros `glass`.

## Telhados (modo script) — o telhado é FORMA PRIMÁRIA
O telhado é o que mais identifica uma casa. Faça-o na **blocagem**, junto com as paredes, e confira no render (de
frente e de lado) antes de qualquer detalhe. Nunca use massa orgânica, displace ou malha deformada: telhado é feito de
planos retos com espessura.

Regras: inclinação 25–45° (telha cerâmica 30–35°) · beiral 0,3–0,6 m além das paredes · espessura 0,10–0,20 m ·
o telhado cobre todas as paredes · a face de baixo encosta no topo das paredes · empenas fecham o vão triangular ·
varanda/alpendre é uma água própria presa **embaixo** do beiral principal (ou o mesmo plano continuado), nunca uma laje
solta. Material `roof_tile`; testeira (tábua da borda do beiral) em `plaster`/`wood`.

```python
import bpy, bmesh, math

def extrudar_perfil_yz(nome, pontos_yz, comprimento_x, x_centro=0.0):
    """Perfil fechado no plano YZ (lista de (y, z) em ordem) extrudado ao longo de X."""
    bm = bmesh.new()
    a = [bm.verts.new((x_centro - comprimento_x / 2, y, z)) for y, z in pontos_yz]
    b = [bm.verts.new((x_centro + comprimento_x / 2, y, z)) for y, z in pontos_yz]
    bm.faces.new(a[::-1]); bm.faces.new(b)
    for i in range(len(a)):
        j = (i + 1) % len(a)
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(nome); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(nome, me); bpy.context.collection.objects.link(ob)
    return ob

def telhado_duas_aguas(nome, largura, profundidade, z_paredes, inclinacao=32, beiral=0.45, espessura=0.12):
    """Cumeeira ao longo de X. largura (X) e profundidade (Y) são da casa SEM beiral; z_paredes = topo das paredes."""
    a = math.radians(inclinacao)
    D = profundidade / 2 + beiral                  # do eixo da cumeeira até a borda do beiral (em planta)
    h = D * math.tan(a)                            # altura da cumeeira acima da borda do beiral
    t = espessura / math.cos(a)                    # espessura medida na vertical
    casca = [(-D, 0), (0, h), (D, 0), (D, -t), (0, h - t), (-D, -t)]   # "V invertido" com espessura
    ob = extrudar_perfil_yz(nome, casca, largura + 2 * beiral)
    ob.location.z = z_paredes + t - beiral * math.tan(a)   # a face de baixo passa no topo da parede
    return ob, h

def empenas(nome, largura, profundidade, z_paredes, inclinacao=32, espessura_parede=0.2):
    """Triângulos que fecham as pontas entre a parede e o telhado de duas águas."""
    a = math.radians(inclinacao); p = profundidade / 2
    tri = [(-p, 0), (0, p * math.tan(a)), (p, 0)]
    obs = []
    for lado, x in (("E", -largura / 2 + espessura_parede / 2), ("D", largura / 2 - espessura_parede / 2)):
        ob = extrudar_perfil_yz(f"{nome}_{lado}", tri, espessura_parede, x_centro=x)
        ob.location.z = z_paredes
        obs.append(ob)
    return obs

def telhado_quatro_aguas(nome, largura, profundidade, z_paredes, inclinacao=30, beiral=0.45, espessura=0.12):
    """Quatro águas: base retangular com beiral e cumeeira curta no meio (largura > profundidade)."""
    a = math.radians(inclinacao)
    L, D = largura / 2 + beiral, profundidade / 2 + beiral
    h = D * math.tan(a); r = max(L - D, 0.0)       # meia-cumeeira
    bm = bmesh.new()
    v = [bm.verts.new(c) for c in ((-L, -D, 0), (L, -D, 0), (L, D, 0), (-L, D, 0), (-r, 0, h), (r, 0, h))]
    for f in ((v[0], v[1], v[5], v[4]), (v[2], v[3], v[4], v[5]), (v[1], v[2], v[5]), (v[3], v[0], v[4])):
        bm.faces.new(f)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(nome); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(nome, me); bpy.context.collection.objects.link(ob)
    s = ob.modifiers.new("Espessura", "SOLIDIFY"); s.thickness = espessura; s.offset = -1
    ob.location.z = z_paredes - beiral * math.tan(a) + espessura
    return ob, h

def agua_unica(nome, largura, y_parede, y_borda, z_alto, z_baixo, espessura=0.1):
    """Uma água (varanda/alpendre): desce da parede (y_parede, z_alto) até a borda (y_borda, z_baixo)."""
    casca = [(y_parede, z_alto), (y_borda, z_baixo), (y_borda, z_baixo - espessura), (y_parede, z_alto - espessura)]
    return extrudar_perfil_yz(nome, casca, largura)
```

Uso típico (casa 8 × 6 m, paredes até z = 3,0, frente em −Y, varanda de 2 m na frente):
```python
telhado, h = telhado_duas_aguas("telhado", 8, 6, 3.0)            # cumeeira em X, empenas nas laterais
empenas("empena", 8, 6, 3.0)
varanda = agua_unica("telhado_varanda", 8.4, -3.0, -5.0, 2.95, 2.55)   # encosta sob o beiral da frente
for ob in (telhado, varanda):
    anvil_assign(ob, anvil_material("roof_tile"))
```
Para a cumeeira correr em Y (empenas na frente e atrás), gire o telhado e as empenas 90° em Z
(`ob.rotation_euler.z = math.radians(90)`) e troque largura por profundidade.
Detalhes depois da forma conferida: testeira ao longo das bordas do beiral (`caixa` fina), cumeeira com uma peça
arredondada, calhas (`tubo_por_curva`), chaminé atravessando o telhado.
