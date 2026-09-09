# NetPulse — TCP vs UDP Performance Analyzer & Smart Recommender

> An application-layer transport protocol measurement suite, benchmark runner, interactive Streamlit dashboard, Wireshark PCAP analyzer, and weighted recommendation engine built in Python.

---

## Features

- **Core Transport Sockets (`tcp/`, `udp/`):**
  - TCP client/server with 4-byte big-endian length-prefix framing.
  - UDP client/server with socket timeout handling and lost packet sequence detection.
  - 16-byte fixed binary header (`8B uint64 seq` + `8B double timestamp`).

- **Measurement Engine (`metrics/`):**
  - Accurately measures Transmission Time (sec), Average RTT (ms), Goodput Throughput (Mbps), Packet Loss (%), and RFC 3550 Jitter (ms).

- **Automated Experiment Runner (`run_experiments.py`):**
  - Runs clean, process-isolated benchmarks across 4 packet sizes (`64`, `256`, `512`, `1024` bytes) for TCP and UDP.
  - Saves results incrementally to `data/results.csv`.

- **Interactive Streamlit Web Dashboard (`dashboard/`):**
  - Side-by-side metric tables per packet size.
  - 5 Matplotlib visualization charts (Transmission Time, Throughput, RTT, Loss, 2x2 Grid).
  - One-click experiment re-execution controls from the UI sidebar.

- **Wireshark PCAP Analyzer (`analyzer/`):**
  - Offline Scapy-based `.pcap` / `.pcapng` parser.
  - Detects TCP 3-way handshakes (`SYN` -> `SYN/ACK` -> `ACK`), flag breakdown, and packet sizes.
  - Includes `--generate-sample` synthetic PCAP generator.

- **Smart Protocol Recommender (`recommender/`):**
  - Rule-based multi-criteria recommendation engine for 6 workload profiles (`Gaming`, `VideoCall`, `Streaming`, `FileTransfer`, `WebAPI`, `IoT`).
  - Outputs recommended protocol (`TCP` vs `UDP`), confidence score (50%–99%), score breakdown, and human-readable decision reasons.

---

## Quick Start Guide

### 1. Requirements & Installation
Ensure you have Python 3.8+ installed. Install project dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run Unit Tests
```bash
python3 -m unittest discover tests -v
```

### 3. Run Benchmark Suite
```bash
# Run experiment matrix and append to data/results.csv
python3 run_experiments.py

# Wipe past results and run fresh
python3 run_experiments.py --fresh
```

### 4. Launch Interactive Web Dashboard
```bash
streamlit run dashboard/app.py
```
Open `http://localhost:8501` in your browser.

### 5. Run Wireshark PCAP Analyzer
```bash
# Generate sample capture and analyze
python3 analyzer/pcap_parser.py --generate-sample

# Analyze your custom capture file from Wireshark
python3 analyzer/pcap_parser.py path/to/your_capture.pcap
```

---

## Project Structure

```
NetPulse/
├── protocol.py               # Shared binary wire format (16B header pack/unpack)
├── config.yaml               # Experiment configuration parameters
├── run_experiments.py        # Automated benchmark orchestrator (TCP & UDP matrix)
├── DEMO_GUIDE.md             # Faculty demonstration script & presentation workflow
├── DECISIONS.md              # Append-only architecture & design decision log
├── PROGRESS.md               # Milestone tracking document
├── tcp/
│   ├── client.py             # Length-prefixed TCP client
│   └── server.py             # Length-prefixed TCP echo server
├── udp/
│   ├── client.py             # UDP client with socket timeouts
│   └── server.py             # UDP datagram echo server
├── metrics/
│   └── engine.py             # Metric calculations (RTT, Throughput, Loss, Jitter)
├── recommender/
│   ├── profiles.py           # 6 application profiles & weighted priorities
│   └── engine.py             # Rule-based scoring & confidence engine
├── analyzer/
│   └── pcap_parser.py        # Scapy offline PCAP parser & handshake detector
├── dashboard/
│   └── app.py                # Streamlit web UI & Matplotlib visualization app
├── data/
│   └── results.csv           # Experiment results dataset
└── tests/
    ├── test_metrics.py       # Unit tests for metric formulas
    └── test_recommender.py   # Unit tests for recommendation engine
```

---

## Faculty Demonstration Guide
For a step-by-step 10-minute presentation guide and Q&A reference for college faculty, refer to **`DEMO_GUIDE.md`**.
