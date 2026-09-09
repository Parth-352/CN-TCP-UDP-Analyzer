"""
NetPulse TCP Echo Server.

Listens on the configured address, accepts one connection at a time,
echoes every received packet back immediately, and closes cleanly on FIN.
"""

import socket
import sys
import os
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from protocol import HEADER_SIZE, parse_header


def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)


def recv_exact(sock: socket.socket, n: int) -> bytes:
    """Receive exactly n bytes from a TCP socket, or b'' on disconnect."""
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return b""
        buf.extend(chunk)
    return bytes(buf)


def run_server(host: str, port: int, packet_size: int = None):
    """Start the TCP echo server.

    Args:
        host: IP to bind to.
        port: Port to listen on.
        packet_size: Expected packet size. If None, reads header first
                     to determine boundaries (fixed-size framing).
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(1)
        print(f"[TCP Server] Listening on {host}:{port}")

        conn, addr = srv.accept()
        with conn:
            print(f"[TCP Server] Connection from {addr}")

            while True:
                # First, read the 4-byte length prefix
                length_data = recv_exact(conn, 4)
                if not length_data:
                    break

                msg_len = int.from_bytes(length_data, "big")
                data = recv_exact(conn, msg_len)
                if not data:
                    break

                seq, ts = parse_header(data)
                print(f"[TCP Server] Echoing packet seq={seq}")
                # Echo back with the same length prefix
                conn.sendall(length_data + data)

        print("[TCP Server] Client disconnected, shutting down.")


if __name__ == "__main__":
    cfg = load_config()
    run_server(cfg["server_ip"], cfg["server_port"])
