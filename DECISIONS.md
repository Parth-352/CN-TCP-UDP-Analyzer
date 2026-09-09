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
