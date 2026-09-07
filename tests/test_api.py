import unittest
import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clash_api.main import app

class TestClashAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_check(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "online")

    def test_list_cards(self):
        resp = self.client.get("/api/v1/cards/")
        self.assertEqual(resp.status_code, 200)
        cards = resp.json()
        self.assertGreater(len(cards), 20)
        card_names = [c["name"] for c in cards]
        self.assertIn("Knight", card_names)
        self.assertIn("Musketeer", card_names)

    def test_get_card_detail_and_breakpoints(self):
        resp = self.client.get("/api/v1/cards/Musketeer")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["name"], "Musketeer")
        self.assertEqual(data["hp"], 721, "Mosquetera N11 debe tener 721 HP")
        self.assertIn("spell_interactions", data)
        self.assertIn("Fireball", data["spell_interactions"])
        self.assertIn("1 TIRO DE TORRE", data["spell_interactions"]["Fireball"])

    def test_balance_watchlist(self):
        resp = self.client.get("/api/v1/balance/watchlist")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("watchlist", data)
        self.assertGreater(len(data["watchlist"]), 0)
        self.assertIn("automated_patch_proposals", data)

    def test_simulate_patch_endpoint(self):
        payload = {
            "modifications": {
                "Knight": {"damage_per_hit": 8.0},
                "Musketeer": {"hp": -5.0}
            },
            "with_tower": True
        }
        resp = self.client.post("/api/v1/balance/simulate-patch", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("cards_impacted", data)
        self.assertIn("Knight", data["cards_impacted"])
        self.assertTrue(data["cards_impacted"]['Knight']["is_directly_patched"])
        self.assertGreater(data["cards_impacted"]["Knight"]["weighted_elixir_shift"], 0.0)

    def test_analyze_match_endpoint(self):
        payload = {
            "player_name": "Chuy",
            "opponent_name": "Rival",
            "player_deck": ["Wizard", "The Log", "Knight", "Cannon"],
            "opponent_deck": ["Goblin Barrel", "Hog Rider"],
            "events": [
                {
                    "time": 25.0, "player": "user", "card": "Wizard",
                    "hand": ["Wizard", "The Log", "Knight", "Cannon"],
                    "target_attacker": "Goblin Barrel"
                },
                {
                    "time": 75.0, "player": "user", "card": "Cannon",
                    "tile": [12.0, 10.0], "enemy_lane_x": 3.5,
                    "hand": ["Cannon", "Knight", "The Log", "Wizard"],
                    "target_attacker": "Hog Rider"
                },
                {
                    "time": 110.0, "player": "user", "card": "Knight",
                    "seconds_at_cap": 2.5
                }
            ]
        }
        resp = self.client.post("/api/v1/review/analyze", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("tactical_accuracy_pct", data)
        self.assertIn("summary", data)
        self.assertGreater(len(data["blunders"]), 0)
        self.assertGreater(len(data["leaks"]), 0)

if __name__ == "__main__":
    unittest.main()
