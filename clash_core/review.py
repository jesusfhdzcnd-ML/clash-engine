import math
from typing import Dict, List, Optional, Tuple, Any
from .data_loader import get_card
from .physics import ClashPhysicsEngine

class ClashMatchReviewer:
    def __init__(self, physics_engine: ClashPhysicsEngine):
        self.engine = physics_engine
        self.db = physics_engine.db

    def analyze_match(self, match_data: dict) -> dict:
        events = match_data.get("events", [])
        leak_records = []
        blunders = []
        mistakes = []
        inaccuracies = []
        brilliant_moves = []
        good_moves = []

        total_evaluations = 0
        total_penalty = 0.0

        for ev in events:
            if ev.get("player") != "user": continue
            total_evaluations += 1

            card_name = ev.get("card")
            t = ev.get("time", 0.0)
            hand = ev.get("hand", [])
            target_enemy = ev.get("target_attacker")
            tile = ev.get("tile", (9, 14))

            # 1. Fuga de Elixir
            time_at_cap = ev.get("seconds_at_cap", 0.0)
            if time_at_cap > 1.0:
                elixir_rate = 1.0 / 1.4 if t >= 120.0 else 1.0 / 2.8
                leaked_elixir = round(time_at_cap * elixir_rate, 2)
                leak_records.append({"time": t, "seconds_at_cap": time_at_cap, "leaked_elixir": leaked_elixir})
                if leaked_elixir >= 2.0: total_penalty += 8.0
                elif leaked_elixir >= 1.0: total_penalty += 4.0

            # 2. Posicionamiento Espacial (Sight Range de 5.5 casillas)
            if target_enemy:
                enemy_card = get_card(self.db, target_enemy)
                played_card = get_card(self.db, card_name)
                if enemy_card and enemy_card.get("target_only_buildings") and played_card and played_card.get("type") == "building":
                    enemy_x = ev.get("enemy_lane_x", 3.5)
                    structure_x, structure_y = tile
                    dist = math.sqrt((structure_x - enemy_x)**2 + (structure_y - 16.0)**2)
                    if dist > 5.5:
                        blunders.append({
                            "time": t, "type": "PLACEMENT_BLUNDER", "card_played": played_card["name"],
                            "enemy_troop": enemy_card["name"], "distance": round(dist, 2),
                            "description": f"Estructura colocada a {round(dist, 1)} casillas (fuera del radio de atraccion de 5.5). El {enemy_card['name']} ignoro el {played_card['name']} e impacto en la torre."
                        })
                        total_penalty += 12.0
                        continue

            # 3. Intercambio Tactico vs Mano
            if target_enemy:
                sim_actual = self.engine.simulate_troop_combat(card_name, target_enemy, with_tower_for_b=True)
                adv_actual = sim_actual["elixir_advantage_for_a"] if sim_actual else 0.0

                best_hand_card = card_name
                best_hand_adv = adv_actual

                for alt_card in hand:
                    c_alt = get_card(self.db, alt_card)
                    if not c_alt or c_alt["name"] == (get_card(self.db, card_name) or {}).get("name"):
                        continue
                    if c_alt.get("type") in ["troop", "hero", "champion"]:
                        sim_alt = self.engine.simulate_troop_combat(c_alt["name"], target_enemy, with_tower_for_b=True)
                        if sim_alt and sim_alt["elixir_advantage_for_a"] > best_hand_adv:
                            best_hand_adv = sim_alt["elixir_advantage_for_a"]
                            best_hand_card = c_alt["name"]
                    elif c_alt.get("type") == "spell":
                        spell_alt = self.engine.simulate_spell(c_alt["name"], target_enemy)
                        if spell_alt and spell_alt["elixir_trade"] > best_hand_adv:
                            best_hand_adv = spell_alt["elixir_trade"]
                            best_hand_card = c_alt["name"]

                lost_value = round(best_hand_adv - adv_actual, 2)
                if lost_value >= 2.5:
                    blunders.append({
                        "time": t, "type": "TRADE_BLUNDER", "card_played": card_name,
                        "optimal_card": best_hand_card, "against": target_enemy, "lost_value": lost_value,
                        "description": f"Jugaste '{card_name}' perdiendo {lost_value} gotas de valor relativo. La jugada optima disponible era '{best_hand_card}'."
                    })
                    total_penalty += 10.0
                elif lost_value >= 1.5:
                    mistakes.append({
                        "time": t, "type": "MISTAKE", "card_played": card_name,
                        "optimal_card": best_hand_card, "against": target_enemy, "lost_value": lost_value,
                        "description": f"Intercambio desfavorable con '{card_name}' (-{lost_value} gotas). '{best_hand_card}' ofrecia mejor control."
                    })
                    total_penalty += 5.0
                elif lost_value >= 0.8:
                    inaccuracies.append({
                        "time": t, "type": "INACCURACY", "card_played": card_name,
                        "optimal_card": best_hand_card, "against": target_enemy, "lost_value": lost_value,
                        "description": f"Imprecision leve: '{best_hand_card}' ahorraba {lost_value} gotas de elixir."
                    })
                    total_penalty += 2.0
                else:
                    if adv_actual >= 1.5:
                        brilliant_moves.append({"time": t, "card": card_name, "against": target_enemy, "advantage": adv_actual})
                    else:
                        good_moves.append({"time": t, "card": card_name})

        raw_acc = 100.0 - (total_penalty / max(1, total_evaluations)) * 6.5
        tactical_accuracy = round(max(20.0, min(99.0, raw_acc)), 1)

        return {
            "tactical_accuracy_pct": tactical_accuracy,
            "summary": {
                "total_decisiones": total_evaluations,
                "brilliant_moves": len(brilliant_moves),
                "good_moves": len(good_moves),
                "inaccuracies": len(inaccuracies),
                "mistakes": len(mistakes),
                "blunders": len(blunders),
                "elixir_leaks": len(leak_records)
            },
            "blunders": blunders, "mistakes": mistakes,
            "inaccuracies": inaccuracies, "brilliant_moves": brilliant_moves,
            "leaks": leak_records
        }
