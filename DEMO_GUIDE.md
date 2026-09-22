# NetPulse — Complete Workflow & Faculty Demonstration Guide

> **Project Title:** NetPulse — Real-Time Transport Protocol (TCP vs UDP) Performance Analyzer & Recommendation Engine  
> **Course:** Computer Networks / Data Communications  

---

## Executive Summary & System Workflow

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

## Detailed Technical Workflow (How Each Module Works)

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
* **Tab 1 (Metric Tables & Comparison):** Per-packet-size side-by-side metric comparison table and full raw CSV dataset preview.
* **Tab 2 (Performance Graphs):** 5 Matplotlib charts:
  1. Packet Size vs Transmission Time (sec)
  2. Packet Size vs Throughput (Mbps)
  3. Packet Size vs Average RTT (ms)
  4. Packet Size vs Packet Loss (%)
  5. 2x2 Multi-Panel Performance Dashboard Grid
* **Tab 3 (Smart Protocol Recommender):** Multi-criteria recommendation engine supporting 6 application profiles with scoring and confidence metrics.
* **Tab 4 (Wireshark PCAP Inspector):** Integrated packet analyzer supporting custom `.pcap` / `.pcapng` file uploads, target port filtering (setting `0` inspects all ports), sample generator button, and TCP 3-way handshake detection.
* **Sidebar Controls:** Interactive triggers to re-run experiments directly from the browser.

### 5. Wireshark PCAP Analyzer (`analyzer/pcap_parser.py`)
* Reads `.pcap` / `.pcapng` capture files using **Scapy**.
* Filters for traffic on target experiment port (default `5001`) or inspects all traffic when port is set to `0`.
* Displays per-packet headers, packet sizes, and TCP flags (`SYN`, `ACK`, `PSH`, `FIN`).
* Tracks and counts completed TCP 3-way handshakes (`SYN` $\rightarrow$ `SYN/ACK` $\rightarrow$ `ACK`).
* Analyzes `.pcap` and `.pcapng` files exported from Wireshark through the dashboard or CLI.

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

## Step-by-Step Faculty Demonstration Script

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

1. **Show Tab 1 ("Metric Tables & Comparison"):**
   - Use the packet size dropdown selector (e.g., `1024` bytes).
   - Point out the side-by-side comparison matrix of Transmission Time, RTT, Throughput, Loss, and Jitter.
2. **Show Tab 2 ("Performance Graphs"):**
   - Scroll through the 5 Matplotlib visualization charts.
   - Highlight the **Combined Performance Dashboard Grid** showing all metrics simultaneously.
3. **Show Tab 4 ("Wireshark PCAP Inspector"):**
   - Demonstrate dragging and dropping a custom `.pcap` / `.pcapng` file into the UI file uploader.
   - Adjust the **Port Filter** input (`0` to view all network traffic, or `5001` for experiment traffic).
   - Upload the Wireshark `.pcap` or `.pcapng` file in the PCAP uploader.
   - Review summary metrics (Total Packets, TCP vs UDP count, Average packet sizes, Complete TCP Handshakes).
4. **Demonstrate Sidebar Controls:**
   - **Start Fresh Benchmark:** Wipes old CSV records and executes a fresh benchmark suite.
   - **Run Additional Benchmark:** Appends new test runs to existing CSV data.
   - **Clear Dataset:** Instantly deletes all stored dataset entries without running new experiments.

---

### Step 4: Smart Protocol Recommender Demo (2 minutes)
Click on **Tab 3 ("Smart Protocol Recommender")**:

1. **Select Profile 1: `Gaming` (Real-Time Online Gaming)**
   - Show that the engine recommends **UDP** with high confidence ($\sim 85\%-90\%$).
   - Point out the decision reasons: Gaming requires sub-50ms latency and tolerates packet drops over retransmission delays.
2. **Select Profile 2: `FileTransfer` (Bulk Data Transfer)**
   - Show that the engine immediately switches recommendation to **TCP** with high confidence ($\sim 95\%$).
   - Point out the decision reasons: Zero loss tolerance requires TCP's guaranteed byte delivery.

---

### Step 5: Wireshark PCAP & Packet Analysis Demo (2 minutes)
Open a new terminal and run the offline PCAP analyzer CLI:
```bash
# Analyze a custom Wireshark capture via CLI
python3 analyzer/pcap_parser.py path/to/capture.pcap
```
* **What to say:**
  > *"To analyze protocol behavior at the packet capture layer, NetPulse includes a Scapy-based Wireshark parser accessible via CLI and integrated into our Streamlit dashboard. Here we inspect packet headers, flag combinations, and handshake sequences."*
* **Key Observations to Point Out:**
  - Explain how the parser detects the **TCP 3-Way Handshake** (`SYN` $\rightarrow$ `SYN/ACK` $\rightarrow$ `ACK`).
  - Compare TCP flag annotations (`[SYN]`, `[PSH+ACK]`, `[FIN+ACK]`) against UDP datagrams (`Len=256`).

---

## Quick Reference Commands Cheat Sheet

| Task | Command |
|---|---|
| **Run Unit Tests** | `python3 -m unittest discover tests -v` |
| **Run Experiments** | `python3 run_experiments.py` |
| **Run Fresh Experiments** | `python3 run_experiments.py --fresh` |
| **Launch Dashboard** | `streamlit run dashboard/app.py` |
| **Run Wireshark Analyzer** | `python3 analyzer/pcap_parser.py path/to/capture.pcap` |
| **Inspect Custom PCAP** | `python3 analyzer/pcap_parser.py path/to/capture.pcap` |

---

## Two-Laptop Same-Network Demo (LAN Testing)

This section walks through running NetPulse across **two laptops on the same Wi-Fi / LAN network**:

| Role | Device | What it does |
|------|--------|-------------|
| **Server** | 🍎 **Mac** | Runs the TCP & UDP echo servers |
| **Client** | 💻 **Asus** | Runs the benchmark + Streamlit dashboard |

This demonstrates real network latency, jitter, and loss instead of loopback-only measurements.

### Prerequisites

- Both laptops (Mac & Asus) are connected to the **same Wi-Fi network** (e.g., your college Wi-Fi or a mobile hotspot).
- Both laptops have the NetPulse project cloned/copied with Python 3 and all dependencies installed (`pip install -r requirements.txt`).
- **Wireshark** is installed on the Mac (download from [wireshark.org](https://www.wireshark.org/download.html)). You will use it to live-capture the benchmark traffic on the server side.
- No firewall is blocking port **5001** (or whichever port you use) on the Mac.

### Step 1: Find the Mac's LAN IP (🍎 Mac)

Open Terminal on the Mac and run:

```bash
ipconfig getifaddr en0
```
*(Use `en1` if `en0` shows nothing — `en0` is usually Wi-Fi on Mac.)*

> **Write down this IP** — you'll need it on the Asus. Example: `192.168.1.42`

---

### Step 2: Allow Incoming Connections Through the Firewall (🍎 Mac)

The macOS firewall usually allows incoming connections by default. If it doesn't, go to:
`System Settings → Network → Firewall → Options` → add Python or allow incoming connections.

---

### Step 3: Start the Servers Manually (🍎 Mac)

Open **two terminal windows** on the Mac and start both servers:

**Terminal 1 — TCP Server:**
```bash
cd path/to/CN\ Project
python3 tcp/server.py
```
You should see:
```
[TCP Server] Listening on 0.0.0.0:5001
```

**Terminal 2 — UDP Server:**
```bash
cd path/to/CN\ Project
python3 udp/server.py
```
You should see:
```
[UDP Server] Listening on 0.0.0.0:5001
```

> **Note:** Both servers already bind to `0.0.0.0` (all network interfaces) by default via `config.yaml`, so they accept connections from the Asus over the LAN.

---

### Step 4: Update config.yaml on the Asus (💻 Asus)

On the **Asus**, edit `config.yaml` to point to the Mac's IP:

```yaml
# Change this from 127.0.0.1 to the Mac's LAN IP
server_ip: "192.168.1.42"    # ← Replace with your Mac's actual IP from Step 1
```

Leave everything else unchanged. The `server_bind` setting on the Asus side doesn't matter — only the Mac (server) uses it.

---

### Step 5: Verify Connectivity (💻 Asus)

Before running experiments, confirm the Asus can reach the Mac:

```bash
ping 192.168.1.42
```

You should see replies. If not, check:
- Both laptops (Mac & Asus) are on the same network.
- The firewall on the Mac isn't blocking.
- The IP address is correct.

---

### Step 6: Start Wireshark Capture Before the Benchmark (🍎 Mac)

Open **Wireshark** on the Mac **before** running the benchmark so it captures all the incoming traffic on the server side:

1. Launch Wireshark on the Mac.
2. On the start screen, **double-click your Wi-Fi interface** (usually `en0` on Mac) to begin a live capture.
3. Packets will start scrolling immediately — that's fine, the real traffic comes when you run the benchmark.
4. *(Optional but recommended)* To reduce noise, apply a **capture filter** before starting:
   ```
   port 5001
   ```
   This captures only traffic on port 5001 — ignoring all background Wi-Fi traffic.

> **Leave Wireshark running.** You will stop it after the benchmark finishes.

---

### Step 7: Run the Benchmark from the Asus (💻 Asus)

> **Important:** Do **NOT** run `run_experiments.py` on the Mac. The experiment runner detects that `server_ip` is not `127.0.0.1` and skips auto-launching servers — it expects the servers to already be running on the Mac (which you started in Step 3).

```bash
python3 run_experiments.py --fresh
```

You will see the Asus sending packets across the real Wi-Fi network. **On the Mac's terminals**, you'll see the echo logs:
```
[TCP Server] Connection accepted from ('192.168.1.55', 52341)
[TCP Server] Echoing packet seq=0
[TCP Server] Echoing packet seq=1
...
```

Meanwhile, **Wireshark on the Mac** will show live packets flowing — you'll see TCP SYN/ACK handshakes and UDP datagrams in real time.

> **What to say to faculty:**
> *"Notice we are now benchmarking across a real wireless LAN link. The Asus sends packets over Wi-Fi to the Mac running the echo servers, which echoes them back. Wireshark is capturing every single packet on the wire — we'll analyze this capture in our dashboard next."*

---

### Step 8: Stop Wireshark & Save the Capture (🍎 Mac)

Once the benchmark finishes:

1. Go back to Wireshark on the Mac and click the **red square (■) Stop** button in the toolbar.
2. Go to **File → Save As…**
3. Save the file as `capture.pcap` — remember where you save it. Use the format **Wireshark/tcpdump/… - pcap** (the default).

> **Tip:** If you didn't use a capture filter earlier, you can apply a **display filter** before saving to keep only the relevant traffic — go to **File → Export Specified Packets…** and choose "Displayed" to export only the filtered packets:
> ```
> tcp.port == 5001 || udp.port == 5001
> ```

---

### Step 9: Launch the Dashboard and Show Results (🍎 Mac)

Since the Mac already has the Wireshark capture, run the dashboard directly on the Mac — no need to transfer files:

```bash
streamlit run dashboard/app.py
```

Open the dashboard in the browser on the Mac (`http://localhost:8501`) and walk through:

1. **Tab 1 — Metric Tables:** Show the side-by-side TCP vs UDP comparison — RTT values will now be in the **0.5–5 ms range** instead of the sub-0.1 ms loopback values.
2. **Tab 2 — Performance Graphs:** The throughput and RTT graphs reflect real network conditions (Wi-Fi congestion, interference, etc.).
3. **Tab 3 — Protocol Recommender:** The recommendations are now based on real network data rather than loopback-ideal conditions.
4. **Tab 4 — Wireshark PCAP Inspector:**
   - Click **"Upload Custom PCAP File"** and select the `capture.pcap` you saved from Wireshark in Step 8.
   - Set the **Port Filter** to `5001` (should be the default).
   - Walk faculty through the results:
     - **Total Packets Captured** — how many packets flowed during the benchmark.
     - **TCP Packets vs UDP Datagrams** — the protocol distribution pie chart.
     - **Complete Handshakes** — the number of TCP 3-way handshakes detected (`SYN → SYN/ACK → ACK`).
     - **Parsed Packet Stream Table** — show the per-packet view with flags, source/destination, and payload sizes.

> **What to say to faculty:**
> *"We captured this traffic live using Wireshark while the benchmark was running. Our PCAP Inspector uses Scapy to parse every packet — here you can see the TCP 3-way handshake sequences, the echo packets flowing back and forth, and the UDP datagrams. Notice TCP has significantly more overhead packets (SYN, ACK, FIN) compared to UDP's fire-and-forget approach."*

> **Key talking points for faculty:**
> - *"TCP RTT is higher than UDP because of the three-way handshake and ACK overhead."*
> - *"UDP may now show actual packet loss if the Wi-Fi link is congested — something impossible to observe on loopback."*
> - *"Jitter values are higher and more realistic on Wi-Fi due to wireless medium access contention."*
> - *"The Wireshark capture gives us ground-truth packet-level visibility — we can verify our application-layer metrics against raw network behavior."*

> **Note:** The `results.csv` data was generated on the Asus. If Tab 1–3 show "no data", copy `data/results.csv` from the Asus to the Mac's `data/` folder (AirDrop or shared folder), then refresh the dashboard.

---

### Step 10: Revert config.yaml After the Demo (💻 Asus)

After the demo, change `server_ip` back to localhost on the Asus so single-device mode works again:

```yaml
server_ip: "127.0.0.1"
```

---

### Troubleshooting

| Problem | Solution |
|---|---|
| `Connection refused` on TCP client | Check TCP server is running on the Mac and firewall allows port 5001. |
| UDP packets all showing as `*** LOST ***` | Firewall is blocking UDP. Allow port 5001/UDP on the Mac. |
| `ping` works but experiments fail | Ensure `config.yaml` on the Asus has the correct Mac IP and both server scripts are running on the Mac. |
| Very high RTT (>100ms) on same Wi-Fi | Normal on a congested college Wi-Fi. Mention this as a real-world observation to faculty. |
| `Address already in use` on Mac | Another process is using port 5001. Run `lsof -i :5001` on the Mac or change `server_port` in `config.yaml` on **both** laptops. |
| Wireshark shows no packets on Mac | Make sure you selected the correct interface (`en0` for Wi-Fi). Also check that the capture filter (if used) matches the actual port. |
| Wireshark asks for permission on Mac | Go to **System Settings → Privacy & Security → Full Disk Access** (or run `sudo chmod +x /dev/bpf*` once). Wireshark also installs a helper tool — say Yes to the installer prompt. |
| PCAP upload in Tab 4 shows no packets | Make sure the **Port Filter** matches the port used (5001). Set it to `0` to show all traffic and verify the capture file is not empty. |

---

## Expected Q&A Questions from Faculty & Answers

**Q1: How do you measure RTT accurately without clock synchronization issues?**
> *Answer:* We use echo-based RTT measurement. The client records `time.time()` before sending and records arrival time when the server echoes the packet back. Because both timestamps come from the same client clock, our measurement is immune to inter-host clock skew.

**Q2: How do you handle TCP stream boundaries?**
> *Answer:* TCP is a byte stream with no concept of packet boundaries. We implement 4-byte big-endian length-prefix framing (`!I`) before every payload, allowing the server to read exact message boundaries.

**Q3: How is Jitter computed in NetPulse?**
> *Answer:* We implement the RFC 3550 standard formula—the mean absolute difference of consecutive RTT samples $E[|\text{RTT}_{i+1} - \text{RTT}_i|]$. This measures latency variation between consecutive packets rather than standard deviation, which would unfairly penalize consistent high latency.

**Q4: Why process isolation for servers during benchmarks?**
> *Answer:* Running servers in separate `subprocess.Popen` processes guarantees that socket buffers, lingering TCP connection states, or Python thread GIL contention never leak across experiment iterations.

**Q5: How does the Wireshark PCAP Inspector work without root/sudo permissions?**
> *Answer:* The parser operates offline using Scapy to parse exported `.pcap` or `.pcapng` capture files recorded via Wireshark or generated by our synthetic capture module. This avoids requiring elevated kernel packet-sniffing permissions (`sudo`) while providing full packet header, flag, and handshake visibility.

**Q6: Why are the RTT values different when testing across two laptops vs localhost?**
> *Answer:* On localhost (`127.0.0.1`), packets never leave the kernel — they are looped back in the network stack with near-zero latency. When we test across two laptops on Wi-Fi, packets traverse the real wireless medium: they go through the Wi-Fi radio, the access point, and back. This adds real-world latency from wireless medium access, buffering, interference, and physical propagation — giving us meaningful RTT, jitter, and loss measurements that reflect how TCP and UDP actually behave in a production network.

**Q7: How does the experiment runner know whether to start the server automatically or expect a remote server?**
> *Answer:* The runner checks `server_ip` in `config.yaml`. If it is `127.0.0.1` or `localhost`, it spawns the server as a subprocess automatically. If it is any other IP (like a LAN address such as `192.168.1.42`), it assumes the server is already running on that remote machine and connects directly — this is how the two-laptop demo works.

**Q8: Why do you capture Wireshark on the Mac (server) instead of the Asus (client)?**
> *Answer:* Capturing on the server-side Mac lets us see the complete traffic picture from the receiving end — including the TCP 3-way handshake initiation arriving from the Asus, the server's SYN/ACK response, and the full echo traffic in both directions. It also demonstrates that we can verify our application-layer metrics against raw packet-level data captured independently on a different machine. You could capture on either side (or both) — the traffic is symmetric for an echo server — but having it on the Mac keeps the Asus focused on running the benchmark without Wireshark competing for CPU/network resources.

---
*Created for NetPulse Demonstration & Evaluation.*
