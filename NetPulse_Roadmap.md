# NetPulse — TCP vs UDP Analyzer: Corrected Roadmap & Claude Code Prompts

This is the PRD's plan with six fixes baked directly into the spec (not just noted) — wire format, RTT method, Wireshark workflow, network simulator honesty, jitter formula, and dashboard tech. Phases below already reflect these; nothing extra to remember before you start.

## What changed vs. the original PRD (for your own notes)

| Area | Original | Corrected |
|---|---|---|
| UDP loss detection | Implied, not specified | App-layer packet carries an explicit sequence number + timestamp, so gaps are detectable |
| RTT | "Transmission time" only | Explicit request→echo protocol on **both** TCP and UDP, same wire format, so RTT is comparable |
| Wireshark | Implied Python-controlled capture | Manual capture in Wireshark GUI → export `.pcap` → Scapy script parses it offline. `tshark` scripted capture is optional stretch only |
| Network simulator | Implied real traffic shaping | Explicit software-level delay/drop injected in the client/server code, documented as such (no `tc netem` claim) |
| Jitter | Unspecified formula | Fixed to: mean of absolute differences between consecutive successful RTT samples (RFC 3550-style) |
| Dashboard | Tkinter *or* Streamlit | Streamlit only — less code, built-in tables/charts |

Everything else (metrics list, MVP/innovation split, architecture, recommendation engine as rule-based) is unchanged from your PRD.

---

## How to use this with Claude Code

- Work **one phase at a time**. Don't paste the whole roadmap and say "build it all."
- After each phase, **run and manually verify** against that phase's checklist before moving to the next prompt — don't let Claude Code chain straight into Phase 2 before Phase 1 actually works over a real socket.
- Keep a running `PROGRESS.md` in the repo; ask Claude Code to update it after each phase so context isn't lost between sessions.
- Keep a running `DECISIONS.md` (set up in Phase 0, updated every phase after — see below) logging every real design choice, the alternatives considered, and why the alternatives lost. This is your viva ammunition and also stops Claude Code from silently flip-flopping on a choice it already made in an earlier session.
- Ask Claude Code to commit to git after each phase completes cleanly.

### DECISIONS.md — what belongs in it

Not every line of code is a "decision." Log it when there was a real fork in the road, i.e. more than one reasonable way to do something and you picked one. Examples from this project: wire format layout, echo-vs-fire-and-forget for RTT, pcap-parsing-offline vs scripted tshark capture, software-level vs OS-level impairment, jitter formula choice, Streamlit vs Tkinter, rule-based vs ML recommender, CSV vs SQLite for storage. Skip logging things like variable names or which loop construct was used — that's noise.

Each entry should follow one format, e.g.:

```
## [Phase 1] Wire format includes explicit sequence number + timestamp
Decision: every packet (TCP and UDP) carries an 8-byte seq + 8-byte timestamp
before the payload.
Alternatives considered:
  - No seq number, rely on arrival order — rejected, UDP doesn't guarantee
    order or delivery so loss/RTT can't be measured without it.
  - Separate control channel for seq tracking — rejected, adds complexity
    with no benefit for a loopback test.
Why this one: minimal overhead, works identically for TCP and UDP, makes
loss/RTT/jitter all computable from the same log.
```

Tell Claude Code explicitly: **never delete or rewrite past entries, only append.** If a later phase reverses an earlier decision, add a new entry that says so and references the old one — don't erase the history.

---

## Phase 0 — Project Setup

**Checklist**
- [ ] `git init`, `.gitignore` (venv, `__pycache__`, `.pcap`, `results.csv` if you want it ignored)
- [ ] `requirements.txt`: `pandas`, `matplotlib`, `streamlit`, `scapy` (optional), `pyshark` (optional)
- [ ] Folder structure: `tcp/`, `udp/`, `metrics/`, `recommender/`, `simulator/`, `dashboard/`, `data/`, `reports/`
- [ ] `config.yaml` or `config.json` for experiment parameters (packet sizes, packet counts, host/port) instead of hardcoding
- [ ] `PROGRESS.md` created (what's done / what's next)
- [ ] `DECISIONS.md` created with the logging format and the append-only rule spelled out at the top

**Prompt for Claude Code**
```
Set up a new Python project called NetPulse (TCP vs UDP performance analyzer).
Create this structure:
  tcp/, udp/, metrics/, recommender/, simulator/, dashboard/, data/, reports/, tests/
Add requirements.txt with pandas, matplotlib, streamlit, scapy, pyshark.
Add a config.yaml with fields: server_ip, server_port, packet_sizes (list, bytes),
num_packets, protocol_timeout_sec.
Add a .gitignore for Python projects plus data/*.csv and *.pcap.

Add a PROGRESS.md file that you will update after every phase with what's
done and what's next.

Add a DECISIONS.md file that you will APPEND to (never rewrite or delete
past entries) at the end of every phase from now on. Each entry logs one
real design decision — something where more than one reasonable approach
existed — in this format:

## [Phase N] <short decision title>
Decision: <what was chosen>
Alternatives considered:
  - <alternative> — rejected because <reason>
  - <alternative> — rejected because <reason>
Why this one: <reason this approach won>

Don't log trivial things like variable naming. Log real forks in the road:
protocol/wire-format choices, library choices, algorithm/formula choices,
architecture choices, anything where you picked X over Y for a reason.

Don't write any networking logic yet — just scaffolding.
```

---

## Phase 1 — TCP + UDP Core Communication

**Checklist**
- [ ] Shared wire format module: `seq (8 bytes)`, `timestamp (8 bytes, double)`, `payload`
- [ ] TCP server: accepts connection, echoes back each received packet
- [ ] TCP client: connects, sends N packets of size S, waits for echo, disconnects (FIN) cleanly
- [ ] UDP server: receives datagrams, echoes back to sender address
- [ ] UDP client: sends N datagrams of size S, listens for echoes with a timeout (to detect loss)
- [ ] Manual test: run server, run client, confirm packets round-trip on `127.0.0.1`

**Prompt for Claude Code**
```
In tcp/ and udp/, implement client-server echo apps using Python's socket module.

Wire format (shared, put in a common module): each packet is
[8 bytes big-endian sequence number][8 bytes double timestamp][payload bytes].

TCP:
- tcp/server.py: listens on server_ip:server_port, accepts one connection,
  reads packets, echoes each one back immediately, closes cleanly on FIN.
- tcp/client.py: connects, sends num_packets packets of packet_size bytes
  (from config.yaml), waits for the echo of each before sending the next,
  records send time and echo-receive time per packet, closes connection.

UDP:
- udp/server.py: binds to server_ip:server_port, receives datagrams, echoes
  each back to the sender's address.
- udp/client.py: sends num_packets datagrams of packet_size bytes, waits for
  each echo with a socket timeout (e.g. 2 sec) — if no echo arrives before
  timeout, mark that sequence number as lost and move on to the next packet.

Both clients should just print per-packet send/receive timestamps and any
lost sequence numbers to stdout for now — no metrics computation yet, that's
Phase 2. Test manually against 127.0.0.1 and show me the commands to run.

Before finishing, append an entry to DECISIONS.md for this phase (e.g. the
wire format layout, echo-based RTT design, timeout-based UDP loss detection)
and update PROGRESS.md.
```

---

## Phase 2 — Measurement Engine

**Checklist**
- [ ] `metrics/engine.py`: given per-packet timestamps + loss list, compute:
  - Transmission time (total)
  - RTT per packet + average RTT
  - Throughput (Mbps)
  - Packet loss %
  - Jitter (mean absolute difference of consecutive RTTs)
- [ ] TCP and UDP clients call this engine and print a results dict
- [ ] Unit tests with fabricated timestamp data (known expected output)

**Prompt for Claude Code**
```
Create metrics/engine.py with a function compute_metrics(records) where
records is a list of dicts: {seq, sent_at, received_at_or_None}.

It should return a dict with:
- transmission_time_sec (last sent_at - first sent_at, or total wall time passed in)
- avg_rtt_ms
- throughput_mbps (total bytes acked / total time)
- packet_loss_pct (count of received_at_or_None is None / total records * 100)
- jitter_ms (mean of abs differences between consecutive successful RTTs)

Wire this into tcp/client.py and udp/client.py so after a run they print this
metrics dict. Add tests/test_metrics.py with a hand-crafted records list and
asserted expected values for each metric.

Before finishing, append an entry to DECISIONS.md for the jitter formula
choice (mean abs. diff of consecutive RTTs, and why not stddev or max-min)
and update PROGRESS.md.
```

---

## Phase 3 — Multiple Experiments + Data Storage

**Checklist**
- [ ] `run_experiments.py`: loops over packet sizes in `config.yaml`, runs TCP then UDP for each, saves each run's metrics to `data/results.csv`
- [ ] CSV columns match PRD section 20: `Protocol, PacketSize, Packets, Time, RTT, Throughput, Loss, Jitter`
- [ ] Re-running experiments appends, doesn't overwrite (or offers a `--fresh` flag)

**Prompt for Claude Code**
```
Create run_experiments.py that:
1. Reads packet_sizes and num_packets from config.yaml.
2. For each packet size, starts the TCP server as a subprocess, runs the TCP
   client, stops the server, then does the same for UDP.
3. Appends each run's metrics as one row to data/results.csv with columns:
   Protocol, PacketSize, Packets, TransmissionTime, AvgRTT, Throughput,
   PacketLoss, Jitter, Timestamp.
4. Supports a --fresh flag to wipe results.csv before running.
Print a summary table (using pandas) at the end.

Before finishing, append an entry to DECISIONS.md for CSV vs SQLite (why
CSV was chosen for this scale) and any subprocess-vs-thread choice for
running server+client together, then update PROGRESS.md.
```

---

## Phase 4 — Graphs + Dashboard

**Checklist**
- [ ] `dashboard/app.py` (Streamlit): loads `data/results.csv`
- [ ] Table view matching PRD section 10 layout (TCP vs UDP columns)
- [ ] Graph 1: Packet Size vs Transmission Time (line, TCP vs UDP)
- [ ] Graph 2: Packet Size vs Throughput
- [ ] Graph 3: Packet Size vs RTT
- [ ] Graph 4: UDP Packet Loss vs Packet Size
- [ ] Graph 5: combined overview (small multiples or radar-ish summary)
- [ ] Button to trigger `run_experiments.py` from the dashboard (optional, nice for demo)

**Prompt for Claude Code**
```
Create dashboard/app.py as a Streamlit app that:
1. Loads data/results.csv with pandas.
2. Shows a comparison table styled like this (TCP column vs UDP column, per
   packet size selected via a dropdown): Time, RTT, Throughput, Loss, Jitter.
3. Renders 5 matplotlib charts, each TCP vs UDP as two lines/bars across
   packet size: Transmission Time, Throughput, RTT, UDP Packet Loss, and one
   combined summary chart.
4. Add a sidebar button "Run new experiment" that calls run_experiments.py
   as a subprocess and refreshes the page when done.
Keep the UI simple — this is a college demo dashboard, not a product.

Before finishing, append an entry to DECISIONS.md for Streamlit vs Tkinter
and update PROGRESS.md.
```

---

## Phase 5 — Wireshark / Packet Analysis

**Checklist**
- [ ] Document manual workflow: start Wireshark capture on loopback → run one experiment → stop capture → save as `data/capture.pcap`
- [ ] `analyzer/pcap_parser.py` using Scapy: reads `.pcap`, extracts src/dst IP, src/dst port, protocol, size, TCP flags or UDP marker, timestamp
- [ ] Output formatted like PRD section 13 (per-packet card or table)
- [ ] Short written note in the report about SYN/SYN-ACK/ACK/FIN sequence observed for TCP vs plain DATA datagrams for UDP

**Prompt for Claude Code**
```
Create analyzer/pcap_parser.py using Scapy that:
1. Takes a path to a .pcap file as argument.
2. Iterates packets, and for each TCP or UDP packet on the configured port,
   prints a formatted block with: Protocol, Source IP, Destination IP,
   Source Port, Destination Port, Packet Size, TCP Flags (if TCP), Sequence
   Number (if TCP), Timestamp.
3. At the end, prints a short summary: total TCP packets, total UDP packets,
   TCP handshake pairs detected (SYN -> SYN/ACK -> ACK), and average packet
   size per protocol.
This script only reads an existing .pcap file captured manually in
Wireshark — it does not try to start/stop capture itself.

Before finishing, append an entry to DECISIONS.md for manual-capture-then-
parse vs scripted tshark capture (why offline parsing was chosen) and
update PROGRESS.md.
```

Manual step you do yourself (tell Claude Code this is expected, don't ask it to automate): open Wireshark, filter `tcp.port == 5000 or udp.port == 5000`, start capture, run `run_experiments.py`, stop capture, File → Export Specified Packets → `data/capture.pcap`.

---

## Phase 6 — Protocol Recommendation Engine (Innovation)

**Checklist**
- [ ] `recommender/profiles.py`: define the 6 application profiles (Gaming, Video Call, Streaming, File Transfer, Web/API, IoT) each as a dict of weighted priorities for {latency, jitter, loss_tolerance, reliability}
- [ ] `recommender/engine.py`: rule-based scoring function — given measured {latency, loss, jitter, throughput} + chosen profile, output `{protocol, confidence_pct, reasons: [...]}`
- [ ] Confidence score formula defined and documented (simple weighted-sum normalized to %, not ML)
- [ ] Unit tests: feed known-good-UDP conditions + Gaming profile → expect UDP; feed known-bad-loss conditions + File Transfer profile → expect TCP
- [ ] Wire into dashboard: dropdown to pick profile, show recommendation card (PRD section 15 layout)

**Prompt for Claude Code**
```
Create recommender/profiles.py with 6 profiles (Gaming, VideoCall,
Streaming, FileTransfer, WebAPI, IoT), each a dict of weights (0-1) for:
latency_sensitivity, jitter_sensitivity, loss_tolerance, reliability_need.

Create recommender/engine.py with recommend(metrics, profile) -> dict where
metrics has measured latency_ms, loss_pct, jitter_ms, throughput_mbps.
Implement a transparent rule-based scoring function (no ML/LLM):
- Score TCP and UDP separately by combining profile weights against
  thresholds you define explicitly in code comments (e.g. loss_tolerance
  low + measured loss > 1% -> penalize UDP heavily).
- Return {protocol: "TCP"|"UDP", confidence_pct: int, reasons: [strings]}.
- confidence_pct should be the normalized score gap between TCP and UDP
  scores, not a random number — show the formula in a comment.

Add tests/test_recommender.py: assert Gaming profile + low latency/loss
conditions recommends UDP; assert FileTransfer profile + any packet loss
recommends TCP.

Add a section to dashboard/app.py: dropdown to pick an application profile,
displays the recommendation card with protocol, confidence %, and reasons,
styled similar to a simple bordered summary box.

Before finishing, append an entry to DECISIONS.md for rule-based scoring vs
ML/decision-tree (why rule-based was chosen for explainability) and the
confidence_pct formula, then update PROGRESS.md.
```

---

## Phase 7 — Network Simulation + Polish

**Checklist**
- [ ] `simulator/impair.py`: wraps send/receive with artificial delay (sleep) and probabilistic drop, parameterized as Normal / Poor / Very Poor presets from PRD section 16
- [ ] Clearly document in code + report that this is software-level impairment inside the app, not OS-level `tc netem`
- [ ] Re-run experiments under each preset, store results with a `NetworkCondition` column
- [ ] Dynamic recommendation table (PRD section 17): re-run recommender every N seconds under changing simulated conditions, log to a small table/CSV
- [ ] Final polish: README with setup + run instructions, a `report/` folder with generated tables/graphs for the writeup, requirements.txt finalized, code cleanup

**Prompt for Claude Code**
```
Create simulator/impair.py with a function apply_impairment(condition_name)
that returns (delay_ms, drop_probability) for presets: "Normal" (0ms, 0%),
"Poor" (150ms, 5%), "VeryPoor" (300ms, 15%). Wire this into udp/client.py
and tcp/client.py as an optional --condition flag: before sending each
packet, sleep for delay_ms and, for UDP only, randomly skip sending with
drop_probability (simulating loss at the source).

Update run_experiments.py to optionally loop over all three conditions and
tag each results.csv row with a NetworkCondition column.

Create simulator/dynamic_monitor.py: runs a loop that every 10 seconds picks
a network condition (cycle Normal -> Poor -> VeryPoor -> Normal), runs a
small UDP+TCP test, calls the recommender, and appends
{time, condition, recommendation} to data/dynamic_log.csv. Add a simple
Streamlit view for this log as a table.

Finally, write a README.md with setup (venv, pip install -r requirements.txt),
how to run each phase, and how to reproduce the demo for viva. Clean up any
dead code and finalize requirements.txt.

Before finishing, append an entry to DECISIONS.md for software-level
impairment vs OS-level tc/netem (why software-level was chosen for
portability), then update PROGRESS.md. Also do a final pass over
DECISIONS.md and confirm every phase's entries are still present and
unedited — this file is the project's audit trail for the viva.
```

---

## Viva-prep checklist (do this after Phase 7, not before)

- [ ] Can explain jitter/RTT/throughput formulas from memory, not just "the code computes it"
- [ ] Can explain *why* UDP loses packets and TCP doesn't at the transport layer, referencing the actual SYN/ACK sequence seen in your own capture
- [ ] Can explain why the network simulator is software-level, if asked
- [ ] Can explain the recommendation engine's scoring logic line by line (no black box)
- [ ] Have one clean `results.csv` and one clean `capture.pcap` saved as backup, in case a live demo glitches
- [ ] Skim `DECISIONS.md` once end-to-end — if an evaluator asks "why did you choose X," you should be able to point to the exact entry instead of improvising
- [ ] 5-minute demo script written out: start dashboard → show table → show graphs → switch profile → show recommendation → (optional) show dynamic monitor
