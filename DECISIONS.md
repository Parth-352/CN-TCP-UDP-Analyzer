# NetPulse — Decision Log

> **Rule: append-only.** Never delete or rewrite past entries. If a later
> phase reverses an earlier decision, add a new entry that says so and
> references the old one — don't erase the history.

Each entry follows this format:

```
## [Phase N] <short decision title>
Decision: <what was chosen>
Alternatives considered:
  - <alternative> — rejected because <reason>
  - <alternative> — rejected because <reason>
Why this one: <reason this approach won>
```

Only log real forks in the road — protocol/wire-format choices, library
choices, algorithm/formula choices, architecture choices. Skip trivial
naming or style choices.

---

## [Phase 0] YAML for experiment configuration

Decision: Use `config.yaml` (with PyYAML) for all experiment parameters.

Alternatives considered:
  - `config.json` — rejected because YAML supports comments, which are useful
    for documenting what each parameter means and what values are reasonable.
  - Hardcoded constants in Python — rejected because changing parameters
    would require editing source code, making experiments less reproducible
    and harder to version-control separately from logic.
  - `.env` file — rejected because experiment config is structured (lists of
    packet sizes, nested settings) and env files are flat key-value pairs.

Why this one: YAML is human-readable, supports comments and lists natively,
and PyYAML is a single lightweight dependency. Config stays separate from
code, so experiments are reproducible by sharing one file.

## [Phase 0] Streamlit for dashboard (over Tkinter)

Decision: Use Streamlit as the sole dashboard framework.

Alternatives considered:
  - Tkinter — rejected because it requires significantly more boilerplate
    for tables and charts, has no built-in DataFrame rendering, and looks
    dated without heavy styling effort.
  - Flask/Dash — rejected because Dash adds Plotly as a dependency and
    Flask requires writing HTML templates; both are heavier than needed
    for a demo dashboard.

Why this one: Streamlit turns a Python script into a web dashboard with
minimal code, has built-in support for pandas DataFrames and matplotlib
charts, and is well-suited for a college project demo. Less code means
fewer bugs and more time spent on the actual networking logic.

---

## [Phase 1] Wire format: 8-byte seq + 8-byte timestamp header on every packet

Decision: Every packet (TCP and UDP alike) carries a fixed 16-byte header —
8 bytes for a big-endian sequence number (`uint64`) and 8 bytes for a
`double` timestamp (`time.time()`) — followed by zero-padded payload.

Alternatives considered:
  - No header / rely on arrival order — rejected because UDP does not
    guarantee ordering or delivery, so without an explicit sequence number
    there is no way to detect loss, reordering, or compute per-packet RTT.
  - Variable-length header with JSON metadata — rejected because parsing
    overhead is unnecessary; fixed 16 bytes keeps pack/unpack trivial and
    the overhead constant regardless of payload size.
  - Separate control channel for sequence tracking — rejected because it
    adds a second socket and synchronization complexity with no benefit for
    a loopback echo test.

Why this one: A fixed binary header is minimal overhead, works identically
for TCP and UDP, and makes loss, RTT, and jitter all computable from the
same per-packet record without any additional bookkeeping.

## [Phase 1] Echo-based RTT measurement (vs. one-way timestamps)

Decision: Measure RTT by having the server echo the entire packet back to
the client. The client records `sent_at` before sending and `received_at`
when the echo arrives; RTT = `received_at - sent_at`.

Alternatives considered:
  - One-way timestamp difference (client sends `time.time()`, server records
    its own `time.time()` on arrival) — rejected because client and server
    clocks are not guaranteed to be synchronized, even on localhost. NTP
    accuracy is millisecond-level at best, which is the same order as the
    latencies we're measuring.
  - External clock sync (PTP / GPS) — rejected, completely impractical for
    a college project running on one laptop.

Why this one: Echo-based RTT uses a single clock (the client's), so it's
immune to clock skew. It mirrors how `ping` measures latency and is the
standard approach for application-level RTT.

## [Phase 1] TCP framing: 4-byte length prefix

Decision: TCP packets are framed with a 4-byte big-endian length prefix
before the packet payload, so the server knows exactly how many bytes to
read for each message.

Alternatives considered:
  - Fixed-size reads (always read `packet_size` bytes) — rejected because
    the server would need to know the packet size in advance or receive it
    out of band, and it breaks if we ever want variable-size packets.
  - Delimiter-based framing (e.g. newline or sentinel) — rejected because
    binary payload can contain any byte value, so no byte is safe as a
    delimiter without escaping, which adds complexity.
  - Read-until-close (one message per connection) — rejected because it
    would require a new TCP connection per packet, paying the three-way
    handshake overhead every time.

Why this one: Length-prefix framing is the standard approach for TCP message
boundaries — simple, robust, and works for any payload content.

## [Phase 1] UDP loss detection: per-packet socket timeout

Decision: The UDP client sets a `socket.timeout` (default 2 s from config)
and waits for each echo reply individually. If the timeout fires, that
sequence number is marked as lost (`received_at = None`).

Alternatives considered:
  - Fire-and-forget (send all packets, then collect replies) — rejected
    because without a per-packet wait, out-of-order replies make it hard to
    match which echo belongs to which send, and you can't detect loss until
    after all sends are done, which complicates flow control.
  - Separate receiver thread — rejected because it adds threading
    complexity for a simple sequential test; per-packet blocking is
    straightforward enough for the scale we're running (100 packets).

Why this one: Blocking per-packet with a timeout is the simplest correct
approach — every packet is either echoed or timed out before the next one
is sent, so sequence matching is trivial and loss is detected immediately.
