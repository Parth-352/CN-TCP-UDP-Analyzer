"""
Shared wire format for NetPulse TCP/UDP echo protocol.

Every packet (TCP and UDP) uses the same layout:
    [8 bytes] sequence number  — big-endian unsigned long long
    [8 bytes] timestamp        — big-endian double (time.time())
    [N bytes] payload          — zero-filled padding to reach desired packet size

Total packet size = 16-byte header + payload bytes.
"""

import struct
import time

# Header: 8-byte sequence number + 8-byte timestamp
HEADER_FORMAT = "!Qd"  # Q = uint64 big-endian, d = float64 (double)
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # 16 bytes


def build_packet(seq: int, packet_size: int) -> bytes:
    """Build a packet with header + zero-padded payload.

    Args:
        seq: Sequence number (0-indexed).
        packet_size: Total desired packet size in bytes (must be >= HEADER_SIZE).

    Returns:
        Bytes of length max(packet_size, HEADER_SIZE).
    """
    timestamp = time.time()
    header = struct.pack(HEADER_FORMAT, seq, timestamp)
    payload_size = max(0, packet_size - HEADER_SIZE)
    return header + (b"\x00" * payload_size)


def parse_header(data: bytes) -> tuple:
    """Extract (sequence_number, timestamp) from the first 16 bytes.

    Args:
        data: Raw packet bytes (at least HEADER_SIZE long).

    Returns:
        (seq, timestamp) tuple.

    Raises:
        struct.error: If data is shorter than HEADER_SIZE.
    """
    seq, timestamp = struct.unpack(HEADER_FORMAT, data[:HEADER_SIZE])
    return seq, timestamp
