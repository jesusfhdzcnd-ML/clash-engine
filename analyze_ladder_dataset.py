"""
Script Analizador de Partidas del Top Ladder y Auditor de Fallos Tácticos
------------------------------------------------------------------------
Procesa partidas competitivas para calcular:
1. Precisión Táctica Promedio (Accuracy %) estilo Chess.com.
2. Tasa de Blunders de Intercambio (Trade Blunders) frente a la mano disponible.
3. Fallos Espaciales de Radio de Atracción (Sight Range de 5.5 casillas).
4. Fugas de Elixir acumuladas (Elixir Leaking).
5. Auditoría de Emparejamiento (Ventaja Teórica vs Resultado Real / Execution Blunders).
"""

import os
import sys
import json
import math
from typing import Dict, List, Tuple, Any

# Agregar directorio raíz para importar clash_core
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from clash_core import (
    build_or_load_canonical_db, get_card, ClashPhysicsEngine, ClashMatchReviewer
)

def generate_mock_ladder_battles(count: int = 50) -> List[dict]:
    """Genera un dataset representativo con escenarios competitivos y errores reales."""
    archetypes = [
        {
            "name": "2.6 Hog Cycle",
            "deck": ["Hog Rider", "Cannon", "Musketeer", "Skeletons", "Ice Spirit", "The Log", "Fireball", "Knight"],
            "tower": "Princess Tower"
        },
        {
            "name": "Log Bait",
            "deck": ["Goblin Barrel", "Knight", "Princess", "Goblin Gang", "The Log", "Rocket", "Ice Spirit", "Dart Goblin"],
            "tower": "Princess Tower"
        },
        {
            "name": "Pekka Bridge Spam",
            "deck": ["P.E.K.K.A", "Bandit", "Royal Ghost", "Zap", "Poison", "Battle Ram", "Magic Archer", "Dark Prince"],
            "tower": "Cannoneer"
        },
        {
            "name": "Mega Knight Wall Breakers",
            "deck": ["Mega Knight", "Wall Breakers", "Miner", "Musketeer", "Bats", "Zap", "Barbarian Barrel", "Goblins"],
            "tower": "Dagger Duchess"
        },
        {
            "name": "Golem Beatdown",
            "deck": ["Golem", "Night Witch", "Baby Dragon", "Lightning", "Tornado", "Mega Minion", "Barbarian Barrel", "Lumberjack"],
            "tower": "Princess Tower"
        }
    ]

    battles = []
    for i in range(count):
        deck_a = archetypes[i % len(archetypes)]
        deck_b = archetypes[(i + 1) % len(archetypes)]

        events = []
        # Evento 1: Defensa contra condición de victoria
        if i % 3 == 0:
            # Placement Blunder: Coloca Cañón fuera de las 5.5 casillas del carril del Montapuercos
            events.append({
                "time": 28.0 + (i % 5), "player": "user",
                "card": "Cannon", "tile": (12.0, 10.0), "enemy_lane_x": 3.5,
                "hand": ["Cannon", "The Log", "Knight", "Musketeer"],
                "target_attacker": "Hog Rider"
            })
        else:
            # Buena colocación defensiva
            events.append({
                "time": 28.0 + (i % 5), "player": "user",
                "card": "Cannon" if "Cannon" in deck_a["deck"] else "Knight",
                "tile": (9.0, 14.0), "enemy_lane_x": 3.5,
                "hand": deck_a["deck"][:4],
                "target_attacker": "Hog Rider" if "Hog Rider" in deck_b["deck"] else deck_b["deck"][0]
            })

        # Evento 2: Respuesta táctica (Trade blunder intencional en 35% de partidas)
        if i % 4 == 1:
            events.append({
                "time": 65.0 + (i % 10), "player": "user",
                "card": "P.E.K.K.A",
                "hand": ["P.E.K.K.A", "The Log", "Knight", "Cannon"],
                "target_attacker": "Goblin Barrel"
            })
        else:
            events.append({
                "time": 65.0 + (i % 10), "player": "user",
                "card": "The Log" if "The Log" in deck_a["deck"] else deck_a["deck"][1],
                "hand": deck_a["deck"][1:5],
                "target_attacker": "Goblin Barrel" if "Goblin Barrel" in deck_b["deck"] else deck_b["deck"][1]
            })

        # Evento 3: Fuga de Elixir
        events.append({
            "time": 115.0 + (i % 15), "player": "user",
            "card": deck_a["deck"][2],
            "hand": deck_a["deck"][2:6],
            "seconds_at_cap": 3.2 if i % 2 == 0 else 0.4
        })

        battles.append({
            "battle_id": f"battle_{i+1:04d}",
            "archetype_a": deck_a["name"],
            "archetype_b": deck_b["name"],
            "player_deck": deck_a["deck"],
            "player_tower": deck_a["tower"],
            "opponent_deck": deck_b["deck"],
            "opponent_tower": deck_b["tower"],
            "player_crowns": 2 if i % 2 == 0 else 0,
            "opponent_crowns": 1 if i % 2 == 0 else 2,
            "result": "WIN" if i % 2 == 0 else "LOSS",
            "events": events
        })

    return battles

class LadderBatchAnalyzer:
    def __init__(self, db: dict):
        self.db = db
        self.physics = ClashPhysicsEngine(db)
        self.reviewer = ClashMatchReviewer(self.physics)

    def evaluate_matchup_advantage(self, deck_a: list, deck_b: list) -> float:
        """Calcula la ventaja teórica de elixir par a par entre dos mazos de 8 cartas."""
        total_trade = 0.0
        comparisons = 0
        for ca in deck_a:
            for cb in deck_b:
                card_obj_a = get_card(self.db, ca)
                card_obj_b = get_card(self.db, cb)
                if not card_obj_a or not card_obj_b: continue
                # Si son tropas
                if card_obj_a.get("type") in ["troop", "hero", "champion"] and card_obj_b.get("type") in ["troop", "hero", "champion"]:
                    res = self.physics.simulate_two_way_interaction(ca, cb)
                    if res:
                        total_trade += res["net_elixir_advantage"]
                        comparisons += 1
                # Si A es hechizo
                elif card_obj_a.get("type") == "spell" and card_obj_b.get("type") in ["troop", "hero", "champion"]:
                    sp = self.physics.simulate_spell(ca, cb)
                    if sp:
                        total_trade += sp["elixir_trade"]
                        comparisons += 1
        return round(total_trade / max(1, comparisons), 3)

    def process_dataset(self, battles: List[dict]) -> dict:
        total_matches = len(battles)
        accuracies = []
        all_blunders = []
        all_mistakes = []
        all_leaks = []
        
        execution_blunders = []
        outplays = []
        
        blunders_by_type = {}
        blunders_by_card = {}

        for b in battles:
            # 1. Auditoría Micro (Game Review de eventos)
            review = self.reviewer.analyze_match(b)
            acc = review["tactical_accuracy_pct"]
            accuracies.append(acc)

            for bl in review["blunders"]:
                all_blunders.append(bl)
                btype = bl.get("type", "UNKNOWN")
                blunders_by_type[btype] = blunders_by_type.get(btype, 0) + 1
                cname = bl.get("card_played", "Unknown")
                blunders_by_card[cname] = blunders_by_card.get(cname, 0) + 1

            for m in review["mistakes"]:
                all_mistakes.append(m)

            for lk in review["leaks"]:
                all_leaks.append(lk)

            # 2. Auditoría Macro (Matchup Teórico vs Resultado Real)
            deck_a = b.get("player_deck", [])
            deck_b = b.get("opponent_deck", [])
            result = b.get("result", "WIN")
            adv = self.evaluate_matchup_advantage(deck_a, deck_b)

            # Si tenía ventaja teórica clara (+0.3 por cruce) pero perdió: Execution Blunder
            if adv >= 0.25 and result == "LOSS":
                execution_blunders.append({
                    "battle_id": b.get("battle_id", "N/A"),
                    "theoretical_advantage": adv,
                    "deck": deck_a, "opponent_deck": deck_b
                })
            # Si tenía desventaja teórica severa (-0.25) pero ganó: Outplay
            elif adv <= -0.25 and result == "WIN":
                outplays.append({
                    "battle_id": b.get("battle_id", "N/A"),
                    "theoretical_advantage": adv,
                    "deck": deck_a, "opponent_deck": deck_b
                })

        avg_accuracy = round(sum(accuracies) / max(1, len(accuracies)), 2)
        avg_leaks_per_match = round(len(all_leaks) / max(1, total_matches), 2)
        total_leaked_elixir = round(sum(l.get("leaked_elixir", 0.0) for l in all_leaks), 1)

        return {
            "total_matches_analyzed": total_matches,
            "average_tactical_accuracy": avg_accuracy,
            "total_blunders_detected": len(all_blunders),
            "total_mistakes_detected": len(all_mistakes),
            "total_elixir_leaks": len(all_leaks),
            "total_elixir_wasted_in_leaks": total_leaked_elixir,
            "average_leaks_per_match": avg_leaks_per_match,
            "blunders_by_category": blunders_by_type,
            "top_blunder_cards": sorted(blunders_by_card.items(), key=lambda x: x[1], reverse=True)[:5],
            "execution_blunders_count": len(execution_blunders),
            "outplay_wins_count": len(outplays),
            "sample_execution_blunders": execution_blunders[:3],
            "sample_outplays": outplays[:3]
        }

def main():
    print("==================================================================")
    print("    AUDITOR TÁCTICO EN LOTE: TELEMETRÍA DE TOP LADDER & BLUNDERS ")
    print("==================================================================\n")

    # 1. Cargar base de datos canónica
    print("[1/3] Cargando motor canónico...")
    db = build_or_load_canonical_db()
    analyzer = LadderBatchAnalyzer(db)

    # 2. Cargar o generar partidas reales
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_file = os.path.join(base_dir, "top_ladder_battles.json")
    if os.path.exists(dataset_file):
        print(f"[2/3] Cargando dataset real desde '{dataset_file}'...")
        with open(dataset_file, "r", encoding="utf-8") as f:
            battles = json.load(f)
        print(f"      -> {len(battles)} partidas reales cargadas.")
    else:
        print("[2/3] No se detectó 'top_ladder_battles.json' local.")
        print("      Generando muestra representativa de 50 partidas competitivas...")
        battles = generate_mock_ladder_battles(count=50)

    # 3. Procesar dataset en lote
    print("\n[3/3] Procesando y auditando partidas con el motor de físicas...")
    report = analyzer.process_dataset(battles)

    # Mostrar reporte ejecutivo
    print("\n" + "=" * 66)
    print("               INFORME EJECUTIVO DE AUDITORÍA TÁCTICA              ")
    print("=" * 66)
    print(f"Partidas Analizadas              : {report['total_matches_analyzed']}")
    print(f"Precisión Táctica Promedio (Meta) : {report['average_tactical_accuracy']}%")
    print(f"Total Errores Graves (Blunders)   : {report['total_blunders_detected']}")
    print(f"Total Errores Menores (Mistakes)  : {report['total_mistakes_detected']}")
    print(f"Fugas de Elixir Detectadas        : {report['total_elixir_leaks']} ({report['total_elixir_wasted_in_leaks']} gotas totales desperdiciadas)")
    print(f"Fugas Promedio por Partida        : {report['average_leaks_per_match']} fugas/partida")
    print(f"Partidas con 'Execution Blunder'  : {report['execution_blunders_count']} (Matchups ganados en papel que se perdieron)")
    print(f"Victorias por 'Outplay'           : {report['outplay_wins_count']} (Matchups desfavorables superados)")

    print("\n--- DESGLOSE DE BLUNDERS POR CATEGORÍA ---")
    for btype, cnt in report["blunders_by_category"].items():
        print(f"   * {btype:<25}: {cnt} ocurrencias")

    if report["top_blunder_cards"]:
        print("\n--- TOP CARTAS ASOCIADAS A BLUNDERS ---")
        for cname, cnt in report["top_blunder_cards"]:
            print(f"   * {cname:<20}: {cnt} fallos registrados")

    # Guardar informe en archivo JSON
    output_report_file = os.path.join(base_dir, "ladder_tactical_audit_report.json")
    with open(output_report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[✓] Informe técnico exportado exitosamente a '{output_report_file}'.")

if __name__ == "__main__":
    main()
