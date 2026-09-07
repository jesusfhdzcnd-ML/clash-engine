"""
Demostración Interactiva del Motor `clash_core`.
Ejecuta los dos pilares:
1. Soporte a la Decisión de Balance (Simulador Multi-Carta + Optimizador de Watchlist).
2. Revisor Táctico de Partidas (Chess.com Game Review con detección de Blunders y Fugas).
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from clash_core import (
    build_or_load_canonical_db, ClashPhysicsEngine,
    MultiCardPatchSimulator, AutonomousBalanceOptimizer, ClashMatchReviewer
)

def main():
    print("==================================================================")
    print("      CLASH ROYALE CORE ANALYTICS & GAME ENGINE (2026 META)       ")
    print("==================================================================\n")

    # 1. Cargar base canónica y motores
    print("[1/4] Inicializando Capa Canónica y Motor Físico...")
    db = build_or_load_canonical_db()
    physics = ClashPhysicsEngine(db)
    print("      -> Base de datos cargada (8 Campeones, 17 Héroes, 42 Evos, 5 Tropas de Torre).\n")

    meta_weights = {
        "Knight": 0.32, "Mini P.E.K.K.A.": 0.18, "Musketeer": 0.20,
        "Valkyrie": 0.22, "The Log": 0.45, "Fireball": 0.28,
        "Hog Rider": 0.22, "P.E.K.K.A": 0.15, "Cannon": 0.15,
        "Goblins": 0.20, "Archers": 0.15, "Skeletons": 0.30
    }

    # 2. PILAR 1: Simulación de Parche Multi-Carta y Detección de Daño Colateral
    print("[2/4] PILAR 1: Simulando Parche de Balance Multi-Carta...")
    patch_simulator = MultiCardPatchSimulator(physics)
    patch_proposal = {
        "Knight": {"damage_per_hit": 8.0},          # Buff: +8% daño al Caballero
        "Musketeer": {"hp": -5.0},                 # Nerf: -5% vida a la Mosquetera
        "Mini P.E.K.K.A.": {"damage_per_hit": -4.0} # Nerf: -4% daño al Mini PEKKA
    }
    roster = ["Knight", "Mini P.E.K.K.A.", "Musketeer", "Valkyrie", "Hog Rider", "P.E.K.K.A"]
    patch_report = patch_simulator.simulate_balance_patch(patch_proposal, roster, meta_weights, with_tower=True)

    print(f"\n      {'Carta':<16} | {'Estado':<12} | {'Desplazamiento Elixir':<22} | {'Flips'}")
    print("      " + "-" * 62)
    for cname, rep in sorted(patch_report.items(), key=lambda x: x[1]['weighted_elixir_shift'], reverse=True):
        status = "MODIFICADA" if rep["is_directly_patched"] else "COLATERAL"
        print(f"      {cname:<16} | {status:<12} | {rep['weighted_elixir_shift']:+0.4f} gotas/partida   | {len(rep['matchup_flips'])}")

    # 3. PILAR 1B: Optimizador Autónomo de Balance y Watchlist
    print("\n[3/4] PILAR 1B: Auditoría Automática de Salud del Metajuego (Watchlist)...")
    optimizer = AutonomousBalanceOptimizer(physics, meta_weights)
    watchlist, mean_eff, std_eff = optimizer.scan_meta_health(roster)
    print(f"      Media del Meta: {mean_eff:+0.3f} gotas | Desviación Estándar: {std_eff:0.3f}\n")
    print(f"      {'Carta':<16} | {'Eficiencia':<14} | {'Z-Score':<8} | {'Veredicto'}")
    print("      " + "-" * 54)
    for w in watchlist[:5]:
        print(f"      {w['card']:<16} | {w['efficiency_score']:+0.4f} gotas  | {w['z_score']:+0.2f}    | {w['status']}")

    # 4. PILAR 2: Analizador Táctico de Partidas (Game Review & Blunders)
    print("\n[4/4] PILAR 2: Analizador Táctico de Partidas (Game Review)...")
    reviewer = ClashMatchReviewer(physics)
    sample_match = {
        "player_name": "Chuy", "opponent_name": "Pro_Player",
        "events": [
            {"time": 22.0, "player": "user", "card": "Wizard", "hand": ["Wizard", "The Log", "Knight", "Cannon"], "target_attacker": "Goblin Barrel"},
            {"time": 55.0, "player": "user", "card": "Knight", "hand": ["Knight", "The Log", "Cannon", "Musketeer"], "seconds_at_cap": 2.8},
            {"time": 105.0, "player": "user", "card": "Cannon", "tile": (12.0, 10.0), "enemy_lane_x": 3.5, "hand": ["Cannon", "Knight", "The Log", "Musketeer"], "target_attacker": "Hog Rider"},
            {"time": 140.0, "player": "user", "card": "Knight", "hand": ["Knight", "The Log", "Musketeer", "Cannon"], "target_attacker": "Mini P.E.K.K.A."}
        ]
    }
    review_result = reviewer.analyze_match(sample_match)
    print(f"\n      -> Puntuación de Precisión Táctica: {review_result['tactical_accuracy_pct']}%\n")
    print("      Resumen de Decisiones:")
    for k, v in review_result["summary"].items():
        print(f"         * {k:<18}: {v}")

    if review_result["blunders"]:
        print("\n      [!] Errores Graves (Blunders) Detectados:")
        for b in review_result["blunders"]:
            print(f"         * [{b['time']}s] {b['type']}: {b['description']}")

    if review_result["leaks"]:
        print("\n      [!] Fugas de Elixir Detectadas:")
        for l in review_result["leaks"]:
            print(f"         * [{l['time']}s] Estuviste {l['seconds_at_cap']}s al tope de 10 de elixir (Regalaste {l['leaked_elixir']} gotas al rival)")

    print("\n==================================================================")
    print("           DEMOSTRACIÓN FINALIZADA CON ÉXITO AL 100%              ")
    print("==================================================================")

if __name__ == "__main__":
    main()
