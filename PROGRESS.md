# NetPulse — Progress Tracker

## Phase 0 — Project Setup ✅
- Created project folder structure: `tcp/`, `udp/`, `metrics/`, `recommender/`, `simulator/`, `dashboard/`, `data/`, `reports/`, `tests/`, `analyzer/`
- Added `requirements.txt` with all dependencies
- Added `config.yaml` with experiment parameters
- Added `.gitignore` for Python projects, `.pcap`, and `data/*.csv`
- Created `PROGRESS.md` (this file)
- Created `DECISIONS.md` with append-only rule and entry format
- Initialized git repository

## What's Next — Phase 1
- Implement shared wire format module (seq + timestamp + payload)
- Build TCP client/server echo pair
- Build UDP client/server echo pair
- Manual test on 127.0.0.1
