# Twenty Minds Decision Engine

A real, working CLI that runs a hard decision through **20 named adversarial
perspectives** — each writes a distinct one-sentence verdict plus exactly one
risk — then synthesizes a decision with the dissent recorded, a confidence
level, and a kill-rule check.

Built by Cumulative Web Inc (CWI). Stdlib only — **zero dependencies, $0**.

## Install

You need Python 3.8+. Nothing else.

```bash
cd twenty-minds-engine
python3 -m twenty_minds --list-perspectives   # sanity check, no network
```

No `pip install`, no virtualenv, no API keys required.

## Quickstart — value in under 5 minutes

The default backend is **manual**: the engine prints each mind's prompt and you
type (or paste) the verdict and risk. This works with $0 and no keys, and it
is how most operators should start — *you* are the minds.

```bash
python3 -m twenty_minds "Should we launch the new single this Friday?" \
  --fact "The distributor needs 48h lead time." \
  --fact "The playlist curator replies within a day." \
  --fact "The artist is free to promote all weekend." \
  --out ./run-001
```

Answer 20 verdict/risk pairs (one sentence each), then write the synthesis
when prompted — the dissent field is **mandatory**; the engine rejects a
synthesis without it. When you finish, you get:

```
  report.md:   run-001/report.md
  report.json: run-001/report.json
```

`report.md` is the human-readable decision record (question, facts, all 20
verdicts + risks, synthesis). `report.json` is the machine-readable version
(schema `1.0.0`) for dashboards, agents, and audit trails.

Non-interactive demo (pipes answers in — useful for testing):

```bash
printf 'Verdict %s.\nRisk %s.\n' {1..20} {1..20} > /dev/null  # placeholder only
```

Better: generate the 45 answer lines with a script and pipe them in, e.g.

```bash
python3 - <<'EOF' | python3 -m twenty_minds "Ship v1?" --fact "Tests pass." --fact "No price published." --out ./demo
for i in range(1, 21):
    print(f"The {i}th mind verdict is to proceed with caution on point {i}.")
    print(f"The {i}th mind risk is untested assumption number {i}.")
print("Proceed with the v1 launch.")
print("The engineer and the data scientist carried it.")
print("The skeptic dissents: one more check is still needed.")
print("medium")
print("yes")
EOF
```

## Backends

| Backend | Flag | What it does |
|---|---|---|
| `manual` (default) | `--backend manual` | Prints each prompt; operator answers via stdin. $0, no keys. |
| `ollama` | `--backend ollama --model llama3.1` | POSTs to `http://localhost:11434/api/generate`. Fails gracefully with setup instructions if Ollama isn't running. |
| `openai-compat` | `--backend openai-compat --model NAME --base-url URL` | POSTs to any OpenAI-compatible `/chat/completions` endpoint. API key read **only** from env var (`--env-var`, default `OPENAI_API_KEY`). Never logged, never printed, never written to files. |

**Per-mind routing** — different minds can run on different models
("combined minds of machines"):

```bash
python3 -m twenty_minds "A vs B?" --fact "F1." \
  --backend manual \
  --route '{"Skeptic":"ollama","Data scientist":"ollama"}' \
  --model llama3.1
```

**Who writes the synthesis** — `--synthesis manual` (default, operator writes
it) or `--synthesis ollama` / `--synthesis openai-compat` (a backend drafts
it from the 20 verdicts; the mandatory-dissent rule is still enforced).

Full option reference: `python3 -m twenty_minds --help`.

## The 20 perspectives

Skeptic · Data scientist · User advocate · Contrarian · Engineer · Economist ·
Security reviewer · Child-of-five explainer · 10-year historian ·
Devil's accountant · Field operator · Systems thinker · Risk underwriter ·
Open-source maintainer · Negotiator · Time traveler (2036) ·
First-principles physicist · Ethicist · Competitor analyst · Black's chair

See `--list-perspectives` for each mind's one-line role.

## Protocol rules (enforced in code)

- **1–5 facts.** More than 5 is rejected — minds argue from the brief, not
  from fresh research.
- **Distinct verdicts.** A normalized-similarity guard flags exact and
  near-duplicate verdicts in the report; duplicates get rewritten until
  distinct.
- **Dissent is mandatory.** `build_synthesis` raises `ValueError` on an empty
  dissent field. A synthesis without a minority view is a press release.
- **Kill rule.** The report records whether the run changed your pre-run
  lean. If 20 minds don't change the outcome twice in a row, drop to 5 minds
  (Skeptic, Data scientist, User advocate, Devil's accountant, Black's chair)
  until a decision proves otherwise.

## Running the tests

```bash
python3 -m unittest discover -s tests
```

40 tests, all passing: protocol rules, backend interface + graceful failures,
and a full end-to-end CLI run through piped stdin that writes and validates
both reports.

## HONESTY

Read this before you trust a report.

- **This tool structures reasoning; it does not make models — or people —
  smarter.** A sharper protocol cannot fix a shallow brief or a careless
  mind. Garbage in, twenty garbage verdicts out.
- **Reports are only as good as the minds behind them.** In manual mode, that
  means you. With LLM backends, the verdicts inherit the model's blind spots,
  hallucinations, and training cutoff. Nothing here fact-checks anything.
- **Never present a report as verified truth.** It is a decision *record*:
  what was asked, what was known, what 20 perspectives said, what was
  decided, and who dissented. Treat it as an artifact for accountability,
  not as evidence.
- **The dissent rule exists because consensus is cheap.** If every mind
  agrees, you didn't need twenty minds — re-check whether the brief
  smuggled the conclusion in.
- **No telemetry, no network** except to backends you explicitly configure
  (your localhost Ollama or your own API endpoint). Your questions, facts,
  and verdicts never leave your machine unless you point a backend at a
  remote endpoint yourself.

## Layout

```
twenty-minds-engine/
├── twenty_minds/
│   ├── __init__.py      public API
│   ├── __main__.py      python -m twenty_minds entry point
│   ├── protocol.py      perspectives, DecisionBrief, MindVerdict, Synthesis,
│   │                    distinctness guard, run_protocol
│   ├── prompts.py       per-mind prompt builder + synthesis prompt/parse
│   ├── backends.py      Backend interface; manual / ollama / openai-compat
│   ├── report.py        report.md + report.json writers
│   └── cli.py           argparse CLI
├── tests/
│   ├── test_protocol.py
│   ├── test_backends.py
│   └── test_cli.py
├── README.md
└── PRODUCT.md
```

## License

Proprietary — Cumulative Web Inc. All rights reserved.
