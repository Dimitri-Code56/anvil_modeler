from __future__ import annotations

import operator
from typing import Annotated, Optional, TypedDict


class Attempt(TypedDict, total=False):
    iteration: int
    code: str
    guard_error: Optional[str]
    exec_error: Optional[str]
    render_path: Optional[str]
    score: float
    approved: bool
    feedback: str


class AnvilState(TypedDict, total=False):
    # entrada
    run_id: str
    asset_name: str
    scene_key: str          # coleção no Blender: asset + modo (cada modo fica na sua)
    description: str
    concept_path: Optional[str]
    style: str
    project: Optional[str]
    use_skills: bool
    use_rag: bool
    use_loop: bool
    use_agent: bool
    max_iters: int
    # intermediários
    spec: Optional[dict]
    api_sheet: str
    api_missing: list[str]
    docs_context: str
    iteration: int
    code: str
    guard_error: Optional[str]
    exec_error: Optional[str]
    render_path: Optional[str]
    evaluation: Optional[dict]
    # histórico (acumula a cada tentativa)
    attempts: Annotated[list[Attempt], operator.add]
