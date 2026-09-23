# PRODUCT.md — Twenty Minds Decision Engine v1.0.0

## Purpose statement

Twenty Minds Decision Engine productizes CWI's adversarial 20-perspective
decision protocol as real, sellable software: any hard, ambiguous, or
high-stakes decision goes in as a question plus 1–5 facts, and comes out as a
decision report with 20 distinct verdicts, 20 risks, a synthesis, and the
dissent on the record. It exists so that consequential calls — launches,
deals, architecture bets, kill-rule reviews — are made *through* opposition
instead of around it.

## Real audience

- **Founders and indie hackers** facing irreversible or expensive calls
  (pricing, pivots, launches, partnerships) who need structured opposition
  before committing.
- **AI-agent operators** who want a deterministic, auditable deliberation
  step in an agent pipeline — the JSON report (schema `1.0.0`) drops straight
  into dashboards, logs, and audit trails.
- **Teams** that need a shared decision record: what was asked, what was
  known, who said what, what was decided, and who dissented.

## Result

A decision report — `report.md` (human) + `report.json` (machine-readable) —
containing the question, the facts, 20 verdicts with risks, a
distinctness-flag section, and a synthesis with decision, why,
recorded dissent, confidence, and whether the run changed the operator's
pre-run lean. The dissent is structurally mandatory: the engine raises
rather than emit a synthesis without it.

## Mechanism

1. Operator states the decision as a question with 1–5 facts (more is
   rejected; minds argue from the brief, not from fresh research).
2. Each of the 20 named perspectives (Skeptic … Black's chair) receives a
   strict prompt — role + question + numbered facts + exactly-one-sentence
   verdict / exactly-one-sentence risk, no extra prose.
3. A Backend turns each prompt into a response. Three ship in v1: `manual`
   (interactive operator, default, $0, no keys), `ollama` (localhost LLM),
   `openai-compat` (operator's own endpoint; key from env var only, never
   logged). Per-mind routing lets different minds run on different models.
4. The distinctness guard (normalized exact match + ≥0.90 Jaccard token
   similarity) flags duplicate verdicts in the report.
5. The synthesis is written by the operator or drafted by a backend, with
   the mandatory-dissent rule enforced in code.
6. Reports are written; the CLI prints both paths on completion.

## Verification

- 40-test suite (`python3 -m unittest discover -s tests`), all passing:
  20 perspectives present with unique names; distinctness guard flags exact
  duplicates and near-duplicates and passes distinct verdicts; synthesis
  builder raises without dissent; brief rejects 0 and 6+ facts; stub-backed
  full 20-verdict run end-to-end; graceful Ollama-down and missing-key
  failures; CLI smoke (`--list-perspectives` exits 0) plus a real
  piped-stdin CLI run that writes and validates both reports.
- Stdlib only: zero dependencies, no network except to user-configured
  backends, no telemetry, no keys in files.
- Dogfood path: CWI runs Twenty Minds on every project per the standing
  mandate; this engine is the tool that runs it.

## Kill rule

**Fewer than 5 external uses with receipts in 30 days → delist.**
"External" means a paying or registered user outside CWI; "receipts" means a
generated report (md+json pair) the user can show. If the engine isn't being
reached for, it doesn't earn its shelf space — cut it and fold the protocol
back into a skill.

## Price

**TBD — pending Black's approval. Do not publish a price.** No price is set,
shown, or implied anywhere in the product, docs, or reports. No payment
flow exists in v1.

## What v1 is NOT

- Not a model and not model training: it structures reasoning; it does not
  make any model smarter (see README's HONESTY section).
- Not verified truth: reports are decision records, not evidence.
- Not a marketplace listing: no Gumroad product has been created, and none
  will be without Black's explicit approval.
- Not touching cwi-store: this product lives at
  `~/workspace/cwi-company/apps/twenty-minds-engine/` and nowhere else.
