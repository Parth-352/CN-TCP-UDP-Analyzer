# NetPulse — Progress Tracker

## Phase 0 — Project Setup ✅
- Created project folder structure: `tcp/`, `udp/`, `metrics/`, `recommender/`, `simulator/`, `dashboard/`, `data/`, `reports/`, `tests/`, `analyzer/`
- Added `requirements.txt` with all dependencies
- Added `config.yaml` with experiment parameters
- Added `.gitignore` for Python projects, `.pcap`, and `data/*.csv`
- Created `PROGRESS.md` (this file)
- Created `DECISIONS.md` with append-only rule and entry format
- Initialized git repository

## Phase 1 — TCP + UDP Core Communication ✅
- Created shared wire format module (`protocol.py`):
  - 16-byte header = 8-byte sequence number + 8-byte double timestamp
  - `build_packet(seq, size)` and `parse_header(data)` functions
- TCP echo server/client (`tcp/server.py`, `tcp/client.py`)
- UDP echo server/client (`udp/server.py`, `udp/client.py`)
- Tested both on `127.0.0.1` — all packets echo correctly

## Phase 2 — Measurement Engine ✅
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
  - Constant RTT → jitter = 0
- ✅ All 6 tests pass
- ✅ Live tested TCP and UDP with metrics output on `127.0.0.1`

## Phase 3 — Automation & Bulk Experiments ✅
- Created `run_experiments.py`:
  - Automatically loops over packet sizes `[64, 256, 512, 1024]` and protocols `[tcp, udp]`
  - Starts server as a clean process (`subprocess.Popen`), runs client, records metrics, terminates server
  - Appends metrics to `data/results.csv`
  - `--fresh` CLI flag wipes CSV before running
  - Uses pandas to display a neat summary table after all runs complete
- ✅ Tested full 8-experiment matrix (100 packets each, 800 packets total)
- ✅ Results cleanly saved to `data/results.csv`

## What's Next — Phase 4
- Build interactive Streamlit dashboard (`dashboard/app.py`)
- Display comparison summary tables
- Plot interactive charts for Throughput vs Packet Size, Latency (RTT) vs Packet Size, Jitter vs Packet Size
- Include protocol selection sidebar & metric filters

