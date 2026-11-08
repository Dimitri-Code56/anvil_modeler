---
name: solucao-de-problemas
description: "Quando o usuário relata um erro, traceback ou algo que não funcionou no Blender: ler a mensagem, achar a causa provável e propor a correção com base na documentação."
---
# Resolver problemas no Blender

1. **Leia a última linha do traceback** e identifique o tipo: `AttributeError` (nome que não existe nesta
   versão), `TypeError` (tipo do argumento, ex.: tupla onde se espera número), `RuntimeError: Operator ...
   poll() failed` (contexto errado: modo de edição, objeto ativo, área), `KeyError` (nome de nó/socket/objeto).
2. **Busque o nome envolvido** na documentação da API para conferir se existe e qual é o tipo esperado.
3. **Mudanças de versão são causa comum:** entradas do Principled BSDF renomeadas no 4.0 ("Subsurface Weight",
   "Coat Weight", "Emission Color"), `use_auto_smooth` removido no 4.1, motores de render renomeados.
4. **Responda em três partes:** causa provável → correção (código ou passo na interface) → como confirmar que
   resolveu.
5. Se o erro vier de algo fora do Blender (sistema, permissões, rede), diga isso e não invente correção.
