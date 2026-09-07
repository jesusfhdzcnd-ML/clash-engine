import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clash_core import (
    build_or_load_canonical_db, get_card, ClashPhysicsEngine,
    MultiCardPatchSimulator, AutonomousBalanceOptimizer, ClashMatchReviewer,
    CHAMPIONS_LIST, HEROES_REGISTRY, EVOLUTIONS_REGISTRY
)

class TestClashCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = build_or_load_canonical_db()
        cls.physics = ClashPhysicsEngine(cls.db)
        cls.meta_weights = {
            "Knight": 0.32, "Mini P.E.K.K.A.": 0.18, "Musketeer": 0.20,
            "Valkyrie": 0.22, "The Log": 0.45, "Fireball": 0.28,
            "Hog Rider": 0.22, "P.E.K.K.A": 0.15, "Cannon": 0.15
        }

    def test_canonical_catalog_integrity(self):
        self.assertEqual(len(CHAMPIONS_LIST), 8)
        self.assertEqual(len(HEROES_REGISTRY), 17)
        self.assertEqual(len(EVOLUTIONS_REGISTRY), 42)

        bandit = get_card(self.db, "Boss Bandit")
        self.assertIsNotNone(bandit)
        self.assertEqual(bandit["active_ability"]["max_uses_per_deployment"], 2)

        goblinstein = get_card(self.db, "Goblinstein")
        self.assertIsNotNone(goblinstein)

        for t in ["Princess Tower", "Cannoneer", "Dagger Duchess", "Royal Chef", "King Tower"]:
            self.assertIsNotNone(get_card(self.db, t))

    def test_rarity_indexing_and_spell_damage(self):
        musk = get_card(self.db, "Musketeer")
        wiz = get_card(self.db, "Wizard")
        self.assertEqual(musk["stats_by_level"]["11"]["hp"], 721)
        self.assertEqual(wiz["stats_by_level"]["11"]["hp"], 755)

        fb = get_card(self.db, "Fireball")
        self.assertEqual(fb["stats_by_level"]["11"]["damage_per_hit"], 689)

    def test_spell_interaction_breakpoints(self):
        res = self.physics.simulate_spell("Fireball", "Musketeer")
        self.assertIsNotNone(res)
        self.assertFalse(res["kills_outright"])
        self.assertTrue(res["leaves_at_one_tower_shot"])
        self.assertEqual(res["remaining_hp"], 32)

    def test_swarm_vs_aoe_physics(self):
        res_valk = self.physics.simulate_troop_combat("Valkyrie", "Skeleton Army", with_tower_for_b=False)
        self.assertIsNotNone(res_valk)
        self.assertEqual(res_valk["winner"], "Valkyrie")
        self.assertLess(res_valk["duration_sec"], 1.0)
        self.assertEqual(res_valk["residual_hp_pct"], 100.0)

    def test_multi_card_patch_simulator(self):
        simulator = MultiCardPatchSimulator(self.physics)
        patch = {
            "Knight": {"damage_per_hit": 8.0},
            "Musketeer": {"hp": -5.0}
        }
        roster = ["Knight", "Musketeer", "Valkyrie", "P.E.K.K.A"]
        report = simulator.simulate_balance_patch(patch, roster, self.meta_weights, with_tower=True)

        self.assertIn("Knight", report)
        self.assertTrue(report["Knight"]["is_directly_patched"])
        self.assertGreater(report["Knight"]["weighted_elixir_shift"], 0.0)

        self.assertIn("Valkyrie", report)
        self.assertFalse(report["Valkyrie"]["is_directly_patched"])
        self.assertLess(report["Valkyrie"]["weighted_elixir_shift"], 0.0)

    def test_autonomous_balance_optimizer(self):
        optimizer = AutonomousBalanceOptimizer(self.physics, self.meta_weights)
        roster = ["Knight", "Mini P.E.K.K.A.", "Musketeer", "Valkyrie", "P.E.K.K.A"]
        watchlist, proposals = optimizer.generate_automated_patch_proposal(roster)
        self.assertGreater(len(watchlist), 0)
        self.assertIn("z_score", watchlist[0])

    def test_match_reviewer_blunder_detection(self):
        reviewer = ClashMatchReviewer(self.physics)
        match_test = {
            "player_name": "TestUser", "opponent_name": "Rival",
            "events": [
                {"time": 25.0, "player": "user", "card": "Wizard", "hand": ["Wizard", "The Log", "Knight", "Cannon"], "target_attacker": "Goblin Barrel"},
                {"time": 80.0, "player": "user", "card": "Cannon", "tile": (12.0, 10.0), "enemy_lane_x": 3.5, "hand": ["Cannon", "Knight", "The Log", "Musketeer"], "target_attacker": "Hog Rider"},
                {"time": 120.0, "player": "user", "card": "Knight", "hand": ["Knight", "The Log", "Cannon", "Musketeer"], "seconds_at_cap": 3.0}
            ]
        }
        report = reviewer.analyze_match(match_test)
        self.assertLess(report["tactical_accuracy_pct"], 80.0)
        self.assertGreater(len(report["blunders"]), 0)
        self.assertGreater(len(report["leaks"]), 0)

if __name__ == "__main__":
    unittest.main()
