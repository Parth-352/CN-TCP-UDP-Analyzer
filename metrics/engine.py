"""
NetPulse Measurement Engine.

Given per-packet send/receive records from a TCP or UDP echo test,
computes the five core metrics:
  - transmission_time_sec
  - avg_rtt_ms
  - throughput_mbps
  - packet_loss_pct
  - jitter_ms (RFC 3550-style: mean of absolute differences between
    consecutive successful RTT samples)
"""


def compute_metrics(records: list, packet_size: int = 0) -> dict:
    """Compute network performance metrics from echo-test records.

    Args:
        records: List of dicts, each with keys:
            - seq (int): sequence number
            - sent_at (float): time.time() when packet was sent
            - received_at (float | None): time.time() when echo arrived,
              or None if the packet was lost
        packet_size: Size of each packet in bytes (used for throughput).

    Returns:
        Dict with keys: transmission_time_sec, avg_rtt_ms, throughput_mbps,
        packet_loss_pct, jitter_ms.
    """
    if not records:
        return {
            "transmission_time_sec": 0.0,
            "avg_rtt_ms": 0.0,
            "throughput_mbps": 0.0,
            "packet_loss_pct": 100.0,
            "jitter_ms": 0.0,
        }

    total = len(records)

    # Separate successful (received) and lost records
    successful = [r for r in records if r["received_at"] is not None]
    lost_count = total - len(successful)

    # --- Transmission time ---
    # Wall-clock span from first send to last send
    send_times = [r["sent_at"] for r in records]
    transmission_time_sec = send_times[-1] - send_times[0] if len(send_times) > 1 else 0.0

    # --- RTT ---
    rtts_ms = []
    for r in successful:
        rtt = (r["received_at"] - r["sent_at"]) * 1000  # seconds → ms
        rtts_ms.append(rtt)

    avg_rtt_ms = sum(rtts_ms) / len(rtts_ms) if rtts_ms else 0.0

    # --- Throughput ---
    # Total bytes acknowledged / total elapsed time (first send → last receive)
    if successful and transmission_time_sec > 0:
        total_bytes_acked = len(successful) * packet_size
        # Use wall time from first send to last receive for throughput
        last_recv = max(r["received_at"] for r in successful)
        elapsed = last_recv - send_times[0]
        throughput_mbps = (total_bytes_acked * 8) / (elapsed * 1_000_000) if elapsed > 0 else 0.0
    else:
        throughput_mbps = 0.0

    # --- Packet loss ---
    packet_loss_pct = (lost_count / total) * 100

    # --- Jitter (RFC 3550-style) ---
    # Mean of absolute differences between consecutive successful RTT samples.
    # This is the standard interarrival jitter estimate, not stddev or max-min.
    jitter_ms = 0.0
    if len(rtts_ms) >= 2:
        diffs = [abs(rtts_ms[i] - rtts_ms[i - 1]) for i in range(1, len(rtts_ms))]
        jitter_ms = sum(diffs) / len(diffs)

    return {
        "transmission_time_sec": round(transmission_time_sec, 6),
        "avg_rtt_ms": round(avg_rtt_ms, 4),
        "throughput_mbps": round(throughput_mbps, 4),
        "packet_loss_pct": round(packet_loss_pct, 2),
        "jitter_ms": round(jitter_ms, 4),
    }


def print_metrics(metrics: dict, protocol: str = ""):
    """Pretty-print a metrics dict to stdout."""
    label = f" ({protocol})" if protocol else ""
    print(f"\n{'=' * 45}")
    print(f"  NetPulse Metrics{label}")
    print(f"{'=' * 45}")
    print(f"  Transmission Time : {metrics['transmission_time_sec']:.6f} sec")
    print(f"  Average RTT       : {metrics['avg_rtt_ms']:.4f} ms")
    print(f"  Throughput        : {metrics['throughput_mbps']:.4f} Mbps")
    print(f"  Packet Loss       : {metrics['packet_loss_pct']:.2f} %")
    print(f"  Jitter            : {metrics['jitter_ms']:.4f} ms")
    print(f"{'=' * 45}\n")
