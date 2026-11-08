from pathlib import Path

from anvil_modeler.skills import available_projects, available_styles, catalog_text, compose_skills, list_skills

SKILLS = Path(__file__).resolve().parents[1] / "skills"


def test_toda_skill_tem_nome_e_descricao():
    skills = list_skills(SKILLS)
    assert skills and all(s.name and s.description for s in skills)


def test_camadas_e_opcoes():
    assert {"realista", "cel-shading"} <= set(available_styles(SKILLS))
    assert "elpis" in available_projects(SKILLS)


def test_catalogo_generico_nao_mostra_projeto():
    cat = catalog_text(SKILLS)
    assert "veiculos" in cat and "elpis-level-design" not in cat
    assert "elpis-level-design" in catalog_text(SKILLS, "elpis")


def test_composicao_sempre_tem_base_materiais_e_estilo():
    text = compose_skills(SKILLS, ["veiculos"], "realista")
    for header in ("(base): qualidade-visual", "(tecnicas): veiculos", "(materiais): biblioteca-pbr", "(estilos): realista"):
        assert f"## Skill {header}" in text
    assert "(estilos): cel-shading" not in text and "(tecnicas): arquitetura" not in text
    assert text.index("(base)") < text.index("(tecnicas)") < text.index("(materiais)") < text.index("(estilos)")


def test_superficies_sao_escolhiveis_e_entram_depois_das_tecnicas():
    cat = catalog_text(SKILLS)
    for name in ("pelos-e-penas", "pele", "tecidos-materiais", "escamas-e-carapacas"):
        assert name in cat
    text = compose_skills(SKILLS, ["organico", "pelos-e-penas"], "realista")
    assert "(superficies): pelos-e-penas" in text and "(superficies): pele" not in text
    assert text.index("(tecnicas)") < text.index("(superficies)") < text.index("(materiais)")


def test_projeto_so_entra_quando_ativo():
    assert "(projetos)" not in compose_skills(SKILLS, ["elpis-blender-pro-modeling"], "realista")
    assert "(projetos): elpis-blender-pro-modeling" in compose_skills(SKILLS, ["elpis-blender-pro-modeling"], "cel-shading", "elpis")
