# Twenty Minds Decision Engine — Cumulative Web Inc

Run any decision through **20 named adversarial perspectives**, then synthesize with **recorded dissent**. A CWI machine-reasoning product.

- **Live interactive demo:** https://cumulativewebinc.github.io/cwi-twenty-minds/ — runs the real protocol (manual backend) in your browser: brief → 20 minds → distinctness guard → synthesis → downloadable `report.md` + `report.json`.
- **Installable CLI:** `cli/` — stdlib-only Python, `manual` / `ollama` / `openai-compat` backends, per-mind model routing, distinctness guard, mandatory-dissent synthesis. 40/40 tests green.

```bash
git clone https://github.com/CumulativeWebInc/cwi-twenty-minds.git
cd cwi-twenty-minds/cli
python3 -m twenty_minds "Should we ship Friday?" --fact "Team of 3, all senior" --fact "\$0 budget"
python3 -m twenty_minds --list-perspectives
```

## Files

| Path | What |
|---|---|
| `index.html` | Interactive web demo (the manual-backend flow, in-browser) |
| `twenty-minds.js` | Protocol port: perspectives, prompt builder, distinctness guard (Jaccard ≥ 0.90), synthesis validation, report builders — parity-verified against the Python engine |
| `perspectives.json` | The 20 perspectives, machine-readable (generated from `cli/twenty_minds/protocol.py`) |
| `cli/` | Full Python CLI: `twenty_minds/` package, `tests/`, `README.md`, `PRODUCT.md` |
| `brand/logo.jpg` | CWI logo |

## Honest limits

This engine structures reasoning; it does not verify it. Verdicts are only as good as the minds behind them — in manual mode, that's you. Never present a report as verified truth. No network calls, no telemetry, stdlib only.

## Contact

© 2026 Cumulative Web Inc · licensing/integration: [hp@cumulativeweb.com](mailto:hp@cumulativeweb.com) · pricing on request, never published without approval.
