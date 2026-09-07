import math
from typing import Dict, List, Optional, Tuple, Any
from .data_loader import get_card
from .physics import ClashPhysicsEngine

class MultiTowerThreatAnalyzer:
    def __init__(self, db: dict):
        self.db = db
        self.towers = {
            "Princess Tower": {"dmg": 109, "hit_speed": 0.8, "range": 7.5, "ground_only": False},
            "Cannoneer": {"dmg": 422, "hit_speed": 2.4, "range": 7.5, "ground_only": False},
            "Dagger Duchess": {"dmg": 119, "hit_speed": 0.35, "range": 7.0, "burst_count": 8, "reload_speed": 1.2, "ground_only": False},
            "Royal Chef": {"dmg": 95, "hit_speed": 1.0, "range": 7.5, "ground_only": False},
            "King Tower": {"dmg": 109, "hit_speed": 1.0, "range": 7.0, "ground_only": False}
        }

    def audit_solo_push_all_towers(self, troop_name: str, proposed_hp: int, orig_hp: int, speed: float, count: int = 1, is_flying: bool = False, jump_range: float = 0.0):
        tower_audit = {}
        for tower_name, tdata in self.towers.items():
            if is_flying and tdata.get("ground_only", False):
                tower_audit[tower_name] = {
                    "orig_connects": True, "new_connects": True,
                    "shots_taken": 0, "status": "Conecta siempre (Torre no ataca aire)"
                }
                continue

            effective_dist = max(1.0, tdata["range"] - jump_range)
            travel_time = effective_dist / max(0.1, speed / 60.0)

            def sim_damage(target_hp):
                hp_pool = target_hp * count
                t, shots = 0.0, 0
                if tower_name == "Dagger Duchess":
                    next_s = 0.0
                    daggers = tdata["burst_count"]
                    while t < travel_time and hp_pool > 0:
                        if t >= next_s:
                            hp_pool -= tdata["dmg"]
                            shots += 1
                            daggers -= 1
                            cadence = tdata["hit_speed"] if daggers > 0 else tdata["reload_speed"]
                            next_s += cadence
                        t += 0.05
                else:
                    shots = math.floor(travel_time / tdata["hit_speed"])
                    hp_pool = max(0, hp_pool - (shots * tdata["dmg"]))
                return (hp_pool > 0), hp_pool, shots

            orig_conn, orig_res, orig_shots = sim_damage(orig_hp)
            new_conn, new_res, new_shots = sim_damage(proposed_hp)

            if orig_conn and not new_conn:
                status = "¡UMBRAL ROTO! Pasa de CONECTAR DAÑO a MORIR EN APROXIMACIÓN"
            elif not orig_conn and new_conn:
                status = "¡UMBRAL ROTO! Pasa de MORIR a CONECTAR DAÑO EN TORRE"
            elif new_conn:
                status = f"Conecta daño ({new_res} HP residual)"
            else:
                status = f"Muere en aproximación ({new_shots} tiros)"

            tower_audit[tower_name] = {
                "orig_connects": orig_conn, "new_connects": new_conn,
                "orig_residual_hp": orig_res, "new_residual_hp": new_res,
                "shots_taken": new_shots, "status": status
            }
        return tower_audit


class MetagameRetentionAdvisor:
    @staticmethod
    def calculate_shannon_entropy(card_usage_probabilities: Dict[str, float]) -> float:
        entropy = 0.0
        for p in card_usage_probabilities.values():
            if p > 0: entropy -= p * math.log2(p)
        return round(entropy, 3)

    @staticmethod
    def evaluate_retention_and_satisfaction(pre_weights: Dict[str, float], post_weights: Dict[str, float], meta_polarization_factor: float = 0.0) -> dict:
        h_pre = -sum(p * math.log2(p) for p in pre_weights.values() if p > 0)
        h_post = -sum(p * math.log2(p) for p in post_weights.values() if p > 0)
        delta_h = round(h_post - h_pre, 3)

        monopoly = [c for c, p in post_weights.items() if p >= 0.30]
        fatigue = min(100.0, max(0.0, ((len(monopoly) * 35.0) + (meta_polarization_factor * 20.0) - (delta_h * 20.0))))

        if fatigue >= 60.0:
            risk = "CRÍTICO (ALTO RIESGO DE ABANDONO)"
            proj = "-5.0% a -10.0% Retención en DAU/MAU"
            rec = "PELIGRO: El cambio centraliza el metajuego en arquetipos hegemónicos. Se proyecta fatiga y frustración en jugadores casuales y competitivos."
        elif fatigue >= 30.0:
            risk = "MODERADO / EN OBSERVACIÓN"
            proj = "-1.5% a +1.0% Retención"
            rec = "Metajuego con polarización localizada. Requiere monitoreo en desafíos de 12 victorias."
        else:
            risk = "EXCELENTE (SALUDABLE)"
            proj = "+2.5% a +6.0% Retención en DAU/MAU"
            rec = "El balance aumenta la entropía del metajuego (diversifica arquetipos viables y contrarresta monopolios). Favorece la satisfacción de los jugadores."

        return {
            "entropy_pre": round(h_pre, 3), "entropy_post": round(h_post, 3), "delta_entropy": delta_h,
            "meta_fatigue_score": round(fatigue, 1), "monopolizing_cards": monopoly,
            "churn_risk_level": risk, "retention_projection": proj, "recommendation": rec
        }


class GameBalanceAuditSuite:
    def __init__(self, physics_engine: ClashPhysicsEngine, meta_weights: dict):
        self.engine = physics_engine
        self.db = physics_engine.db
        self.weights = meta_weights
        self.tower_analyzer = MultiTowerThreatAnalyzer(self.db)
        self.retention_advisor = MetagameRetentionAdvisor()

    def audit_card_proposal(self, card_name: str, stat_to_tune: str, proposed_pct: float, meta_sample: list):
        card = get_card(self.db, card_name)
        if not card: return None

        lvl = "11"
        orig_val = card["stats_by_level"][lvl][stat_to_tune]
        new_val = int(round(orig_val * (1.0 + proposed_pct / 100.0)))
        delta_abs = new_val - orig_val

        spells_benchmark = {
            "Zap": 192, "The Log": 290, "Arrows": 366,
            "Fireball": 689, "Poison": 728, "Lightning": 1054,
            "Rocket": 1484, "Fireball + The Log": 689 + 290
        }

        spell_margins = {}
        if stat_to_tune == "hp":
            for sp_name, sp_dmg in spells_benchmark.items():
                orig_margin = orig_val - sp_dmg
                new_margin = new_val - sp_dmg
                crossed = (orig_margin > 0 and new_margin <= 0)
                spell_margins[sp_name] = {
                    "spell_dmg": sp_dmg, "orig_margin": orig_margin,
                    "new_margin": new_margin, "crossed": crossed
                }

        breakpoint_shifts = []
        if stat_to_tune == "hp":
            for opp_name in meta_sample:
                opp = get_card(self.db, opp_name)
                if not opp or opp["name"] == card["name"]: continue
                dmg_hit = opp["stats_by_level"][lvl]["damage_per_hit"]
                if dmg_hit <= 0: continue

                hits_before = math.ceil(orig_val / dmg_hit)
                hits_after = math.ceil(new_val / dmg_hit)
                hs = opp.get("hit_speed", 1.0)
                time_diff = round((hits_before - hits_after) * hs, 2)

                if hits_before != hits_after:
                    breakpoint_shifts.append({
                        "opponent": opp["name"], "opp_damage": dmg_hit,
                        "hits_before": hits_before, "hits_after": hits_after,
                        "time_saved_sec": time_diff
                    })
        elif stat_to_tune == "damage_per_hit":
            for opp_name in meta_sample:
                opp = get_card(self.db, opp_name)
                if not opp or opp["name"] == card["name"]: continue
                opp_hp = opp["stats_by_level"][lvl]["hp"]
                if opp_hp <= 0: continue

                hits_before = math.ceil(opp_hp / orig_val)
                hits_after = math.ceil(opp_hp / new_val)
                hs = card.get("hit_speed", 1.0)
                time_diff = round((hits_before - hits_after) * hs, 2)

                if hits_before != hits_after:
                    breakpoint_shifts.append({
                        "opponent": opp["name"], "opp_hp": opp_hp,
                        "hits_before": hits_before, "hits_after": hits_after,
                        "time_saved_sec": time_diff
                    })

        # Auditoría frente a las 5 Tropas de Torre en Solitario
        tower_audit = {}
        if stat_to_tune == "hp":
            speed_val = card.get("speed", 60.0)
            count_val = card.get("count", 1)
            is_flying = card.get("is_flying", False)
            jump_r = 2.0 if "Spirit" in card["name"] else 0.0
            tower_audit = self.tower_analyzer.audit_solo_push_all_towers(
                card["name"], proposed_hp=new_val, orig_hp=orig_val,
                speed=speed_val, count=count_val, is_flying=is_flying, jump_range=jump_r
            )

        elasticity_steps = [-5.0, -4.0, -3.0, -2.0, -1.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        sensitivity_table = []
        for step in elasticity_steps:
            val_step = int(round(orig_val * (1.0 + step / 100.0)))
            card["stats_by_level"][lvl][stat_to_tune] = val_step
            diffs = []
            bp_count = 0
            for opp_name in meta_sample:
                opp = get_card(self.db, opp_name)
                if not opp or opp["name"] == card["name"]: continue
                sim = self.engine.simulate_troop_combat(card["name"], opp["name"], with_tower_for_b=True)
                if sim: diffs.append(sim["elixir_advantage_for_a"] * self.weights.get(opp_name, 0.05))
                if stat_to_tune == "hp":
                    dmg = opp["stats_by_level"][lvl]["damage_per_hit"]
                    if dmg > 0 and math.ceil(orig_val / dmg) != math.ceil(val_step / dmg): bp_count += 1

            card["stats_by_level"][lvl][stat_to_tune] = orig_val
            sensitivity_table.append({
                "step_pct": f"{'+' if step > 0 else ''}{step:.1f}%",
                "simulated_val": val_step,
                "weighted_shift": round(sum(diffs), 4),
                "breakpoints_altered": bp_count
            })

        return {
            "card_name": card["name"], "stat": stat_to_tune,
            "proposed_pct": proposed_pct, "original_value": orig_val,
            "new_value": new_val, "delta_absolute": delta_abs,
            "spell_margins": spell_margins, "breakpoint_shifts": breakpoint_shifts,
            "tower_audit": tower_audit, "sensitivity_table": sensitivity_table
        }


class MultiCardPatchSimulator:
    def __init__(self, engine: ClashPhysicsEngine):
        self.engine = engine
        self.db = engine.db

    def simulate_balance_patch(self, patch_dict: dict, meta_roster: list, weights: dict, with_tower: bool = True) -> Dict[str, Any]:
        valid_roster = [c for c in meta_roster if get_card(self.db, c) is not None]
        base_matrix = {}
        for c1 in valid_roster:
            base_matrix[c1] = {}
            for c2 in valid_roster:
                if c1 != c2:
                    base_matrix[c1][c2] = self.engine.simulate_troop_combat(c1, c2, with_tower_for_b=with_tower)

        backups = {}
        for card_name, mods in patch_dict.items():
            card = get_card(self.db, card_name)
            if card:
                c_name = card["name"]
                backups[c_name] = {}
                for stat, pct in mods.items():
                    if stat in card["stats_by_level"]["11"]:
                        orig = card["stats_by_level"]["11"][stat]
                        backups[c_name][stat] = orig
                        card["stats_by_level"]["11"][stat] = int(round(orig * (1.0 + pct / 100.0)))

        post_matrix = {}
        for c1 in valid_roster:
            post_matrix[c1] = {}
            for c2 in valid_roster:
                if c1 != c2:
                    post_matrix[c1][c2] = self.engine.simulate_troop_combat(c1, c2, with_tower_for_b=with_tower)

        for c_name, orig_dict in backups.items():
            card = get_card(self.db, c_name)
            if card:
                for stat, orig in orig_dict.items():
                    card["stats_by_level"]["11"][stat] = orig

        card_reports = {}
        for c1 in valid_roster:
            opps = [c for c in valid_roster if c != c1]
            adv_shifts = []
            flips = []
            for c2 in opps:
                b_res = base_matrix[c1].get(c2)
                p_res = post_matrix[c1].get(c2)
                if b_res and p_res:
                    shift = p_res["elixir_advantage_for_a"] - b_res["elixir_advantage_for_a"]
                    adv_shifts.append(shift * weights.get(c2, 0.05))
                    if b_res["winner"] != p_res["winner"]:
                        flips.append({"opponent": c2, "pre": b_res["winner"], "post": p_res["winner"]})

            weighted_shift = sum(adv_shifts)
            card = get_card(self.db, c1)
            is_direct = any(get_card(self.db, p_name) and get_card(self.db, p_name)["name"] == card["name"] for p_name in patch_dict)
            card_reports[card["name"]] = {
                "weighted_elixir_shift": round(weighted_shift, 4),
                "matchup_flips": flips,
                "is_directly_patched": is_direct
            }
        return card_reports


class AutonomousBalanceOptimizer:
    def __init__(self, physics_engine: ClashPhysicsEngine, meta_weights: dict):
        self.engine = physics_engine
        self.db = physics_engine.db
        self.weights = meta_weights

    def scan_meta_health(self, roster: list) -> Tuple[List[dict], float, float]:
        card_scores = {}
        for c1 in roster:
            card_a = get_card(self.db, c1)
            if not card_a or card_a.get("type") not in ["troop", "hero", "champion"]:
                continue
            opps = [c for c in roster if c != c1 and get_card(self.db, c) and get_card(self.db, c).get("type") in ["troop", "hero", "champion"]]
            elixir_diffs = []
            for c2 in opps:
                res = self.engine.simulate_troop_combat(card_a["name"], c2, with_tower_for_b=True)
                if res:
                    w = self.weights.get(c2, 0.05)
                    elixir_diffs.append(res["elixir_advantage_for_a"] * w)
            card_scores[card_a["name"]] = sum(elixir_diffs) if elixir_diffs else 0.0

        vals = list(card_scores.values())
        mean_val = sum(vals) / len(vals) if vals else 0.0
        variance = sum((v - mean_val) ** 2 for v in vals) / len(vals) if len(vals) > 1 else 0.0
        std_val = math.sqrt(variance)

        watchlist = []
        for c, score in card_scores.items():
            z = (score - mean_val) / std_val if std_val > 0 else 0.0
            if z > 1.2: status = "CRITICAL_NERF"
            elif z > 0.6: status = "MONITOR_NERF"
            elif z < -1.2: status = "CRITICAL_BUFF"
            elif z < -0.6: status = "MONITOR_BUFF"
            else: status = "BALANCED"

            watchlist.append({
                "card": c, "efficiency_score": round(score, 4),
                "z_score": round(z, 2), "status": status
            })
        watchlist.sort(key=lambda x: x["efficiency_score"], reverse=True)
        return watchlist, mean_val, std_val

    def recommend_optimal_tuning(self, target_card: str, stat_to_tune: str, target_eff: float, test_opps: list) -> Optional[dict]:
        card = get_card(self.db, target_card)
        if not card: return None
        orig_val = card["stats_by_level"]["11"][stat_to_tune]

        best_pct = 0.0
        min_dist = float('inf')

        # Acotado a micro-ajustes realistas de Supercell (-6% a +6%)
        for pct_step in [x * 0.5 for x in range(-12, 13)]:
            test_val = int(round(orig_val * (1.0 + pct_step / 100.0)))
            card["stats_by_level"]["11"][stat_to_tune] = test_val

            diffs = []
            for opp in test_opps:
                res = self.engine.simulate_troop_combat(card["name"], opp, with_tower_for_b=True)
                if res: diffs.append(res["elixir_advantage_for_a"] * self.weights.get(opp, 0.05))
            avg_eff = sum(diffs)
            dist = abs(avg_eff - target_eff)
            if dist < min_dist:
                min_dist = dist
                best_pct = pct_step

        card["stats_by_level"]["11"][stat_to_tune] = orig_val
        optimal_val = int(round(orig_val * (1.0 + best_pct / 100.0)))

        breakpoint_warning = None
        if stat_to_tune == "hp" and best_pct < 0:
            if optimal_val < 689 and orig_val >= 689:
                breakpoint_warning = "PELIGRO: El nerf rompe el umbral de Bola de Fuego (morira de 1 golpe directo). Se aconseja limitar a >= 690 HP."
            elif optimal_val <= 109 and orig_val > 109:
                breakpoint_warning = "PELIGRO: La carta pasara a morir de 1 tiro de Torre de la Princesa."

        return {
            "card": card["name"], "stat": stat_to_tune,
            "original_value": orig_val, "optimal_value": optimal_val,
            "recommended_pct": f"{'+' if best_pct > 0 else ''}{best_pct:.1f}%",
            "breakpoint_warning": breakpoint_warning
        }

    def generate_automated_patch_proposal(self, roster: list) -> Tuple[List[dict], List[dict]]:
        watchlist, mean_eff, _ = self.scan_meta_health(roster)
        nerf_candidates = [w for w in watchlist if "NERF" in w["status"]][:3]
        buff_candidates = [w for w in watchlist if "BUFF" in w["status"]][-3:]

        proposals = []
        for item in nerf_candidates:
            c = item["card"]
            rec = self.recommend_optimal_tuning(c, "hp", mean_eff, roster)
            if rec: proposals.append({"card": c, "action": "NERF", "details": rec, "current_z": item["z_score"]})

        for item in buff_candidates:
            c = item["card"]
            rec = self.recommend_optimal_tuning(c, "damage_per_hit", mean_eff, roster)
            if rec: proposals.append({"card": c, "action": "BUFF", "details": rec, "current_z": item["z_score"]})

        return watchlist, proposals

SHARED_SUBUNIT_REGISTRY = {
    "Goblin": {
        "source_cards": ["Goblins", "Goblin Barrel", "Goblin Gang", "Goblin Drill"],
        "base_hp": 202, "base_dmg": 120
    },
    "Spear Goblin": {
        "source_cards": ["Spear Goblins", "Goblin Gang", "Goblin Hut", "Goblin Giant"],
        "base_hp": 133, "base_dmg": 81
    },
    "Skeleton": {
        "source_cards": ["Skeletons", "Skeleton Army", "Tombstone", "Witch", "Graveyard", "Skeleton Barrel", "Skeleton King"],
        "base_hp": 81, "base_dmg": 81
    },
    "Barbarian": {
        "source_cards": ["Barbarians", "Battle Ram", "Barbarian Barrel", "Barbarian Hut"],
        "base_hp": 670, "base_dmg": 192
    },
    "Bat": {
        "source_cards": ["Bats", "Night Witch"],
        "base_hp": 81, "base_dmg": 81
    },
    "Minion": {
        "source_cards": ["Minions", "Minion Horde"],
        "base_hp": 230, "base_dmg": 102
    },
    "Royal Recruit": {
        "source_cards": ["Royal Recruits", "Royal Delivery"],
        "base_hp": 532, "base_dmg": 133
    }
}

class SharedEntityDependencyGraph:
    def __init__(self, db: dict, meta_weights: dict):
        self.db = db
        self.weights = meta_weights
        self.registry = SHARED_SUBUNIT_REGISTRY
        self.card_to_subunits = {}
        for sub_name, data in self.registry.items():
            for c in data["source_cards"]:
                if c not in self.card_to_subunits:
                    self.card_to_subunits[c] = []
                self.card_to_subunits[c].append(sub_name)

    def get_subunit_for_card(self, card_name: str) -> List[str]:
        return self.card_to_subunits.get(card_name, [])

    def audit_shared_entity_ripple(self, target_card_or_subunit: str, stat_to_tune: str, delta_pct: float) -> dict:
        if target_card_or_subunit in self.registry:
            subunit_name = target_card_or_subunit
            origin_card = None
        else:
            subunits = self.get_subunit_for_card(target_card_or_subunit)
            if not subunits:
                return {"is_shared": False, "message": f"'{target_card_or_subunit}' es una tropa independiente (sin sub-tropas compartidas)."}
            subunit_name = subunits[0]
            origin_card = target_card_or_subunit

        sub_info = self.registry[subunit_name]
        siblings = sub_info["source_cards"]
        total_meta_exposure = sum(self.weights.get(c, 0.05) for c in siblings)

        breakdown = []
        for c in siblings:
            c_weight = self.weights.get(c, 0.05)
            breakdown.append({
                "card": c,
                "is_target_origin": (c == origin_card),
                "pick_rate": round(c_weight * 100, 1),
                "role_in_card": f"Invoca a la sub-tropa '{subunit_name}'"
            })

        warning_msg = (
            f"¡ATENCIÓN DE DISEÑO!: Modificar '{subunit_name}' no solo afecta a '{origin_card or subunit_name}', "
            f"sino a una familia de {len(siblings)} cartas que acumula el {round(total_meta_exposure*100, 1)}% de presencia en el metajuego."
        )

        isolated_tuning = None
        if origin_card == "Goblin Barrel":
            isolated_tuning = "Ajustar parámetros propios del barril sin tocar a los Duendes: velocidad de primer golpe tras aterrizar (load_time), coste de elixir o daño de impacto del barril al caer."
        elif origin_card == "Battle Ram":
            isolated_tuning = "Ajustar la vida del tronco de madera del ariete o el daño de embestida sin alterar las estadísticas base de los Bárbaros."
        elif origin_card == "Barbarian Barrel":
            isolated_tuning = "Ajustar el daño de rodada del barril o su alcance en casillas sin modificar a los Bárbaros."
        elif origin_card == "Goblin Drill":
            isolated_tuning = "Ajustar la velocidad de excavación o la frecuencia de aparición periódica sin tocar las stats del Duende."

        return {
            "is_shared": True,
            "subunit_name": subunit_name,
            "origin_card": origin_card,
            "affected_family_cards": siblings,
            "total_meta_exposure_pct": round(total_meta_exposure * 100, 1),
            "family_breakdown": breakdown,
            "warning": warning_msg,
            "isolated_tuning_option": isolated_tuning
        }
