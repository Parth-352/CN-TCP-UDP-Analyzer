# NetPulse — Progress Tracker

## Phase 0 — Project Setup [COMPLETED]
- Created project folder structure: `tcp/`, `udp/`, `metrics/`, `recommender/`, `simulator/`, `dashboard/`, `data/`, `reports/`, `tests/`, `analyzer/`
- Added `requirements.txt` with all dependencies
- Added `config.yaml` with experiment parameters
- Added `.gitignore` for Python projects, `.pcap`, and `data/*.csv`
- Created `PROGRESS.md` (this file)
- Created `DECISIONS.md` with append-only rule and entry format
- Initialized git repository

## Phase 1 — TCP + UDP Core Communication [COMPLETED]
- Created shared wire format module (`protocol.py`):
  - 16-byte header = 8-byte sequence number + 8-byte double timestamp
  - `build_packet(seq, size)` and `parse_header(data)` functions
- TCP echo server/client (`tcp/server.py`, `tcp/client.py`)
- UDP echo server/client (`udp/server.py`, `udp/client.py`)
- Tested both on `127.0.0.1` — all packets echo correctly

## Phase 2 — Measurement Engine [COMPLETED]
- Created `metrics/engine.py` with `compute_metrics(records, packet_size)`:
  - `transmission_time_sec` — wall-clock span from first to last send
  - `avg_rtt_ms` — mean RTT of successfully echoed packets
  - `throughput_mbps` — total bytes acked × 8 / elapsed time
  - `packet_loss_pct` — fraction of packets with no echo
  - `jitter_ms` — mean absolute difference of consecutive RTTs (RFC 3550-style)
- Added `print_metrics()` helper for formatted console output
- Wired metrics into both `tcp/client.py` and `udp/client.py`
- Created `tests/test_metrics.py` with 6 unit tests:
  - Basic no-loss (5 packets, known RTTs)
  - With packet loss (2 of 5 lost)
  - All packets lost
  - Empty records
  - Single packet
  - Constant RTT -> jitter = 0
- All 6 tests pass
- Live tested TCP and UDP with metrics output on `127.0.0.1`

## Phase 3 — Automation & Bulk Experiments [COMPLETED]
- Created `run_experiments.py`:
  - Automatically loops over packet sizes `[64, 256, 512, 1024]` and protocols `[tcp, udp]`
  - Starts server as a clean process (`subprocess.Popen`), runs client, records metrics, terminates server
  - Appends metrics to `data/results.csv`
  - `--fresh` CLI flag wipes CSV before running
  - Uses pandas to display a neat summary table after all runs complete
- Tested full 8-experiment matrix (100 packets each, 800 packets total)
- Results cleanly saved to `data/results.csv`

## Phase 4 — Graphs & Interactive Dashboard [COMPLETED]
- Created Streamlit web dashboard (`dashboard/app.py`):
  - Metric comparison view: side-by-side TCP vs UDP summary per selected packet size
  - Raw results DataFrame view with CSV export capability
  - 5 Matplotlib visualization graphs:
    1. Packet Size vs Transmission Time (sec)
    2. Packet Size vs Throughput (Mbps)
    3. Packet Size vs Average RTT (ms)
    4. Packet Size vs Packet Loss (%)
    5. Combined 2x2 Multi-Panel Performance Grid
  - Interactive sidebar controls: "Run Experiments" and "Run Fresh" triggers calling `run_experiments.py` as a subprocess
- Installed `streamlit` and `matplotlib` dependencies
- Verified `dashboard/app.py` compiles cleanly and renders metrics

## Phase 5 — Wireshark / Packet Analysis [COMPLETED]
- Created Scapy-based PCAP parser (`analyzer/pcap_parser.py`):
  - Filters and parses `.pcap` / `.pcapng` files exported from Wireshark for configured server port
  - Extracts per-packet metadata: Protocol, Src/Dst IP & Port, Packet Size, TCP Flags, Seq/Ack numbers, UDP lengths
  - Automatically detects full TCP 3-way handshakes (`SYN` -> `SYN/ACK` -> `ACK`)
  - Displays summary statistics: Total TCP/UDP packet counts, average packet sizes, handshake counts
  - Built-in `--generate-sample` synthetic PCAP generator for testing and standalone demonstration
- Installed `scapy` dependency
- Tested parsing on sample PCAP: detected TCP handshakes and UDP datagrams accurately

## Phase 6 — Protocol Recommendation Engine [COMPLETED]
- Created workload profiles (`recommender/profiles.py`):
  - Defined 6 application profiles (Gaming, VideoCall, Streaming, FileTransfer, WebAPI, IoT) with 4 weighted sensitivities: latency, jitter, loss tolerance, reliability
- Created recommendation engine (`recommender/engine.py`):
  - Implemented `recommend(metrics, profile)` with weighted scoring (0 to 100) for TCP and UDP
  - Computed normalized confidence % (50% to 99%) and human-readable decision reasons
- Created unit tests (`tests/test_recommender.py`):
  - 6 unit tests covering all profile scenarios, confidence bounds, and loss adaptation
  - All 12 project unit tests pass
- Integrated Recommender into Streamlit UI (`dashboard/app.py`):
  - Added "Smart Protocol Recommender" tab with profile selection, weight metrics, score breakdown, and decision explanations

## Phase 7 — Final Documentation & Faculty Presentation Guide [COMPLETED]
- Created `DEMO_GUIDE.md`:
  - System architecture block diagram and module breakdown
  - 5-step faculty presentation script (Unit tests -> Benchmark runner -> Streamlit Dashboard -> Recommender -> Wireshark PCAP)
  - Quick reference commands cheat sheet & anticipated faculty Q&A section
- Created `README.md`:
  - Full project feature breakdown, installation guide, quick start instructions, and directory map
- Final project audit complete! All 7 phases implemented, tested, and documented.
