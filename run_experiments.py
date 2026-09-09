"""
NetPulse Experiment Runner.

Loops over all packet sizes in config.yaml, runs TCP then UDP for each,
collects metrics, and appends results to data/results.csv.

Usage:
    python run_experiments.py            # append to existing results
    python run_experiments.py --fresh    # wipe results.csv and start fresh
"""

import argparse
import csv
import os
import subprocess
import sys
import time
from datetime import datetime

import pandas as pd
import yaml

# Project root
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcp.client import run_client as tcp_run
from udp.client import run_client as udp_run
from metrics.engine import compute_metrics, print_metrics

CSV_PATH = os.path.join(ROOT, "data", "results.csv")
CSV_COLUMNS = [
    "Protocol", "PacketSize", "Packets",
    "TransmissionTime", "AvgRTT", "Throughput",
    "PacketLoss", "Jitter", "Timestamp",
]


def load_config():
    with open(os.path.join(ROOT, "config.yaml")) as f:
        return yaml.safe_load(f)


def ensure_csv(fresh: bool = False):
    """Create the CSV file with headers if it doesn't exist, or wipe if --fresh."""
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    if fresh or not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_COLUMNS)
        if fresh:
            print("[Runner] Wiped results.csv (--fresh)")


def append_row(protocol: str, packet_size: int, num_packets: int, metrics: dict):
    """Append one experiment result row to the CSV."""
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            protocol,
            packet_size,
            num_packets,
            metrics["transmission_time_sec"],
            metrics["avg_rtt_ms"],
            metrics["throughput_mbps"],
            metrics["packet_loss_pct"],
            metrics["jitter_ms"],
            datetime.now().isoformat(timespec="seconds"),
        ])


def start_server(protocol: str, cfg: dict) -> subprocess.Popen:
    """Start a TCP or UDP server as a subprocess."""
    script = os.path.join(ROOT, protocol, "server.py")
    proc = subprocess.Popen(
        [sys.executable, script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.5)  # give the server time to bind
    return proc


def stop_server(proc: subprocess.Popen):
    """Terminate a server subprocess."""
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def run_experiment(protocol: str, cfg: dict, packet_size: int) -> dict:
    """Run one experiment: start server, run client, compute metrics, stop server."""
    host = cfg["server_ip"]
    port = cfg["server_port"]
    num_packets = cfg["num_packets"]
    timeout = cfg["protocol_timeout_sec"]

    print(f"\n{'─' * 50}")
    print(f"  {protocol.upper()} | Packet Size: {packet_size} bytes | Packets: {num_packets}")
    print(f"{'─' * 50}")

    server = start_server(protocol, cfg)

    try:
        if protocol == "tcp":
            records = tcp_run(host, port, num_packets, packet_size)
        else:
            records = udp_run(host, port, num_packets, packet_size, timeout)

        metrics = compute_metrics(records, packet_size=packet_size)
        print_metrics(metrics, protocol=protocol.upper())
        return metrics

    finally:
        stop_server(server)


def print_summary():
    """Load and print the full results table using pandas."""
    if not os.path.exists(CSV_PATH):
        print("[Runner] No results.csv found.")
        return

    df = pd.read_csv(CSV_PATH)
    if df.empty:
        print("[Runner] results.csv is empty.")
        return

    print(f"\n{'=' * 70}")
    print("  EXPERIMENT SUMMARY")
    print(f"{'=' * 70}")
    # Show a clean comparison table
    summary = df[["Protocol", "PacketSize", "TransmissionTime", "AvgRTT",
                   "Throughput", "PacketLoss", "Jitter"]].to_string(index=False)
    print(summary)
    print(f"{'=' * 70}")
    print(f"  Total runs: {len(df)}  |  CSV: {CSV_PATH}")
    print(f"{'=' * 70}\n")


def main():
    parser = argparse.ArgumentParser(description="NetPulse Experiment Runner")
    parser.add_argument("--fresh", action="store_true",
                        help="Wipe results.csv before running experiments")
    args = parser.parse_args()

    cfg = load_config()
    ensure_csv(fresh=args.fresh)

    packet_sizes = cfg["packet_sizes"]
    num_packets = cfg["num_packets"]

    print(f"[Runner] Starting experiments: {len(packet_sizes)} sizes × 2 protocols")
    print(f"[Runner] Packet sizes: {packet_sizes}")
    print(f"[Runner] Packets per run: {num_packets}")

    for pkt_size in packet_sizes:
        for protocol in ["tcp", "udp"]:
            metrics = run_experiment(protocol, cfg, pkt_size)
            append_row(protocol.upper(), pkt_size, num_packets, metrics)

    print_summary()
    print("[Runner] All experiments complete.")


if __name__ == "__main__":
    main()
