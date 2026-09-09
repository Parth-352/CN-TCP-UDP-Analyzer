"""
NetPulse Application Profiles.

Defines 6 application workload profiles with normalized sensitivity weights (0.0 to 1.0)
for transport protocol selection:
- latency_sensitivity
- jitter_sensitivity
- loss_tolerance
- reliability_need
"""

PROFILES = {
    "Gaming": {
        "name": "Real-Time Online Gaming",
        "description": "Fast-paced multiplayer gaming requiring sub-50ms latency. Drops individual state updates rather than waiting for retransmissions.",
        "weights": {
            "latency_sensitivity": 0.95,
            "jitter_sensitivity": 0.90,
            "loss_tolerance": 0.80,
            "reliability_need": 0.15,
        },
    },
    "VideoCall": {
        "name": "Interactive Video / Audio Call",
        "description": "Real-time conferencing (Zoom, WebRTC). Requires low latency and low jitter; minor packet loss manifests as transient artifact.",
        "weights": {
            "latency_sensitivity": 0.85,
            "jitter_sensitivity": 0.85,
            "loss_tolerance": 0.60,
            "reliability_need": 0.30,
        },
    },
    "Streaming": {
        "name": "Buffered Video Streaming",
        "description": "On-demand media (Netflix, YouTube). Uses client buffer to smooth jitter, but requires reliable, ordered byte delivery.",
        "weights": {
            "latency_sensitivity": 0.30,
            "jitter_sensitivity": 0.25,
            "loss_tolerance": 0.10,
            "reliability_need": 0.90,
        },
    },
    "FileTransfer": {
        "name": "File Transfer / Download",
        "description": "Bulk data transfer (FTP, HTTP download, database dump). Zero tolerance for data corruption or missing bytes.",
        "weights": {
            "latency_sensitivity": 0.10,
            "jitter_sensitivity": 0.10,
            "loss_tolerance": 0.00,
            "reliability_need": 1.00,
        },
    },
    "WebAPI": {
        "name": "Web & REST API Requests",
        "description": "Transactional web traffic (HTTP/JSON APIs). Requires reliable request/response cycles without lost payloads.",
        "weights": {
            "latency_sensitivity": 0.50,
            "jitter_sensitivity": 0.20,
            "loss_tolerance": 0.05,
            "reliability_need": 0.95,
        },
    },
    "IoT": {
        "name": "IoT Telemetry / Sensor Data",
        "description": "Periodic sensor updates (temperature, GPS). Single missing packet is quickly superseded by the next telemetry reading.",
        "weights": {
            "latency_sensitivity": 0.40,
            "jitter_sensitivity": 0.20,
            "loss_tolerance": 0.70,
            "reliability_need": 0.25,
        },
    },
}


def get_profile(name: str) -> dict:
    """Retrieve a profile dictionary by key."""
    return PROFILES.get(name, PROFILES["Gaming"])
