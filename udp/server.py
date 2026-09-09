"""
NetPulse UDP Echo Server.

Binds to the configured address, receives datagrams, and echoes each one
back to the sender's address. Runs until interrupted (Ctrl+C).
"""

import socket
import sys
import os
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from protocol import parse_header


def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)


def run_server(host: str, port: int):
    """Start the UDP echo server.

    Args:
        host: IP to bind to.
        port: Port to listen on.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as srv:
        srv.bind((host, port))
        print(f"[UDP Server] Listening on {host}:{port}")

        try:
            while True:
                data, addr = srv.recvfrom(65535)
                seq, ts = parse_header(data)
                print(f"[UDP Server] Echoing packet seq={seq} to {addr}")
                srv.sendto(data, addr)
        except KeyboardInterrupt:
            print("\n[UDP Server] Shutting down.")


if __name__ == "__main__":
    cfg = load_config()
    run_server(cfg["server_ip"], cfg["server_port"])
