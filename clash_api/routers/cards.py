from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from clash_core import build_or_load_canonical_db, get_card, ClashPhysicsEngine
from ..schemas import CardStatsResponse

router = APIRouter(prefix="/api/v1/cards", tags=["Cards & Breakpoints"])

db = build_or_load_canonical_db()
physics = ClashPhysicsEngine(db)

@router.get("/", response_model=List[Dict[str, Any]])
def list_cards_endpoint():
    """Lista todas las cartas registradas en el catalogo canonico con elixir, tipo y rareza."""
    seen = set()
    cards_list = []
    for k, c in db.items():
        if isinstance(c, dict) and c.get("name") and c["name"] not in seen:
            seen.add(c["name"])
            cards_list.append({
                "name": c["name"],
                "type": c.get("type", "troop"),
                "rarity": c.get("rarity", "common"),
                "elixir": c.get("elixir", 0),
                "is_champion": c.get("is_champion", False),
                "is_hero": c.get("is_hero", False),
                "has_evolution": c.get("has_evolution", False)
            })
    cards_list.sort(key=lambda x: x["name"])
    return cards_list

@router.get("/{card_name}", response_model=CardStatsResponse)
def get_card_stats_endpoint(card_name: str, level: int = 11):
    """
    Devuelve la ficha tecnica canonica oficial de una carta para un nivel dado (por defecto 11),
    incluyendo sus puntos de quiebre exactos frente a los principales hechizos del juego.
    """
    card = get_card(db, card_name)
    if not card:
        raise HTTPException(status_code=404, detail=f"Carta '{card_name}' no encontrada en la base canónica.")
        
    lvl_str = str(level)
    st = card.get("stats_by_level", {}).get(lvl_str, {})
    
    # Evaluar interacciones con hechizos si es tropa con vida
    spell_inter = {}
    if st.get("hp", 0) > 0:
        spells_to_test = ["Fireball", "The Log", "Zap", "Arrows", "Rocket", "Lightning", "Poison"]
        for sp in spells_to_test:
            res = physics.simulate_spell(sp, card["name"], level=level)
            if res:
                if res["kills_outright"]:
                    verdict = "ELIMINACION DIRECTA (One-shot kill)"
                elif res["leaves_at_one_tower_shot"]:
                    verdict = f"1 TIRO DE TORRE ({res['remaining_hp']} HP restante)"
                else:
                    verdict = f"SOBREVIVE ({res['remaining_hp']} HP restante)"
                spell_inter[sp] = verdict

    return CardStatsResponse(
        name=card["name"],
        type=card.get("type", "troop"),
        rarity=card.get("rarity", "common"),
        elixir=card.get("elixir", 0),
        hp=st.get("hp", 0),
        damage_per_hit=st.get("damage_per_hit", 0),
        dps=st.get("dps", 0.0),
        hit_speed=card.get("hit_speed", 0.0),
        range=card.get("range", 0.0),
        speed=card.get("speed", 0.0),
        aoe_shape=card.get("aoe_shape", "single_target"),
        is_champion=card.get("is_champion", False),
        is_hero=card.get("is_hero", False),
        has_evolution=card.get("has_evolution", False),
        spell_interactions=spell_inter if spell_inter else None
    )
