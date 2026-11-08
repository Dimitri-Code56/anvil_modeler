---
name: responder-com-fontes
description: "Como responder dúvidas sobre o Blender com base na documentação: buscar antes, citar os trechos com [n], admitir quando a documentação não cobre e indicar a versão."
---
# Responder com fontes

1. **Busque antes de responder.** Toda pergunta técnica passa por `buscar_documentacao`. Use termos em inglês
   como aparecem na documentação: nome do modificador ("Bevel modifier"), do nó ("Principled BSDF", "ShaderNodeTexBrick"),
   do operador ("bpy.ops.mesh.primitive_cylinder_add") ou da classe/propriedade ("SubsurfModifier.levels").
2. **Uma busca por assunto.** Se a pergunta tem duas partes (ex.: modificador + material), faça duas buscas.
3. **Cite.** Toda afirmação técnica leva o número do trecho de onde veio: "O Bevel tem a opção Limit Method [2]".
   Não cite um trecho que não diz aquilo.
4. **Sem trecho, sem invenção.** Se nenhum trecho cobre o que foi perguntado, diga "a documentação indexada não
   cobre isso" e, se souber, dê a orientação geral marcada como tal.
5. **Versão.** As respostas valem para a versão do Blender indexada; se o usuário citar outra versão e algo mudou
   de nome (ex.: entradas do Principled BSDF), avise.
6. **Formato.** Resposta curta e direta; passo a passo numerado para ações na interface; código só quando pedido
   ou quando for o jeito mais claro.
