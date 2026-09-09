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
- TCP echo server (`tcp/server.py`):
  - Accepts one connection, reads length-prefixed packets, echoes each back
  - Closes cleanly on FIN
- TCP echo client (`tcp/client.py`):
  - Connects, sends N packets, waits for each echo before sending next
  - Records `sent_at` and `received_at` per packet
  - Accepts packet size as CLI argument
- UDP echo server (`udp/server.py`):
  - Binds and echoes every datagram back to sender's address
  - Runs until Ctrl+C
- UDP echo client (`udp/client.py`):
  - Sends N datagrams, waits for each echo with configurable timeout
  - Marks timed-out packets as lost (`received_at = None`)
  - Reports lost sequence numbers at the end
- ✅ Tested both on `127.0.0.1` — all packets echo correctly

## What's Next — Phase 2
- Create `metrics/engine.py` with `compute_metrics(records)`
  - Transmission time, average RTT, throughput (Mbps), packet loss %, jitter
- Wire metrics into TCP and UDP clients
- Add unit tests with fabricated data (`tests/test_metrics.py`)
