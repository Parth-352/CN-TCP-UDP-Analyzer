"""
Unit tests for metrics/engine.py.

Uses hand-crafted records with known expected outputs to verify each
metric formula independently.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from metrics.engine import compute_metrics


class TestComputeMetrics(unittest.TestCase):
    """Tests with deterministic fabricated data."""

    def test_basic_no_loss(self):
        """5 packets, all received, known RTTs: 10, 20, 30, 20, 10 ms."""
        base = 1000.0
        records = [
            {"seq": 0, "sent_at": base + 0.00, "received_at": base + 0.010},   # RTT = 10 ms
            {"seq": 1, "sent_at": base + 0.05, "received_at": base + 0.070},   # RTT = 20 ms
            {"seq": 2, "sent_at": base + 0.10, "received_at": base + 0.130},   # RTT = 30 ms
            {"seq": 3, "sent_at": base + 0.15, "received_at": base + 0.170},   # RTT = 20 ms
            {"seq": 4, "sent_at": base + 0.20, "received_at": base + 0.210},   # RTT = 10 ms
        ]
        m = compute_metrics(records, packet_size=64)

        # Transmission time: last sent_at - first sent_at = 0.20 - 0.00 = 0.20
        self.assertAlmostEqual(m["transmission_time_sec"], 0.20, places=6)

        # Avg RTT: (10 + 20 + 30 + 20 + 10) / 5 = 18.0 ms
        self.assertAlmostEqual(m["avg_rtt_ms"], 18.0, places=2)

        # Packet loss: 0 / 5 = 0%
        self.assertAlmostEqual(m["packet_loss_pct"], 0.0, places=2)

        # Jitter: mean(|20-10|, |30-20|, |20-30|, |10-20|) = mean(10, 10, 10, 10) = 10.0 ms
        self.assertAlmostEqual(m["jitter_ms"], 10.0, places=2)

        # Throughput: 5 pkts * 64 bytes * 8 bits / elapsed_sec / 1e6
        # elapsed = last recv (0.210) - first send (0.00) = 0.210 s
        # = (5 * 64 * 8) / (0.210 * 1e6) = 2560 / 210000 ≈ 0.01219 Mbps
        self.assertAlmostEqual(m["throughput_mbps"], 0.0122, places=3)

    def test_with_packet_loss(self):
        """5 packets, 2 lost (seq 1 and 3)."""
        base = 2000.0
        records = [
            {"seq": 0, "sent_at": base + 0.00, "received_at": base + 0.010},   # RTT = 10 ms
            {"seq": 1, "sent_at": base + 0.05, "received_at": None},            # LOST
            {"seq": 2, "sent_at": base + 0.10, "received_at": base + 0.130},   # RTT = 30 ms
            {"seq": 3, "sent_at": base + 0.15, "received_at": None},            # LOST
            {"seq": 4, "sent_at": base + 0.20, "received_at": base + 0.220},   # RTT = 20 ms
        ]
        m = compute_metrics(records, packet_size=64)

        # Packet loss: 2 / 5 = 40%
        self.assertAlmostEqual(m["packet_loss_pct"], 40.0, places=2)

        # Avg RTT: (10 + 30 + 20) / 3 ≈ 20.0 ms (only successful packets)
        self.assertAlmostEqual(m["avg_rtt_ms"], 20.0, places=2)

        # Jitter over successful RTTs [10, 30, 20]: mean(|30-10|, |20-30|) = mean(20, 10) = 15.0
        self.assertAlmostEqual(m["jitter_ms"], 15.0, places=2)

    def test_all_lost(self):
        """All packets lost → loss = 100%, all other metrics zero."""
        records = [
            {"seq": 0, "sent_at": 100.0, "received_at": None},
            {"seq": 1, "sent_at": 100.05, "received_at": None},
        ]
        m = compute_metrics(records, packet_size=64)

        self.assertAlmostEqual(m["packet_loss_pct"], 100.0, places=2)
        self.assertAlmostEqual(m["avg_rtt_ms"], 0.0, places=2)
        self.assertAlmostEqual(m["throughput_mbps"], 0.0, places=2)
        self.assertAlmostEqual(m["jitter_ms"], 0.0, places=2)

    def test_empty_records(self):
        """Empty input → safe defaults."""
        m = compute_metrics([], packet_size=64)

        self.assertAlmostEqual(m["packet_loss_pct"], 100.0)
        self.assertAlmostEqual(m["avg_rtt_ms"], 0.0)
        self.assertAlmostEqual(m["throughput_mbps"], 0.0)
        self.assertAlmostEqual(m["jitter_ms"], 0.0)

    def test_single_packet(self):
        """One packet → transmission_time = 0, jitter = 0, RTT computed."""
        records = [
            {"seq": 0, "sent_at": 500.0, "received_at": 500.015},  # RTT = 15 ms
        ]
        m = compute_metrics(records, packet_size=128)

        self.assertAlmostEqual(m["transmission_time_sec"], 0.0, places=6)
        self.assertAlmostEqual(m["avg_rtt_ms"], 15.0, places=2)
        self.assertAlmostEqual(m["jitter_ms"], 0.0, places=2)
        self.assertAlmostEqual(m["packet_loss_pct"], 0.0, places=2)
        # Throughput: 0 because transmission_time = 0
        self.assertAlmostEqual(m["throughput_mbps"], 0.0, places=2)

    def test_jitter_constant_rtt(self):
        """All RTTs identical → jitter = 0."""
        base = 3000.0
        records = [
            {"seq": 0, "sent_at": base + 0.00, "received_at": base + 0.010},
            {"seq": 1, "sent_at": base + 0.05, "received_at": base + 0.060},
            {"seq": 2, "sent_at": base + 0.10, "received_at": base + 0.110},
            {"seq": 3, "sent_at": base + 0.15, "received_at": base + 0.160},
        ]
        m = compute_metrics(records, packet_size=64)

        self.assertAlmostEqual(m["jitter_ms"], 0.0, places=4)


if __name__ == "__main__":
    unittest.main()
