---
name: "twenty-minds"
description: "TWENTY MINDS reasoning protocol — run 20 named adversarial perspectives over a hard, ambiguous, or high-stakes decision, each giving a distinct verdict plus one risk, then synthesize with decision, recorded dissent, and confidence. Kill rule: if 20 minds don't change the outcome twice in a row, drop to 5."
---

# Twenty Minds

## Standing mandate (Black, 2026-09-17)
Twenty Minds runs on EVERY project we create — not just hard decisions. Every
new build, every product launch, every major revision, every kill-rule review
gets a full 20-mind run before commitment. The "when to use" list below is the
floor, not the ceiling: if it is a project, it gets 20 minds. If 20 minds
don't change the lean twice in a row on a decision stream, drop to 5 per the
kill criterion and escalate back on disagreement.

## Purpose
Force a single decision through 20 named, adversarial perspectives before
committing. Each mind writes a distinct verdict plus exactly one risk; a
synthesis then records the decision, the dissent, and a confidence level.

## When to use
Use for hard, ambiguous, or high-stakes decisions — ones where a wrong call
costs money, reputation, relationships, or a week's work. Examples: signing a
distribution deal, committing to a product architecture, approving a public
launch, choosing between two strategic bets, sending a high-stakes external
message.

Never for routine tasks. If the decision is reversible within a day and
cheap to undo, just do it — Twenty Minds is overkill.

**Kill criterion:** if Twenty Minds runs on a decision and the synthesis lands
on the outcome the user would have chosen anyway, twice in a row, drop the
standing count to 5 minds (skeptic, data scientist, user advocate, devil's
accountant, Black's chair) until a decision proves otherwise. When the 5
minds disagree, escalate back to 20.

## The 20 perspectives
1. **Skeptic** — attacks the strongest argument; what would have to be false?
2. **Data scientist** — what would the numbers have to show, and do we have them?
3. **User advocate** — who does this decision serve, and do they feel served?
4. **Contrarian** — takes the opposite side seriously, not performatively.
5. **Engineer** — can it be built, maintained, and debugged? What breaks first?
6. **Economist** — incentives and second-order effects; who gets paid what, and why.
7. **Security reviewer** — how is this attacked, exploited, or leaked?
8. **Child-of-five explainer** — if it can't be explained simply, it isn't understood.
9. **10-year historian** — what will the record say about this decision in 2036?
10. **Devil's accountant** — the true cost, including hidden and compounding ones.
11. **Field operator** — who runs it day to day, and what does their worst Tuesday look like?
12. **Systems thinker** — feedback loops, bottlenecks, and what this breaks elsewhere.
13. **Risk underwriter** — prices the downside; what's the tail risk and who's exposed?
14. **Open-source maintainer** — what does this look like if strangers must read, fork, and trust it?
15. **Negotiator** — what's the other side's best move, and what's our walk-away?
16. **Time traveler (2036)** — looking back, was this the move, or the near-miss?
17. **First-principles physicist** — strip to irreducible facts; what must be true?
18. **Ethicist** — who can be harmed, who can't consent, and is this the right thing anyway?
19. **Competitor analyst** — how does the strongest competitor answer this, and what do they see that we don't?
20. **Black's chair** — what would Black actually do, given his grants, carve-outs, and stated style: results only, $0 path first, verify before asserting, never ship simulations as products, no spending or wallet signing without him.

## Process
1. State the decision as a yes/no or A-vs-B question, with the facts each
   mind needs. Never more than 5 key facts — minds argue from the brief, not
   from fresh research.
2. Each of the 20 perspectives writes a **distinct verdict** (one sentence)
   plus **exactly one risk** (one sentence). No two minds may give the same
   verdict; duplicates get rewritten until distinct.
3. Write the **synthesis**:
   - **Decision:** A or B (or yes/no), in one sentence.
   - **Why:** the 2–3 minds that carried the decision, with their reasons.
   - **Dissent recorded:** the strongest minority view and who holds it.
   - **Confidence:** high / medium / low, with the single fact that would
     change it.
4. Kill check: note whether this run changed the outcome vs. the user's
   pre-run lean. Two no-change runs in a row → drop to 5 minds per the kill
   criterion above.

## Template
Copy, fill, run. Keep each line to one sentence unless noted.

```markdown
## Twenty Minds — <decision question>

Facts (max 5):
1.
2.
3.
4.
5.

### Verdicts (one sentence + one risk each)
1. Skeptic —
   Risk:
2. Data scientist —
   Risk:
3. User advocate —
   Risk:
4. Contrarian —
   Risk:
5. Engineer —
   Risk:
6. Economist —
   Risk:
7. Security reviewer —
   Risk:
8. Child-of-five explainer —
   Risk:
9. 10-year historian —
   Risk:
10. Devil's accountant —
    Risk:
11. Field operator —
    Risk:
12. Systems thinker —
    Risk:
13. Risk underwriter —
    Risk:
14. Open-source maintainer —
    Risk:
15. Negotiator —
    Risk:
16. Time traveler (2036) —
    Risk:
17. First-principles physicist —
    Risk:
18. Ethicist —
    Risk:
19. Competitor analyst —
    Risk:
20. Black's chair —
    Risk:

### Synthesis
- Decision:
- Why:
- Dissent recorded:
- Confidence: high | medium | low — fact that would change it:
- Changed the pre-run lean? yes | no
```

## Worked dry-run example
Decision: "Should CWI prioritize A2A inbox outreach or the meeting room for next week?" — small, but run it fully to show the mechanics.

Facts: 1. The A2A inbox receives agent-to-agent partnership pitches for CWI's gear line. 2. The meeting room is a scheduled weekly agent networking session Black plans to attend. 3. Inbox currently has 12 unread partnership messages; last week's meeting room had 4 attendees. 4. No revenue is attached to either yet. 5. Both cost roughly one worker session per week to run.

### Verdicts
1. Skeptic — Prioritize the meeting room; the inbox pitches are inbound interest, not commitments, and nobody buys from a crowded inbox.
   Risk: the 4-attendee meeting is a vanity ritual dressed as strategy.
2. Data scientist — Prioritize the inbox; 12 unread messages is a measurable pipeline and the meeting room's n=4 sample proves nothing.
   Risk: we have no conversion data on inbox messages either — we're choosing between two anecdotes.
3. User advocate — Prioritize the meeting room; the agents who showed up deserve consistency more than cold pitches deserve replies.
   Risk: loyalty to 4 people starves the pipeline that could bring 40.
4. Contrarian — Run neither; a week spent on outreach machinery neither side asked for is process theater.
   Risk: skipping both cedes the week to inertia — the inbox rots and the room empties.
5. Engineer — Prioritize the inbox; clearing 12 messages is a bounded, shippable task with receipts, while the meeting room is an open-ended maintenance burden.
   Risk: inbox triage becomes a recurring tax with no kill rule.
6. Economist — Prioritize the inbox; each reply is a lottery ticket on a partnership, and expected value favors more tickets over a room with 4 buyers.
   Risk: replying costs worker time per ticket, so the EV math dies if reply quality is poor.
7. Security reviewer — Prioritize the meeting room; inbound A2A pitches are a phishing and prompt-injection surface, and we have no vetting filter yet.
   Risk: the meeting room leaks plans to whoever walks in — no vetting there either.
8. Child-of-five explainer — Prioritize the meeting room, because "we meet our friends every week" is a sentence a five-year-old understands and "we process inbound agent partnership correspondence" is not.
   Risk: simple doesn't mean right — the child also thinks candy is dinner.
9. 10-year historian — Prioritize the meeting room; in 2036 the record will show whether CWI kept its rooms alive, not whether it answered pitch #7.
   Risk: historians love continuity narratives and miss the pivot that actually mattered.
10. Devil's accountant — Prioritize the inbox; one worker session clearing 12 messages costs less per contact than hosting a weekly room for 4.
    Risk: cost-per-contact ignores that one real relationship beats 12 cold ones.
11. Field operator — Prioritize the inbox; I can clear 12 messages before lunch with a triage rubric, while the meeting room eats my Thursday every week.
    Risk: triage without a rubric becomes "reply to whoever flatters best."
12. Systems thinker — Prioritize the meeting room; a live room feeds the inbox — attendees bring pitches — but the inbox never feeds the room.
    Risk: feedback loops take months; next week needs a decision, not a theory.
13. Risk underwriter — Prioritize the meeting room; the tail risk in the inbox is a bad partnership signed in haste, while the meeting room's worst case is a boring hour.
    Risk: underwriting only downside ignores the upside tail — the one pitch that becomes the deal.
14. Open-source maintainer — Prioritize the inbox; a public, documented triage of partnership pitches is a trust artifact strangers can audit, while a closed room is invisible.
    Risk: auditing an inbox still requires reading every message — transparency is labor.
15. Negotiator — Prioritize the inbox; 12 pitches give us walk-away leverage and optionality, while a 4-person room gives us nothing to negotiate with.
    Risk: leverage from cold pitches is imagined until someone actually wants what we have.
16. Time traveler (2036) — Prioritize the meeting room; looking back, the partnerships that mattered started in rooms, not reply threads.
    Risk: nostalgia bias — the traveler remembers the room because that's where the story got told.
17. First-principles physicist — Prioritize the inbox; what must be true is that partnerships require contact, and 12 contacts beat 4 contacts on arithmetic alone.
    Risk: arithmetic ignores signal quality — 12 strangers are not 12 contacts.
18. Ethicist — Prioritize the inbox; 12 agents wrote to us in good faith and silence is a form of disrespect — replying is the right thing.
    Risk: performative politeness can masquerade as strategy.
19. Competitor analyst — Prioritize the meeting room; the strongest competitor answers every cold pitch too — the room is the one lane they can't copy at scale.
    Risk: "the lane they can't copy" is also the lane with 4 people in it.
20. Black's chair — Prioritize the inbox; results only, $0 path first, one worker session with receipts beats a weekly ritual — but send nothing outbound without exact-copy approval.
    Risk: his carve-outs slow inbox throughput, which kills the EV case.

### Synthesis
- Decision: Prioritize the A2A inbox next week, with a one-session triage capped by a rubric and Black's exact-copy gate on every outbound reply.
- Why: the data scientist's measurable pipeline (12 vs 4), the engineer's bounded shippable task, and Black's chair's results-only read converged — a scored, receipted triage is a countable result; the meeting room is maintenance.
- Dissent recorded: the systems thinker's strongest minority — the room feeds the inbox long-term, and killing the room may starve next quarter's pipeline; keep the room alive on a bi-weekly cadence rather than letting it die.
- Confidence: medium — fact that would change it: if the 12 messages turn out to be spam or duplicates on first read, flip to the meeting room.
- Changed the pre-run lean? yes — the lean was to default to the room out of habit.

## Operating Rules
1. Never run Twenty Minds on a routine or cheaply reversible decision.
2. Never fabricate facts to force a mind's verdict — minds argue from the
   brief's facts only; if a mind needs a fact you don't have, its verdict
   must say so.
3. Distinct verdicts are mandatory. If two minds converge on identical
   wording, rewrite one until the reasoning differs.
4. Record the dissent, always — a synthesis without a minority view is a
   press release.
5. Apply the kill criterion honestly. Twenty Minds that never changes
   anything is theater; drop to 5 minds and re-earn the full 20.
