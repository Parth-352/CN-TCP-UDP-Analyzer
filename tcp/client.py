"""
NetPulse TCP Echo Client.

Connects to the TCP server, sends N packets of a given size, waits for
the echo of each before sending the next, and records send/receive
timestamps per packet.
"""

import socket
import time
import sys
import os
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from protocol import build_packet, parse_header, HEADER_SIZE
from metrics.engine import compute_metrics, print_metrics


def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)


def recv_exact(sock: socket.socket, n: int) -> bytes:
    """Receive exactly n bytes from a TCP socket."""
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Server closed connection unexpectedly")
        buf.extend(chunk)
    return bytes(buf)


def run_client(host: str, port: int, num_packets: int, packet_size: int) -> list:
    """Run a TCP echo test.

    Args:
        host: Server IP.
        port: Server port.
        num_packets: Number of packets to send.
        packet_size: Size of each packet in bytes.

    Returns:
        List of dicts: {seq, sent_at, received_at}.
    """
    records = []

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        print(f"[TCP Client] Connected to {host}:{port}")
        print(f"[TCP Client] Sending {num_packets} packets of {packet_size} bytes\n")

        for i in range(num_packets):
            pkt = build_packet(i, packet_size)
            sent_at = time.time()

            # Send with 4-byte length prefix for framing
            length_prefix = len(pkt).to_bytes(4, "big")
            sock.sendall(length_prefix + pkt)

            # Receive the echoed length prefix + packet
            recv_exact(sock, 4)  # length prefix
            echo = recv_exact(sock, len(pkt))
            received_at = time.time()

            echo_seq, echo_ts = parse_header(echo)
            rtt_ms = (received_at - sent_at) * 1000

            records.append({
                "seq": i,
                "sent_at": sent_at,
                "received_at": received_at,
            })

            print(f"  seq={i:4d}  sent={sent_at:.6f}  recv={received_at:.6f}  RTT={rtt_ms:.3f}ms")

    print(f"\n[TCP Client] Done. {len(records)} packets sent and echoed.")
    return records


if __name__ == "__main__":
    cfg = load_config()
    # Default to smallest packet size if not specified
    pkt_size = cfg["packet_sizes"][0]
    if len(sys.argv) > 1:
        pkt_size = int(sys.argv[1])

    records = run_client(cfg["server_ip"], cfg["server_port"], cfg["num_packets"], pkt_size)
    metrics = compute_metrics(records, packet_size=pkt_size)
    print_metrics(metrics, protocol="TCP")
