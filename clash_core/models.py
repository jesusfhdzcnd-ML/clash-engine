from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

@dataclass
class ProjectileInfo:
    name: str
    speed: float = 0.0
    radius: float = 0.0
    pushback: float = 0.0
    crown_tower_damage_percent: int = 100

@dataclass
class LevelStats:
    hp: int
    damage_per_hit: int
    damage: int
    dps: float
    shield_hp: int = 0
    death_damage: int = 0
    crown_tower_damage: int = 0

@dataclass
class DeathSpawnInfo:
    unit_name: str
    count: int
    is_flying: bool
    hp_lvl11: int
    dmg_lvl11: int
    dps_lvl11: float
    hit_speed: float

@dataclass
class AbilityData:
    ability_name: str
    elixir_cost: int
    max_uses_per_deployment: int = 1
    duration: float = 0.0
    ability_type: str = ""
    description: str = ""
    special_value: float = 0.0
    summoned_unit: Optional[str] = None

@dataclass
class EvolutionData:
    cycles: int
    ability_name: str
    ability_type: str
    description: str = ""
    stat_modifiers: Dict[str, float] = field(default_factory=dict)

@dataclass
class CompleteCard:
    id: int
    key: str
    sc_key: str
    name: str
    elixir: int
    type: str
    rarity: str
    role: str
    count: int = 1
    hit_speed: float = 0.0
    load_time: float = 0.0
    range: float = 0.0
    minimum_range: float = 0.0
    speed: float = 0.0
    sight_range: float = 5.5
    mass: int = 0
    collision_radius: float = 0.0
    attacks_ground: bool = True
    attacks_air: bool = False
    target_only_buildings: bool = False
    is_flying: bool = False
    has_shield: bool = False
    has_death_damage: bool = False
    death_spawn: Optional[DeathSpawnInfo] = None
    lifetime: float = 0.0
    is_charge_unit: bool = False
    is_ramping_damage: bool = False
    splash_radius: float = 0.0
    aoe_shape: str = "single_target"
    stun_duration: float = 0.0
    slow_percent: float = 0.0
    slow_duration: float = 0.0
    freeze_duration: float = 0.0
    is_champion: bool = False
    is_hero: bool = False
    has_evolution: bool = False
    evolution: Optional[EvolutionData] = None
    projectile: Optional[ProjectileInfo] = None
    active_ability: Optional[AbilityData] = None
    stats_by_level: Dict[str, LevelStats] = field(default_factory=dict)

@dataclass
class CombatResult:
    card_a: str
    card_b: str
    winner: str
    duration_sec: float
    residual_hp_pct: float
    elixir_advantage_for_a: float

@dataclass
class SpellResult:
    spell: str
    target: str
    kills_outright: bool
    leaves_at_one_tower_shot: bool
    remaining_hp: int
    elixir_trade: float

@dataclass
class MatchReviewReport:
    tactical_accuracy_pct: float
    summary: Dict[str, int]
    blunders: List[Dict[str, Any]]
    mistakes: List[Dict[str, Any]]
    inaccuracies: List[Dict[str, Any]]
    leaks: List[Dict[str, Any]]
