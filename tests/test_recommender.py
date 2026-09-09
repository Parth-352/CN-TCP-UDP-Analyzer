"""
Unit tests for NetPulse Protocol Recommendation Engine.
"""

import unittest
from recommender.profiles import PROFILES, get_profile
from recommender.engine import recommend


class TestRecommender(unittest.TestCase):

    def setUp(self):
        self.dummy_metrics = {
            "TCP": {"AvgRTT": 2.5, "PacketLoss": 0.0, "Jitter": 0.2, "Throughput": 50.0},
            "UDP": {"AvgRTT": 1.2, "PacketLoss": 0.0, "Jitter": 0.1, "Throughput": 65.0},
        }

    def test_gaming_recommends_udp(self):
        profile = PROFILES["Gaming"]
        result = recommend(self.dummy_metrics, profile)
        self.assertEqual(result["protocol"], "UDP")
        self.assertGreater(result["udp_score"], result["tcp_score"])
        self.assertGreaterEqual(result["confidence_pct"], 60)
        self.assertTrue(any("latency" in r.lower() for r in result["reasons"]))

    def test_file_transfer_recommends_tcp(self):
        profile = PROFILES["FileTransfer"]
        result = recommend(self.dummy_metrics, profile)
        self.assertEqual(result["protocol"], "TCP")
        self.assertGreater(result["tcp_score"], result["udp_score"])
        self.assertGreaterEqual(result["confidence_pct"], 60)
        self.assertTrue(any("reliability" in r.lower() for r in result["reasons"]))

    def test_streaming_recommends_tcp(self):
        profile = PROFILES["Streaming"]
        result = recommend(self.dummy_metrics, profile)
        self.assertEqual(result["protocol"], "TCP")

    def test_videocall_recommends_udp(self):
        profile = PROFILES["VideoCall"]
        result = recommend(self.dummy_metrics, profile)
        self.assertEqual(result["protocol"], "UDP")

    def test_confidence_bounds(self):
        for name, profile in PROFILES.items():
            res = recommend(self.dummy_metrics, profile)
            self.assertGreaterEqual(res["confidence_pct"], 50)
            self.assertLessEqual(res["confidence_pct"], 99)
            self.assertIn(res["protocol"], ["TCP", "UDP"])

    def test_measured_udp_loss_boosts_tcp(self):
        lossy_metrics = {
            "TCP": {"AvgRTT": 2.5, "PacketLoss": 0.0},
            "UDP": {"AvgRTT": 1.2, "PacketLoss": 15.0},
        }
        profile = PROFILES["WebAPI"]
        res = recommend(lossy_metrics, profile)
        self.assertEqual(res["protocol"], "TCP")
        self.assertTrue(any("observed udp packet loss" in r.lower() for r in res["reasons"]))


if __name__ == "__main__":
    unittest.main()
