import math
from typing import Dict, List, Optional, Tuple

from .data_loader import get_card

class ClashPhysicsEngine:
    def __init__(self, db: dict):
        self.db = db

    def simulate_troop_combat(self, card_a_name: str, card_b_name: str, level: int = 11, with_tower_for_b: bool = False, tower_type: str = "Princess Tower") -> Optional[dict]:
        card_a = get_card(self.db, card_a_name)
        card_b = get_card(self.db, card_b_name)
        if not card_a or not card_b: return None

        lvl_str = str(level)
        st_a = card_a["stats_by_level"][lvl_str]
        st_b = card_b["stats_by_level"][lvl_str]
        if st_a["hp"] <= 0 or st_b["hp"] <= 0: return None

        count_a = card_a.get("count", 1)
        count_b = card_b.get("count", 1)
        is_aoe_a = card_a.get("aoe_shape", "single_target") != "single_target" or card_a.get("splash_radius", 0) > 0
        is_aoe_b = card_b.get("aoe_shape", "single_target") != "single_target" or card_b.get("splash_radius", 0) > 0

        can_a_hit_b = (card_a.get("attacks_air", False) if card_b.get("is_flying", False) else card_a.get("attacks_ground", True)) and not card_a.get("target_only_buildings", False)
        can_b_hit_a = (card_b.get("attacks_air", False) if card_a.get("is_flying", False) else card_b.get("attacks_ground", True)) and not card_b.get("target_only_buildings", False)

        hp_unit_a, shield_a = st_a["hp"], st_a.get("shield_hp", 0)
        hp_unit_b, shield_b = st_b["hp"], st_b.get("shield_hp", 0)
        alive_a, alive_b = count_a, count_b
        dmg_a, dmg_b = st_a["damage_per_hit"], st_b["damage_per_hit"]
        hs_a, hs_b = card_a.get("hit_speed", 1.0) or 1.0, card_b.get("hit_speed", 1.0) or 1.0

        approach_a = round(max(0.0, card_b.get("range", 0.0) - card_a.get("range", 0.0)) / (card_a.get("speed", 60.0) / 60.0), 2) if card_a.get("speed", 60.0) > 0 else 0.0
        approach_b = round(max(0.0, card_a.get("range", 0.0) - card_b.get("range", 0.0)) / (card_b.get("speed", 60.0) / 60.0), 2) if card_b.get("speed", 60.0) > 0 else 0.0
        next_hit_a = approach_a + card_a.get("load_time", 0.0)
        next_hit_b = approach_b + card_b.get("load_time", 0.0)

        t_entry = get_card(self.db, tower_type) or {}
        tower_dmg = t_entry.get("stats_by_level", {}).get(lvl_str, {}).get("damage_per_hit", 109) if with_tower_for_b else 0
        tower_cadence = t_entry.get("hit_speed", 0.8)

        curr_hp_a, curr_hp_b = hp_unit_a, hp_unit_b
        t, dt, next_tower = 0.0, 0.05, 0.0

        while alive_a > 0 and alive_b > 0 and t < 40.0:
            if can_a_hit_b and t >= next_hit_a:
                if shield_b > 0:
                    shield_b = max(0, shield_b - dmg_a)
                else:
                    total_a = dmg_a * alive_a
                    if is_aoe_a:
                        curr_hp_b -= total_a
                        if curr_hp_b <= 0: alive_b = 0
                    else:
                        curr_hp_b -= dmg_a
                        if curr_hp_b <= 0:
                            alive_b -= 1
                            curr_hp_b = hp_unit_b
                next_hit_a += hs_a

            if can_b_hit_a and t >= next_hit_b:
                if shield_a > 0:
                    shield_a = max(0, shield_a - dmg_b)
                else:
                    total_b = dmg_b * alive_b
                    if is_aoe_b:
                        curr_hp_a -= total_b
                        if curr_hp_a <= 0: alive_a = 0
                    else:
                        curr_hp_a -= dmg_b
                        if curr_hp_a <= 0:
                            alive_a -= 1
                            curr_hp_a = hp_unit_a
                next_hit_b += hs_b

            if with_tower_for_b and t >= next_tower and alive_a > 0:
                if shield_a > 0:
                    shield_a = max(0, shield_a - tower_dmg)
                else:
                    curr_hp_a -= tower_dmg
                    if curr_hp_a <= 0:
                        alive_a -= 1
                        curr_hp_a = hp_unit_a
                next_tower += tower_cadence
            t += dt

        winner = card_a["name"] if alive_a > 0 and alive_b <= 0 else (card_b["name"] if alive_b > 0 and alive_a <= 0 else "Empate")
        cost_a, cost_b = card_a["elixir"], card_b["elixir"]

        if winner == card_a["name"]:
            res_ratio_a = (alive_a / count_a) * (max(0, curr_hp_a) / hp_unit_a)
            adv_a = cost_b - cost_a * (1.0 - res_ratio_a)
            res_pct = round(res_ratio_a * 100, 1)
        elif winner == card_b["name"]:
            res_ratio_b = (alive_b / count_b) * (max(0, curr_hp_b) / hp_unit_b)
            damage_ratio_dealt = 1.0 - res_ratio_b
            adv_a = cost_b * damage_ratio_dealt - cost_a
            res_pct = round(res_ratio_b * 100, 1)
        else:
            adv_a = 0.0
            res_pct = 0.0

        return {
            "card_a": card_a["name"], "card_b": card_b["name"], "winner": winner,
            "duration_sec": round(t, 2), "residual_hp_pct": res_pct,
            "elixir_advantage_for_a": round(adv_a, 2)
        }

    def simulate_spell(self, spell_name: str, target_name: str, level: int = 11) -> Optional[dict]:
        spell = get_card(self.db, spell_name)
        target = get_card(self.db, target_name)
        if not spell or not target: return None
        lvl = str(level)
        st_spell = spell["stats_by_level"][lvl]
        st_tgt = target["stats_by_level"][lvl]
        if st_tgt["hp"] <= 0: return None

        dmg = st_spell["damage_per_hit"]
        hp = st_tgt["hp"]
        shield = st_tgt.get("shield_hp", 0)

        if shield > 0:
            remaining_hp = hp
            kills_outright = False
        else:
            remaining_hp = max(0, hp - dmg)
            kills_outright = (remaining_hp == 0)

        leaves_at_one_tower_shot = (0 < remaining_hp <= 109)
        cost_spell = spell["elixir"]
        cost_target = target["elixir"]
        if kills_outright:
            trade = cost_target - cost_spell
        else:
            trade = cost_target * ((hp - remaining_hp) / hp) - cost_spell

        return {
            "spell": spell["name"], "target": target["name"],
            "kills_outright": kills_outright,
            "leaves_at_one_tower_shot": leaves_at_one_tower_shot,
            "remaining_hp": remaining_hp,
            "elixir_trade": round(trade, 2)
        }

    def simulate_two_way_interaction(self, card_a_name: str, card_b_name: str, level: int = 11) -> Optional[dict]:
        card_a = get_card(self.db, card_a_name)
        card_b = get_card(self.db, card_b_name)
        if not card_a or not card_b: return None

        sim_attack = self.simulate_troop_combat(card_a["name"], card_b["name"], level=level, with_tower_for_b=True)
        sim_defend = self.simulate_troop_combat(card_b["name"], card_a["name"], level=level, with_tower_for_b=True)
        if not sim_attack or not sim_defend: return None

        adv_attack = sim_attack["elixir_advantage_for_a"]
        adv_defense = -sim_defend["elixir_advantage_for_a"]
        net_adv = round(0.5 * adv_attack + 0.5 * adv_defense, 3)

        return {
            "card_a": card_a["name"], "card_b": card_b["name"],
            "net_elixir_advantage": net_adv,
            "advantage_as_attacker": adv_attack,
            "advantage_as_defender": adv_defense
        }
