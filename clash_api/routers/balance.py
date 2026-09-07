from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from clash_core import (
    build_or_load_canonical_db, ClashPhysicsEngine,
    MultiCardPatchSimulator, AutonomousBalanceOptimizer, get_card
)
from ..schemas import (
    PatchSimulationRequest, PatchSimulationResponse, CardImpactDetail,
    WatchlistResponse, WatchlistEntry
)

router = APIRouter(prefix="/api/v1/balance", tags=["Game Balance & Patch Simulation"])

db = build_or_load_canonical_db()
physics = ClashPhysicsEngine(db)
patch_sim = MultiCardPatchSimulator(physics)

DEFAULT_META_WEIGHTS = {
    "Knight": 0.32, "Mini P.E.K.K.A.": 0.18, "Musketeer": 0.20,
    "Valkyrie": 0.22, "The Log": 0.45, "Fireball": 0.28,
    "Hog Rider": 0.22, "P.E.K.K.A": 0.15, "Cannon": 0.15,
    "Goblins": 0.20, "Archers": 0.15, "Skeletons": 0.30
}

DEFAULT_ROSTER = [
    "Knight", "Mini P.E.K.K.A.", "Musketeer", "Valkyrie",
    "Hog Rider", "P.E.K.K.A", "Mega Knight", "Golden Knight"
]

optimizer = AutonomousBalanceOptimizer(physics, DEFAULT_META_WEIGHTS)

@router.post("/simulate-patch", response_model=PatchSimulationResponse)
def simulate_patch_endpoint(request: PatchSimulationRequest):
    """
    Simula un parche de balance multi-carta de 6 a 12 modificaciones simultaneas.
    Calcula efectos directos y dano o beneficio colateral en cartas no modificadas.
    """
    roster = request.meta_roster or DEFAULT_ROSTER
    report = patch_sim.simulate_balance_patch(
        request.modifications, roster, DEFAULT_META_WEIGHTS, with_tower=request.with_tower
    )
    
    impacts = {}
    for cname, data in report.items():
        impacts[cname] = CardImpactDetail(
            weighted_elixir_shift=data["weighted_elixir_shift"],
            matchup_flips=data["matchup_flips"],
            is_directly_patched=data["is_directly_patched"]
        )
        
    direct_count = sum(1 for d in impacts.values() if d.is_directly_patched)
    collateral_count = len(impacts) - direct_count
    verdict = f"Parche evaluado con exito: {direct_count} cartas modificadas directamente y {collateral_count} cartas afectadas por daño/beneficio colateral en el meta."

    return PatchSimulationResponse(
        cards_impacted=impacts,
        total_cards_evaluated=len(impacts),
        summary_verdict=verdict
    )

@router.get("/watchlist", response_model=WatchlistResponse)
def get_watchlist_endpoint():
    """
    Audita la salud del metajuego en vivo y devuelve el radar de cartas rotas (CRITICAL_NERF)
    o inviables (CRITICAL_BUFF) con propuestas automaticas de ajuste acotadas por umbrales duros.
    """
    watchlist_raw, mean_eff, std_eff = optimizer.scan_meta_health(DEFAULT_ROSTER)
    _, proposals = optimizer.generate_automated_patch_proposal(DEFAULT_ROSTER)
    
    entries = [
        WatchlistEntry(
            card=w["card"], efficiency_score=w["efficiency_score"],
            z_score=w["z_score"], status=w["status"]
        ) for w in watchlist_raw
    ]
    
    return WatchlistResponse(
        mean_meta_efficiency=round(mean_eff, 4),
        std_meta_efficiency=round(std_eff, 4),
        watchlist=entries,
        automated_patch_proposals=proposals
    )
