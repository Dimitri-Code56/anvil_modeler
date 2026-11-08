---
name: varkos-ground-particles-and-dust
description: Regras para partículas de atmosfera rasteira em Varkos. Proíbe risquinhos longos parecendo chuva em ambientes abertos e secos.
---
# Padrão de Partículas Rasteiras e Atmosfera (Varkos)

1. **Proibido Riscos de Chuva (`Stretched Billboard` vertical):** Em planetas/luas sem atmosfera chuvosa (como Varkos), partículas ambientais de vento nunca devem usar texturas compridas verticais que pareçam chuva.
2. **Partículas de Poeira e Cinzas Rasteiras (`Ground Dust Gusts`):** Devem usar billboards redondos pequenos (`Size 0.06` a `0.14`) com opacidade baixa (`Alpha 0.25`), movendo-se horizontalmente rente ao chão (`0.2m a 0.8m` de altura) para simular grãos de poeira lunar e cinzas soprados pelo vento do mundo aberto.

## No projeto (onde fica cada coisa)
- Emissor: `VarkosGroundAtmosphereVFX` (em `Scripts/Jogo/VarkosChao3D.cs`) — poeira na cor do chão local, vapor das grelhas do forte, cinza de ferrugem no norte, esporos ciano no leste.
- Partícula: `VarkosVFX.PoeiraRasteira` + material transparente `VarkosVFXTextureGenerator.Mat_PoeiraSuave` (ponto redondo de borda suave; o alpha vem da cor).
- Efeitos de combate/ácido seguem a skill `varkos-liquids-and-vfx-hd` (recorte duro) — a poeira ambiente é a exceção suave.
