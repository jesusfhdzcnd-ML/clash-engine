from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Tuple, Any

class MatchEventInput(BaseModel):
    time: float = Field(..., description="Segundo del despliegue en la partida")
    player: str = Field("user", description="Jugador que realiza la accion ('user' u 'opponent')")
    card: str = Field(..., description="Nombre de la carta jugada")
    hand: List[str] = Field(default_factory=list, description="Las 4 cartas disponibles en la mano al jugar")
    target_attacker: Optional[str] = Field(None, description="Amenaza enemiga a la que responde")
    tile: Tuple[float, float] = Field((9.0, 14.0), description="Coordenadas (x, y) en la arena")
    enemy_lane_x: float = Field(3.5, description="Carril x por donde avanza el enemigo")
    seconds_at_cap: float = Field(0.0, description="Segundos acumulados al tope de 10 de elixir")

class MatchReviewRequest(BaseModel):
    player_name: str = Field("Chuy", description="Nombre del jugador auditado")
    opponent_name: str = Field("Rival", description="Nombre del oponente")
    player_deck: List[str] = Field(default_factory=list, description="Mazo de 8 cartas del jugador")
    opponent_deck: List[str] = Field(default_factory=list, description="Mazo de 8 cartas del rival")
    events: List[MatchEventInput] = Field(..., description="Historial cronologico de eventos de la partida")

class MatchReviewResponse(BaseModel):
    player_name: str
    opponent_name: str
    tactical_accuracy_pct: float
    summary: Dict[str, int]
    blunders: List[Dict[str, Any]]
    mistakes: List[Dict[str, Any]]
    inaccuracies: List[Dict[str, Any]]
    brilliant_moves: List[Dict[str, Any]]
    leaks: List[Dict[str, Any]]

class PatchSimulationRequest(BaseModel):
    modifications: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Diccionario de cartas y porcentaje de cambio en cada stat. Ej: {'Knight': {'damage_per_hit': 8.0}}"
    )
    meta_roster: Optional[List[str]] = Field(
        None,
        description="Lista opcional de tropas del meta a evaluar. Si se omite, se usa el roster representativo oficial."
    )
    with_tower: bool = Field(True, description="Si los combates se evaluan con fuego de apoyo de torre defensora")

class CardImpactDetail(BaseModel):
    weighted_elixir_shift: float
    matchup_flips: List[Dict[str, Any]]
    is_directly_patched: bool

class PatchSimulationResponse(BaseModel):
    cards_impacted: Dict[str, CardImpactDetail]
    total_cards_evaluated: int
    summary_verdict: str

class WatchlistEntry(BaseModel):
    card: str
    efficiency_score: float
    z_score: float
    status: str

class WatchlistResponse(BaseModel):
    mean_meta_efficiency: float
    std_meta_efficiency: float
    watchlist: List[WatchlistEntry]
    automated_patch_proposals: List[Dict[str, Any]]

class CardStatsResponse(BaseModel):
    name: str
    type: str
    rarity: str
    elixir: int
    hp: int
    damage_per_hit: int
    dps: float
    hit_speed: float
    range: float
    speed: float
    aoe_shape: str
    is_champion: bool
    is_hero: bool
    has_evolution: bool
    spell_interactions: Optional[Dict[str, str]] = None
