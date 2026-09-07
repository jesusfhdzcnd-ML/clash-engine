import json
import math
import os
import urllib.request
from typing import Dict, List, Optional, Tuple, Any

from .models import CompleteCard, LevelStats, AbilityData, EvolutionData

BASE_URL = "https://royaleapi.github.io/cr-api-data/json"

RARITY_BASE_LEVEL = {
    "common": 1, "rare": 3, "epic": 6, "legendary": 9,
    "champion": 11, "hero": 11, "tower_troop": 11
}

CHAMPIONS_LIST = {
    "Golden Knight", "Archer Queen", "Skeleton King", "Mighty Miner",
    "Monk", "Little Prince", "Goblinstein", "Boss Bandit"
}

SPELL_BASE_DAMAGE = {
    "Fireball": {"11": 689, "14": 913, "15": 1004, "16": 1104},
    "The Log": {"11": 290, "14": 384, "15": 422, "16": 464},
    "Zap": {"11": 192, "14": 254, "15": 279, "16": 307},
    "Arrows": {"11": 366, "14": 486, "15": 534, "16": 588},
    "Rocket": {"11": 1484, "14": 1968, "15": 2165, "16": 2381},
    "Lightning": {"11": 1054, "14": 1397, "15": 1537, "16": 1690},
    "Poison": {"11": 728, "14": 965, "15": 1061, "16": 1167},
    "Giant Snowball": {"11": 192, "14": 254, "15": 279, "16": 307},
    "Earthquake": {"11": 273, "14": 361, "15": 397, "16": 437},
    "Void": {"11": 580, "14": 768, "15": 845, "16": 929},
    "Tornado": {"11": 168, "14": 222, "15": 244, "16": 268},
    "Barbarian Barrel": {"11": 241, "14": 319, "15": 351, "16": 386},
    "Royal Delivery": {"11": 422, "14": 559, "15": 615, "16": 676}
}

ABILITIES_REGISTRY = {
    "Golden Knight": {"ability_name": "Dashing Dash", "elixir_cost": 1, "max_uses_per_deployment": 1, "max_uses": 1, "duration": 0.0, "ability_type": "chain_dash", "special_value": 360, "description": "Embestida en cadena que ataca hasta 10 objetivos."},
    "Archer Queen": {"ability_name": "Cloaking Cape", "elixir_cost": 1, "max_uses_per_deployment": 1, "max_uses": 1, "duration": 3.0, "ability_type": "invisibility_burst_dps", "special_value": 3.0, "description": "Invisibilidad y triplica cadencia."},
    "Skeleton King": {"ability_name": "Soul Summoning", "elixir_cost": 2, "max_uses_per_deployment": 1, "max_uses": 1, "duration": 4.0, "ability_type": "soul_graveyard", "special_value": 16, "description": "Invoca entre 6 y 16 esqueletos."},
    "Mighty Miner": {"ability_name": "Explosive Escape", "elixir_cost": 1, "max_uses_per_deployment": 1, "max_uses": 1, "duration": 0.0, "ability_type": "tunnel_bomb_swap", "special_value": 400, "description": "Bomba de 400 DMG y viaja por tunel."},
    "Monk": {"ability_name": "Pensive Protection", "elixir_cost": 1, "max_uses_per_deployment": 1, "max_uses": 1, "duration": 4.0, "ability_type": "projectile_reflection", "special_value": 80, "description": "Reduce 80% dano y refleja proyectiles."},
    "Little Prince": {"ability_name": "Royal Rescue", "elixir_cost": 3, "max_uses_per_deployment": 1, "max_uses": 1, "duration": 0.0, "ability_type": "summon_guardian", "special_value": 2.5, "description": "Invoca a la Guardiana con empuje."},
    "Goblinstein": {"ability_name": "Lightning Link", "elixir_cost": 2, "max_uses_per_deployment": 1, "max_uses": 1, "duration": 3.0, "ability_type": "chain_lightning_arc", "special_value": 350, "description": "Arco electrico continuo entre Doctor y Monstruo."},
    "Boss Bandit": {"ability_name": "Asalto Veloz", "elixir_cost": 1, "max_uses_per_deployment": 2, "max_uses": 2, "duration": 0.0, "ability_type": "invulnerable_dash", "special_value": 320, "description": "Embestida veloz e invulnerable con 2 usos por despliegue."}
}

HEROES_REGISTRY = {
    "Hero Knight", "Hero Giant", "Hero Goblins", "Hero Balloon", "Hero Mega Minion",
    "Hero Barbarian Barrel", "Hero Magic Archer", "Hero Dark Prince", "Hero Bowler",
    "Hero Tombstone", "Hero Ice Golem", "Hero Wizard", "Hero Mini PEKKA",
    "Hero Musketeer", "Hero Valkyrie", "Hero Berserker", "Hero Ice Wizard"
}

EVOLUTIONS_REGISTRY = {
    "Knight": {"cycles": 1, "ability_name": "Shield Shielding"}, "Skeletons": {"cycles": 2, "ability_name": "Soul Multiplication"},
    "Firecracker": {"cycles": 2, "ability_name": "Spark Shower"}, "Barbarians": {"cycles": 1, "ability_name": "Rage Stacking"},
    "Royal Giant": {"cycles": 1, "ability_name": "Recoil Shockwave"}, "Valkyrie": {"cycles": 2, "ability_name": "Tornado Vortex"},
    "Bomber": {"cycles": 1, "ability_name": "Triple Bounce"}, "Wall Breakers": {"cycles": 1, "ability_name": "Rolling Barrels"},
    "Bats": {"cycles": 2, "ability_name": "Vampiric Bite"}, "Mortar": {"cycles": 2, "ability_name": "Goblin Shell"},
    "Royal Recruits": {"cycles": 1, "ability_name": "Vengeful Charge"}, "Archers": {"cycles": 2, "ability_name": "Power Shot"},
    "Battle Ram": {"cycles": 1, "ability_name": "Juggernaut Charge"}, "Zap": {"cycles": 1, "ability_name": "Triple Stun Wave"},
    "Wizard": {"cycles": 1, "ability_name": "Flame Shield"}, "Goblin Barrel": {"cycles": 2, "ability_name": "Decoy Barrel"},
    "Goblin Giant": {"cycles": 1, "ability_name": "Boiled Goblins"}, "P.E.K.K.A": {"cycles": 1, "ability_name": "Bloodlust Heal"},
    "Mega Knight": {"cycles": 1, "ability_name": "Uppercut Launch"}, "Tesla": {"cycles": 1, "ability_name": "Electro Pulse"},
    "Ice Spirit": {"cycles": 2, "ability_name": "Deep Freeze"}, "Goblin Cage": {"cycles": 1, "ability_name": "Iron Cage Slam"},
    "Goblin Drill": {"cycles": 1, "ability_name": "Subterranean Ambush"}, 
     "Giant Snowball": {"cycles": 1, "ability_name": "Blizzard Frost"},
    "Musketeer": {"cycles": 2, "ability_name": "Sniper Stance"}, "Electro Dragon": {"cycles": 1, "ability_name": "Chain Lightning Surge"},
    "Witch": {"cycles": 1, "ability_name": "Healing Bones"}, "Minion Horde": {"cycles": 1, "ability_name": "Aerial Swarm Shield"},
    "Cannon": {"cycles": 1, "ability_name": "Rapid Fire Barrels"}, "Dart Goblin": {"cycles": 2, "ability_name": "Poison Darts"},
    "Hunter": {"cycles": 1, "ability_name": "Heavy Pellets"}, "Prince": {"cycles": 1, "ability_name": "Unstoppable Lance"},
    "Dark Prince": {"cycles": 1, "ability_name": "Shield Bash Pulse"}, "Rascals": {"cycles": 1, "ability_name": "Gum Shield & Rocket Slings"},
    "Royal Hogs": {"cycles": 1, "ability_name": "Iron Tusks"}, "Flying Machine": {"cycles": 2, "ability_name": "Overclock Rotor"},
    "Fisherman": {"cycles": 1, "ability_name": "Anchor Slam"}, "Magic Archer": {"cycles": 2, "ability_name": "Piercing Aurora"},
    "Lumberjack": {"cycles": 1, "ability_name": "Berserk Aura"}, "Princess": {"cycles": 2, "ability_name": "Volley Rain"},
    "Skeleton Barrel": {"cycles": 2, "ability_name": "Cluster Payload"}, "Royal Ghost": {"cycles": 1, "ability_name": "Spectral Invisibility"}
}

def normalize_card_name(name: str) -> str:
    return str(name or "").lower().replace(".", "").replace("-", "").replace(" ", "")

def get_card(db: dict, name: str) -> Optional[dict]:
    if not name: return None
    if name in db: return db[name]
    clean = normalize_card_name(name)
    for k, v in db.items():
        if normalize_card_name(k) == clean:
            return v
    return None

def resolve_stat(entry: dict, stat_keys: list, target_level: int, rarity_base: int = 1) -> int:
    for k in stat_keys:
        val = entry.get(k)
        if isinstance(val, list) and val:
            if target_level < rarity_base: return 0
            idx = target_level - rarity_base
            return int(val[idx]) if 0 <= idx < len(val) else int(val[-1])
        elif isinstance(val, (int, float)) and val > 0:
            curr = int(val)
            for _ in range(rarity_base, target_level):
                curr = math.floor(curr * 1.1)
            return curr
    return 0

def to_sec(val): v = float(val or 0.0); return round(v / 1000.0, 2) if v > 50 else round(v, 2)
def to_tiles(val): v = float(val or 0.0); return round(v / 1000.0, 2) if v > 50 else round(v, 2)

def inject_tower_troops(db: dict, target_levels=(11, 14, 15, 16)):
    towers = {
        "Princess Tower": {"id": 10000000, "key": "princess-tower", "name": "Princess Tower", "elixir": 0, "type": "tower_troop", "range": 7.5, "hit_speed": 0.8, "attacks_ground": True, "attacks_air": True, "hp": {"11": 3052, "14": 4032, "15": 4446, "16": 4890}, "dmg": {"11": 109, "14": 144, "15": 159, "16": 175}},
        "Cannoneer": {"id": 10000001, "key": "cannoneer", "name": "Cannoneer", "elixir": 0, "type": "tower_troop", "range": 7.5, "hit_speed": 2.4, "attacks_ground": True, "attacks_air": True, "hp": {"11": 2616, "14": 3456, "15": 3811, "16": 4192}, "dmg": {"11": 422, "14": 557, "15": 615, "16": 676}},
        "Dagger Duchess": {"id": 10000002, "key": "dagger-duchess", "name": "Dagger Duchess", "elixir": 0, "type": "tower_troop", "range": 7.0, "hit_speed": 0.35, "attacks_ground": True, "attacks_air": True, "hp": {"11": 3150, "14": 4160, "15": 4589, "16": 5047}, "dmg": {"11": 119, "14": 157, "15": 173, "16": 190}},
        "Royal Chef": {"id": 10000003, "key": "royal-chef", "name": "Royal Chef", "elixir": 0, "type": "tower_troop", "range": 7.5, "hit_speed": 1.0, "attacks_ground": True, "attacks_air": True, "hp": {"11": 3052, "14": 4032, "15": 4446, "16": 4890}, "dmg": {"11": 95, "14": 126, "15": 139, "16": 153}},
        "King Tower": {"id": 10000005, "key": "king-tower", "name": "King Tower", "elixir": 0, "type": "tower_troop", "range": 7.0, "hit_speed": 1.0, "attacks_ground": True, "attacks_air": True, "hp": {"11": 4824, "14": 6408, "15": 7048, "16": 7752}, "dmg": {"11": 109, "14": 144, "15": 159, "16": 175}}
    }
    for t_name, data in towers.items():
        levels_data = {}
        for lvl in target_levels:
            hp_val = data["hp"].get(str(lvl), 0)
            dmg_val = data["dmg"].get(str(lvl), 0)
            levels_data[str(lvl)] = {"hp": hp_val, "damage_per_hit": dmg_val, "damage": dmg_val, "dps": round(dmg_val / data["hit_speed"], 2), "shield_hp": 0, "death_damage": 0, "crown_tower_damage": dmg_val}
        t_entry = {
            "id": data["id"], "key": data["key"], "name": t_name, "elixir": 0, "type": "tower_troop",
            "count": 1, "hit_speed": data["hit_speed"], "load_time": 0.0, "range": data["range"],
            "speed": 0.0, "attacks_ground": data["attacks_ground"], "attacks_air": data["attacks_air"],
            "target_only_buildings": False, "is_flying": False, "splash_radius": 0.0,
            "aoe_shape": "single_target", "stats_by_level": levels_data
        }
        db[t_name] = t_entry
        db[data["key"]] = t_entry
    db["Cocinero Real"] = db["Royal Chef"]
    db["Cocinero"] = db["Royal Chef"]

def build_or_load_canonical_db(cache_path: str = "canonical_cards_db.json", target_levels=(11, 14, 15, 16)) -> Dict[str, dict]:
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                db = json.load(f)
            if "Knight" in db and "Princess Tower" in db:
                return db
        except Exception:
            pass

    canonical_db = {}
    standard_units = [
        {"name": "Knight", "type": "troop", "rarity": "common", "elixir": 3, "hp": 1766, "dmg": 202, "hit_speed": 1.2, "load": 0.2, "range": 1.2, "speed": 60, "count": 1, "aoe": "single_target"},
        {"name": "Mini P.E.K.K.A.", "type": "troop", "rarity": "rare", "elixir": 4, "hp": 1361, "dmg": 757, "hit_speed": 1.6, "load": 0.3, "range": 0.8, "speed": 90, "count": 1, "aoe": "single_target"},
        {"name": "P.E.K.K.A", "type": "troop", "rarity": "epic", "elixir": 7, "hp": 3760, "dmg": 1081, "hit_speed": 1.8, "load": 0.5, "range": 1.2, "speed": 45, "count": 1, "aoe": "single_target"},
        {"name": "Musketeer", "type": "troop", "rarity": "rare", "elixir": 4, "hp": 721, "dmg": 244, "hit_speed": 1.1, "load": 0.3, "range": 6.0, "speed": 60, "attacks_air": True, "count": 1, "aoe": "single_target"},
        {"name": "Valkyrie", "type": "troop", "rarity": "rare", "elixir": 4, "hp": 1907, "dmg": 281, "hit_speed": 1.5, "load": 0.2, "range": 1.2, "speed": 60, "count": 1, "aoe": "circle", "splash": 2.5},
        {"name": "Hog Rider", "type": "troop", "rarity": "rare", "elixir": 4, "hp": 1696, "dmg": 342, "hit_speed": 1.6, "load": 0.3, "range": 1.2, "speed": 120, "count": 1, "buildings_only": True, "aoe": "single_target"},
        {"name": "Wizard", "type": "troop", "rarity": "rare", "elixir": 5, "hp": 755, "dmg": 281, "hit_speed": 1.4, "load": 0.3, "range": 5.5, "speed": 60, "attacks_air": True, "count": 1, "aoe": "circle", "splash": 2.0},
        {"name": "Cannon", "type": "building", "rarity": "common", "elixir": 3, "hp": 896, "dmg": 212, "hit_speed": 0.9, "load": 0.1, "range": 5.5, "count": 1, "aoe": "single_target"},
        {"name": "Tesla", "type": "building", "rarity": "common", "elixir": 4, "hp": 1152, "dmg": 230, "hit_speed": 1.1, "load": 0.1, "range": 5.5, "attacks_air": True, "count": 1, "aoe": "single_target"},
        {"name": "Skeleton Army", "type": "troop", "rarity": "epic", "elixir": 3, "hp": 81, "dmg": 81, "hit_speed": 1.0, "load": 0.0, "range": 0.5, "speed": 90, "count": 15, "aoe": "single_target"},
        {"name": "Skeletons", "type": "troop", "rarity": "common", "elixir": 1, "hp": 81, "dmg": 81, "hit_speed": 1.0, "load": 0.0, "range": 0.5, "speed": 90, "count": 3, "aoe": "single_target"},
        {"name": "Goblins", "type": "troop", "rarity": "common", "elixir": 2, "hp": 202, "dmg": 120, "hit_speed": 1.1, "load": 0.0, "range": 0.5, "speed": 120, "count": 4, "aoe": "single_target"},
        {"name": "Archers", "type": "troop", "rarity": "common", "elixir": 3, "hp": 304, "dmg": 107, "hit_speed": 0.9, "load": 0.1, "range": 5.0, "speed": 60, "attacks_air": True, "count": 2, "aoe": "single_target"},
        {"name": "Dart Goblin", "type": "troop", "rarity": "rare", "elixir": 3, "hp": 260, "dmg": 131, "hit_speed": 0.7, "load": 0.1, "range": 6.5, "speed": 120, "attacks_air": True, "count": 1, "aoe": "single_target"},
        {"name": "Barbarians", "type": "troop", "rarity": "common", "elixir": 5, "hp": 670, "dmg": 192, "hit_speed": 1.3, "load": 0.2, "range": 1.2, "speed": 60, "count": 5, "aoe": "single_target"},
        {"name": "Mega Knight", "type": "troop", "rarity": "legendary", "elixir": 7, "hp": 3713, "dmg": 268, "hit_speed": 1.7, "load": 0.3, "range": 1.2, "speed": 60, "count": 1, "aoe": "circle", "splash": 2.5},
        {"name": "Golden Knight", "type": "champion", "rarity": "champion", "elixir": 4, "hp": 2000, "dmg": 230, "hit_speed": 0.9, "load": 0.2, "range": 1.2, "speed": 60, "count": 1, "aoe": "single_target"},
        {"name": "Goblinstein", "type": "champion", "rarity": "champion", "elixir": 5, "hp": 3200, "dmg": 240, "hit_speed": 1.0, "load": 0.2, "range": 1.2, "speed": 60, "count": 1, "aoe": "single_target"},
        {"name": "Boss Bandit", "type": "champion", "rarity": "champion", "elixir": 4, "hp": 1350, "dmg": 280, "hit_speed": 1.0, "load": 0.2, "range": 1.2, "speed": 60, "count": 1, "aoe": "single_target"},
        {"name": "Fireball", "type": "spell", "rarity": "rare", "elixir": 4, "hp": 0, "dmg": 689},
        {"name": "The Log", "type": "spell", "rarity": "legendary", "elixir": 2, "hp": 0, "dmg": 290},
        {"name": "Zap", "type": "spell", "rarity": "common", "elixir": 2, "hp": 0, "dmg": 192},
        {"name": "Arrows", "type": "spell", "rarity": "common", "elixir": 3, "hp": 0, "dmg": 366},
        {"name": "Rocket", "type": "spell", "rarity": "rare", "elixir": 6, "hp": 0, "dmg": 1484},
        {"name": "Poison", "type": "spell", "rarity": "epic", "elixir": 4, "hp": 0, "dmg": 728},
        {"name": "Goblin Barrel", "type": "troop", "rarity": "epic", "elixir": 3, "hp": 202, "dmg": 120, "hit_speed": 1.1, "load": 0.0, "range": 0.5, "speed": 90, "count": 3, "aoe": "single_target"}
    ]

    for u in standard_units:
        name = u["name"]
        card_type = u["type"]
        rarity = u["rarity"]
        elixir = u["elixir"]
        hp = u.get("hp", 0)
        dmg = u.get("dmg", 0)
        hs = u.get("hit_speed", 1.0)
        count = u.get("count", 1)

        levels_data = {}
        for lvl in target_levels:
            curr_hp = hp
            curr_dmg = dmg
            diff_lvl = lvl - 11
            if diff_lvl > 0:
                for _ in range(diff_lvl):
                    curr_hp = math.floor(curr_hp * 1.1)
                    curr_dmg = math.floor(curr_dmg * 1.1)
            levels_data[str(lvl)] = {
                "hp": curr_hp, "damage_per_hit": curr_dmg, "damage": curr_dmg,
                "dps": round((curr_dmg / hs) * count, 2) if hs > 0 else 0.0,
                "shield_hp": 0
            }

        ab_data = ABILITIES_REGISTRY.get(name)
        card_entry = {
            "id": 26000000, "key": normalize_card_name(name), "name": name, "elixir": elixir,
            "type": card_type, "rarity": rarity, "role": "support", "count": count,
            "hit_speed": hs, "load_time": u.get("load", 0.0), "range": u.get("range", 0.0),
            "speed": u.get("speed", 0.0), "sight_range": 5.5,
            "attacks_ground": True, "attacks_air": u.get("attacks_air", False),
            "target_only_buildings": u.get("buildings_only", False),
            "is_flying": False, "splash_radius": u.get("splash", 0.0),
            "aoe_shape": u.get("aoe", "single_target"),
            "is_champion": name in CHAMPIONS_LIST,
            "is_hero": name in HEROES_REGISTRY,
            "has_evolution": name in EVOLUTIONS_REGISTRY,
            "active_ability": ab_data,
            "stats_by_level": levels_data
        }
        canonical_db[name] = card_entry
        canonical_db[card_entry["key"]] = card_entry
        canonical_db[name.replace(".", "")] = card_entry
        canonical_db[name.rstrip(".")] = card_entry

    if "Boss Bandit" in canonical_db:
        canonical_db["Bandida Líder"] = canonical_db["Boss Bandit"]

    for h_name in HEROES_REGISTRY:
        if h_name not in canonical_db:
            canonical_db[h_name] = {
                "id": 26000000, "key": normalize_card_name(h_name), "name": h_name, "elixir": 4,
                "type": "hero", "rarity": "hero", "is_hero": True,
                "active_ability": {"ability_name": f"Habilidad {h_name}", "elixir_cost": 2, "max_uses_per_deployment": 1},
                "stats_by_level": {"11": {"hp": 1800, "damage_per_hit": 220, "dps": 180.0, "shield_hp": 0}}
            }

    inject_tower_troops(canonical_db, target_levels)

    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(canonical_db, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return canonical_db
