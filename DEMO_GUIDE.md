# ⚡ NetPulse — Complete Workflow & Faculty Demonstration Guide

> **Project Title:** NetPulse — Real-Time Transport Protocol (TCP vs UDP) Performance Analyzer & Recommendation Engine  
> **Course:** Computer Networks / Data Communications  

---

## 📖 Executive Summary & System Workflow

NetPulse is an application-layer network benchmarking tool built to evaluate, measure, visualize, and analyze the performance trade-offs between **TCP** (Transmission Control Protocol) and **UDP** (User Datagram Protocol) under identical local network conditions.

```
+-----------------------------------------------------------------------------------+
|                                 NETPULSE ARCHITECTURE                             |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [ 1. Core Sockets ]      [ 2. Measurement Engine ]     [ 3. Benchmark Runner ]   |
|   - protocol.py            - metrics/engine.py           - run_experiments.py     |
|   - 16B Binary Header      - RTT, Throughput (Mbps),     - 4 Packet Sizes         |
|   - TCP Length Prefix        Packet Loss (%), Jitter       (64, 256, 512, 1024B)   |
|   - UDP Socket Timeout     - RFC 3550 Jitter Calc        - Subprocess Isolation   |
|                                                                                   |
+------------------------------------------+----------------------------------------+
                                           | Output to data/results.csv
                                           v
+-----------------------------------------------------------------------------------+
|  [ 4. Dashboard ]              [ 5. PCAP Analyzer ]     [ 6. Smart Recommender ]   |
|   - dashboard/app.py            - analyzer/pcap_parser   - recommender/engine.py  |
|   - Streamlit Web UI            - Scapy Offline Parser   - 6 Application Profiles |
|   - 5 Matplotlib Graphs         - 3-Way Handshake Track  - Weighted Scoring Model |
|   - Metric Tables & Export      - Sample PCAP Generator  - Confidence % + Reasons |
+-----------------------------------------------------------------------------------+
```

---

## 🛠 Detailed Technical Workflow (How Each Module Works)

### 1. Packet Binary Wire Format (`protocol.py`)
Every message sent across TCP or UDP uses a custom 16-byte binary header followed by a zero-padded payload:
* **Bytes 0–7 (`!Q`):** 64-bit unsigned integer packet sequence number.
* **Bytes 8–15 (`d`):** 64-bit double-precision floating-point timestamp (`time.time()`).
* **TCP Framing:** Prepend a 4-byte big-endian payload length integer before sending to ensure exact boundary framing over stream sockets.
* **UDP Loss Detection:** Per-packet `socket.timeout` (2.0s). If the echo reply does not arrive within the timeout window, the packet sequence is marked as lost (`received_at = None`).

### 2. Measurement Engine (`metrics/engine.py`)
Measures 5 core network parameters:
1. **Transmission Time (sec):** Wall-clock duration from first packet send to last echo receipt.
2. **Average RTT (ms):** Mean round-trip latency ($\text{RTT} = t_{\text{receive}} - t_{\text{send}}$) of successfully echoed packets.
3. **Throughput (Mbps):** Goodput rate calculated as:
   $$\text{Throughput} = \frac{\text{Packets Received} \times \text{Packet Size (bytes)} \times 8}{\text{Elapsed Seconds} \times 1,000,000}$$
4. **Packet Loss (%):** Percentage of sent packets that received no echo reply.
5. **Jitter (ms):** RFC 3550-style inter-packet delay variation computed as the mean absolute difference of consecutive RTT samples:
   $$\text{Jitter} = \frac{1}{N-1} \sum_{i=1}^{N-1} |\text{RTT}_{i+1} - \text{RTT}_i|$$

### 3. Automated Benchmark Matrix (`run_experiments.py`)
* Executes an automated 8-experiment benchmark across packet sizes `[64, 256, 512, 1024]` bytes for both `TCP` and `UDP`.
* Uses `subprocess.Popen` to launch fresh server instances per run and kill them cleanly in a `finally` block to prevent socket buffer contamination.
* Persists results to `data/results.csv` (with a `--fresh` flag to reset data).

### 4. Interactive Streamlit Dashboard (`dashboard/app.py`)
* **Tab 1 (Metric Tables):** Per-packet-size side-by-side metric comparison table and full raw CSV dataset preview.
* **Tab 2 (Visual Benchmarks):** 5 Matplotlib charts:
  1. Packet Size vs Transmission Time (sec)
  2. Packet Size vs Throughput (Mbps)
  3. Packet Size vs Average RTT (ms)
  4. Packet Size vs Packet Loss (%)
  5. 2x2 Multi-Panel Performance Dashboard Grid
* **Sidebar Controls:** Interactive triggers to re-run experiments directly from the browser.

### 5. Wireshark PCAP Analyzer (`analyzer/pcap_parser.py`)
* Reads `.pcap` / `.pcapng` capture files using **Scapy**.
* Filters for traffic on target experiment port (default `5000`).
* Displays per-packet headers, packet sizes, and TCP flags (`SYN`, `ACK`, `PSH`, `FIN`).
* Tracks and counts completed TCP 3-way handshakes (`SYN` $\rightarrow$ `SYN/ACK` $\rightarrow$ `ACK`).
* Includes `--generate-sample` CLI flag to generate a synthetic binary capture file for instant offline demonstration.

### 6. Smart Protocol Recommendation Engine (`recommender/`)
* **Workload Profiles (`recommender/profiles.py`):** Defines 6 workload profiles with normalized sensitivity weights ($0.0$ to $1.0$):
  - **Gaming:** High Latency (0.95), High Jitter (0.90), High Loss Tolerance (0.80), Low Reliability (0.15)
  - **VideoCall:** High Latency (0.85), High Jitter (0.85), Moderate Loss Tolerance (0.60), Low Reliability (0.30)
  - **Streaming:** Low Latency (0.30), High Reliability (0.90)
  - **FileTransfer:** Zero Loss Tolerance (0.00), Maximum Reliability (1.00)
  - **WebAPI:** High Reliability (0.95), Low Loss Tolerance (0.05)
  - **IoT:** High Loss Tolerance (0.70), Low Reliability (0.25)
* **Scoring Engine (`recommender/engine.py`):** Calculates continuous TCP vs UDP scores ($0$ to $100$) and normalized confidence % ($50\%$ to $99\%$) with human-readable rationale.

---

## 🎓 Step-by-Step Faculty Demonstration Script

Follow this step-by-step flow to give a 10-minute presentation to your professor or faculty panel.

### Step 1: Verification & Unit Tests (1 minute)
Open a terminal in the project directory and run the test suite:
```bash
python3 -m unittest discover tests -v
```
* **What to say:**
  > *"We have implemented comprehensive unit tests for our measurement engine and rule-based recommender. All 12 unit tests pass cleanly, validating our RTT, jitter, loss calculation formulas, and scoring logic."*

---

### Step 2: Automated Benchmark Execution (2 minutes)
Execute the experiment runner CLI with a fresh dataset wipe:
```bash
python3 run_experiments.py --fresh
```
* **What to say:**
  > *"Here we run an automated benchmark suite across 8 experiment conditions—4 packet sizes (64, 256, 512, and 1024 bytes) across both TCP and UDP protocols. Notice how each server is launched in a process-isolated subprocess to ensure zero socket state pollution."*
* **Key Observations to Point Out:**
  - UDP achieves faster average RTT because it does not pay TCP's connection management overhead.
  - TCP guarantees 0% packet loss due to socket buffering and retransmissions.

---

### Step 3: Interactive Streamlit Dashboard Demo (3 minutes)
Launch the web dashboard:
```bash
streamlit run dashboard/app.py
```
*(The browser will automatically open to `http://localhost:8501`)*

1. **Show Tab 1 ("📊 Metric Tables & Comparison"):**
   - Use the packet size dropdown selector (e.g., `1024` bytes).
   - Point out the side-by-side comparison matrix of Transmission Time, RTT, Throughput, Loss, and Jitter.
2. **Show Tab 2 ("📈 Performance Graphs"):**
   - Scroll through the 5 Matplotlib visualization charts.
   - Highlight the **Combined Performance Dashboard Grid** showing all metrics simultaneously.
3. **Demonstrate Sidebar Interactivity:**
   - Click **"🚀 Run Experiments (Append)"** in the sidebar.
   - Show how Streamlit dynamically reruns the benchmark and refreshes the charts automatically.

---

### Step 4: Smart Protocol Recommender Demo (2 minutes)
Click on **Tab 3 ("🎯 Smart Protocol Recommender")**:

1. **Select Profile 1: `Gaming` (Real-Time Online Gaming)**
   - Show that the engine recommends **UDP** with high confidence ($\sim 85\%-90\%$).
   - Point out the decision reasons: Gaming requires sub-50ms latency and tolerates packet drops over retransmission delays.
2. **Select Profile 2: `FileTransfer` (Bulk Data Transfer)**
   - Show that the engine immediately switches recommendation to **TCP** with high confidence ($\sim 95\%$).
   - Point out the decision reasons: Zero loss tolerance requires TCP's guaranteed byte delivery.

---

### Step 5: Wireshark PCAP & Packet Analysis Demo (2 minutes)
Open a new terminal and run the offline PCAP analyzer:
```bash
python3 analyzer/pcap_parser.py --generate-sample
```
* **What to say:**
  > *"To analyze protocol behavior at the packet capture layer, NetPulse includes a Scapy-based Wireshark parser. Here we generate and inspect a synthetic network capture file."*
* **Key Observations to Point Out:**
  - Explain how the parser detects the **TCP 3-Way Handshake** (`SYN` $\rightarrow$ `SYN/ACK` $\rightarrow$ `ACK`).
  - Compare TCP flag annotations (`[SYN]`, `[PSH+ACK]`, `[FIN+ACK]`) against UDP datagrams (`Len=256`).

---

## ⚡ Quick Reference Commands Cheat Sheet

| Task | Command |
|---|---|
| **Run Unit Tests** | `python3 -m unittest discover tests -v` |
| **Run Experiments** | `python3 run_experiments.py` |
| **Run Fresh Experiments** | `python3 run_experiments.py --fresh` |
| **Launch Dashboard** | `streamlit run dashboard/app.py` |
| **Run Wireshark Analyzer** | `python3 analyzer/pcap_parser.py --generate-sample` |

---

## 💡 Expected Q&A Questions from Faculty & Answers

**Q1: How do you measure RTT accurately without clock synchronization issues?**
> *Answer:* We use echo-based RTT measurement. The client records `time.time()` before sending and records arrival time when the server echoes the packet back. Because both timestamps come from the same client clock, our measurement is immune to inter-host clock skew.

**Q2: How do you handle TCP stream boundaries?**
> *Answer:* TCP is a byte stream with no concept of packet boundaries. We implement 4-byte big-endian length-prefix framing (`!I`) before every payload, allowing the server to read exact message boundaries.

**Q3: How is Jitter computed in NetPulse?**
> *Answer:* We implement the RFC 3550 standard formula—the mean absolute difference of consecutive RTT samples $E[|\text{RTT}_{i+1} - \text{RTT}_i|]$. This measures latency variation between consecutive packets rather than standard deviation, which would unfairly penalize consistent high latency.

**Q4: Why process isolation for servers during benchmarks?**
> *Answer:* Running servers in separate `subprocess.Popen` processes guarantees that socket buffers, lingering TCP connection states, or Python thread GIL contention never leak across experiment iterations.

---
*Created for NetPulse Demonstration & Evaluation.*
