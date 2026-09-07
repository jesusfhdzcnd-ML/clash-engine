from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from clash_core import build_or_load_canonical_db, ClashPhysicsEngine, ClashMatchReviewer
from ..schemas import MatchReviewRequest, MatchReviewResponse

router = APIRouter(prefix="/api/v1/review", tags=["Match Review & Blunders"])

db = build_or_load_canonical_db()
physics = ClashPhysicsEngine(db)
reviewer = ClashMatchReviewer(physics)

@router.post("/analyze", response_model=MatchReviewResponse)
def analyze_match_endpoint(request: MatchReviewRequest):
    """
    Audita una partida jugada a jugada estilo Chess.com Game Review.
    Detecta:
    - Trade Blunders: Intercambios deficientes teniendo mejor respuesta en mano.
    - Placement Blunders: Estructuras colocadas fuera del radio de atraccion de 5.5 casillas.
    - Fugas de Elixir: Gotas desperdiciadas al estar al tope de 10.
    - Puntuacion de Precision Tactica (Accuracy %).
    """
    match_dict = request.dict() if hasattr(request, "dict") else request.model_dump()
    report = reviewer.analyze_match(match_dict)
    
    return MatchReviewResponse(
        player_name=request.player_name,
        opponent_name=request.opponent_name,
        tactical_accuracy_pct=report["tactical_accuracy_pct"],
        summary=report["summary"],
        blunders=report["blunders"],
        mistakes=report["mistakes"],
        inaccuracies=report["inaccuracies"],
        brilliant_moves=report.get("brilliant_moves", []),
        leaks=report["leaks"]
    )
