"""
NetPulse UDP Echo Client.

Sends N datagrams to the UDP server, waits for each echo with a timeout.
If no echo arrives before the timeout, marks that sequence number as lost.
"""

import socket
import time
import sys
import os
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from protocol import build_packet, parse_header
from metrics.engine import compute_metrics, print_metrics


def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)


def run_client(host: str, port: int, num_packets: int, packet_size: int,
               timeout_sec: float) -> list:
    """Run a UDP echo test.

    Args:
        host: Server IP.
        port: Server port.
        num_packets: Number of datagrams to send.
        packet_size: Size of each datagram in bytes.
        timeout_sec: Seconds to wait for each echo reply.

    Returns:
        List of dicts: {seq, sent_at, received_at} where received_at is
        None if the echo was not received (packet lost).
    """
    records = []
    lost_seqs = []

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout_sec)
        print(f"[UDP Client] Sending to {host}:{port}")
        print(f"[UDP Client] {num_packets} packets of {packet_size} bytes, timeout={timeout_sec}s\n")

        for i in range(num_packets):
            pkt = build_packet(i, packet_size)
            sent_at = time.time()
            sock.sendto(pkt, (host, port))

            try:
                echo, _ = sock.recvfrom(65535)
                received_at = time.time()
                echo_seq, echo_ts = parse_header(echo)
                rtt_ms = (received_at - sent_at) * 1000

                records.append({
                    "seq": i,
                    "sent_at": sent_at,
                    "received_at": received_at,
                })
                print(f"  seq={i:4d}  sent={sent_at:.6f}  recv={received_at:.6f}  RTT={rtt_ms:.3f}ms")

            except socket.timeout:
                records.append({
                    "seq": i,
                    "sent_at": sent_at,
                    "received_at": None,
                })
                lost_seqs.append(i)
                print(f"  seq={i:4d}  sent={sent_at:.6f}  *** LOST (timeout) ***")

    received = num_packets - len(lost_seqs)
    print(f"\n[UDP Client] Done. {received}/{num_packets} packets echoed.")
    if lost_seqs:
        print(f"[UDP Client] Lost sequence numbers: {lost_seqs}")

    return records


if __name__ == "__main__":
    cfg = load_config()
    pkt_size = cfg["packet_sizes"][0]
    if len(sys.argv) > 1:
        pkt_size = int(sys.argv[1])

    records = run_client(
        cfg["server_ip"], cfg["server_port"],
        cfg["num_packets"], pkt_size,
        cfg["protocol_timeout_sec"],
    )
    metrics = compute_metrics(records, packet_size=pkt_size)
    print_metrics(metrics, protocol="UDP")
