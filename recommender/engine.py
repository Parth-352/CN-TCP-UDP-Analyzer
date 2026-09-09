"""
NetPulse Recommendation Engine.

Evaluates TCP vs UDP suitability for a given application profile based on:
1. Application requirement profile weights (latency, jitter, loss tolerance, reliability)
2. Measured or estimated network performance metrics (RTT, packet loss, jitter)

Returns recommended protocol ('TCP' or 'UDP'), normalized confidence %, scores, and explicit reasons.
"""

from typing import Dict, Any


def recommend(metrics: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recommend transport protocol (TCP or UDP) for an application profile.

    Parameters:
        metrics: Dictionary containing network metrics or protocol measurements.
                 Can be flat (e.g. {'avg_rtt_ms': 5.0, 'packet_loss_pct': 0.0})
                 or nested per protocol (e.g. {'TCP': {...}, 'UDP': {...}}).
        profile: Application profile dictionary with 'name', 'description', and 'weights'.

    Returns:
        dict: {
            'protocol': 'TCP' | 'UDP',
            'confidence_pct': int (50 to 99),
            'tcp_score': float,
            'udp_score': float,
            'reasons': list of str
        }
    """
    weights = profile.get("weights", {})
    lat_sens = weights.get("latency_sensitivity", 0.5)
    jit_sens = weights.get("jitter_sensitivity", 0.5)
    loss_tol = weights.get("loss_tolerance", 0.5)
    rel_need = weights.get("reliability_need", 0.5)

    tcp_score = 50.0
    udp_score = 50.0
    reasons = []

    # 1. Reliability & Data Loss Evaluation
    if rel_need >= 0.8 or loss_tol <= 0.1:
        tcp_boost = rel_need * 35.0
        udp_penalty = (1.0 - loss_tol) * 25.0
        tcp_score += tcp_boost
        udp_score -= udp_penalty
        reasons.append(
            f"{profile['name']} requires strict data reliability ({rel_need * 100:.0f}% need). "
            f"TCP provides guaranteed, zero-loss ordered byte delivery."
        )
    elif loss_tol >= 0.6 and rel_need <= 0.3:
        udp_boost = loss_tol * 30.0
        udp_score += udp_boost
        reasons.append(
            f"{profile['name']} tolerates packet loss ({loss_tol * 100:.0f}% tolerance). "
            f"UDP avoids head-of-line blocking by discarding stale updates."
        )

    # 2. Latency Sensitivity Evaluation
    if lat_sens >= 0.7:
        udp_boost = lat_sens * 30.0
        tcp_penalty = lat_sens * 15.0
        udp_score += udp_boost
        tcp_score -= tcp_penalty
        reasons.append(
            f"Low latency is critical ({lat_sens * 100:.0f}% sensitivity). "
            f"UDP eliminates TCP 3-way handshake overhead and retransmission delay spikes."
        )
    elif lat_sens <= 0.3:
        tcp_score += 10.0
        reasons.append(
            f"Latency tolerance is high ({lat_sens * 100:.0f}% sensitivity). "
            f"TCP retransmission overhead does not impact user experience."
        )

    # 3. Jitter Sensitivity Evaluation
    if jit_sens >= 0.7:
        udp_boost = jit_sens * 25.0
        udp_score += udp_boost
        reasons.append(
            f"High jitter sensitivity ({jit_sens * 100:.0f}%). "
            f"UDP avoids TCP congestion control window fluctuations and retransmission stalls."
        )

    # 4. Measured Empirical Network Metrics (if provided)
    tcp_metrics = metrics.get("TCP", {}) if "TCP" in metrics else metrics
    udp_metrics = metrics.get("UDP", {}) if "UDP" in metrics else metrics

    tcp_loss = tcp_metrics.get("packet_loss_pct", tcp_metrics.get("PacketLoss", 0.0))
    udp_loss = udp_metrics.get("packet_loss_pct", udp_metrics.get("PacketLoss", 0.0))
    tcp_rtt = tcp_metrics.get("avg_rtt_ms", tcp_metrics.get("AvgRTT", None))
    udp_rtt = udp_metrics.get("avg_rtt_ms", udp_metrics.get("AvgRTT", None))

    if udp_loss > 0.0 and rel_need >= 0.5:
        tcp_score += 15.0
        reasons.append(
            f"Observed UDP packet loss ({udp_loss:.2f}%) poses risk for application reliability."
        )

    if tcp_rtt is not None and udp_rtt is not None:
        if udp_rtt < tcp_rtt and lat_sens >= 0.5:
            udp_score += 10.0
            reasons.append(
                f"Measured UDP RTT ({udp_rtt:.3f} ms) is faster than TCP RTT ({tcp_rtt:.3f} ms)."
            )

    # Normalize scores to 0-100 range
    tcp_score = max(0.0, min(100.0, tcp_score))
    udp_score = max(0.0, min(100.0, udp_score))

    # Winner & Confidence Calculation
    if tcp_score >= udp_score:
        protocol = "TCP"
        diff = tcp_score - udp_score
    else:
        protocol = "UDP"
        diff = udp_score - tcp_score

    # Confidence formula: maps score difference to 50% - 99%
    confidence_pct = min(99, max(50, int(50 + (diff / 100.0) * 50)))

    return {
        "protocol": protocol,
        "confidence_pct": confidence_pct,
        "tcp_score": round(tcp_score, 1),
        "udp_score": round(udp_score, 1),
        "reasons": reasons,
    }
