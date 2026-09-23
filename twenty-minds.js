/* Twenty Minds Decision Engine — in-browser protocol (JS port of
 * twenty_minds/protocol.py + prompts.py + report.py).
 *
 * Faithful port of the CLI's manual-backend flow:
 *  - same 20 named adversarial perspectives in fixed order (PERSPECTIVES,
 *    injected at build time from perspectives.json, which is generated from
 *    protocol.py — byte-identical content)
 *  - same brief rules (non-empty question, 1-5 facts)
 *  - same prompt text the CLI hands each mind (buildPrompt mirrors build_prompt)
 *  - same distinctness guard (normalized exact match, Jaccard >= 0.90)
 *  - same synthesis validation (dissent mandatory, confidence high|medium|low)
 *  - same report shape (report.md + report.json)
 *
 * The operator is the backend: in the CLI's manual mode a human answers each
 * mind; this page runs exactly that flow in the browser. Nothing is verified
 * for you — the report structures reasoning; it does not verify it.
 */
"use strict";

const PERSPECTIVES = [{"name": "Skeptic", "role": "Attacks the strongest argument for the decision; asks what would have to be false for it to fail."}, {"name": "Data scientist", "role": "Asks what the numbers would have to show, and whether we actually have them."}, {"name": "User advocate", "role": "Asks who the decision serves, and whether they will feel served."}, {"name": "Contrarian", "role": "Takes the opposite side seriously, not performatively."}, {"name": "Engineer", "role": "Asks whether it can be built, maintained, and debugged \u2014 and what breaks first."}, {"name": "Economist", "role": "Maps incentives and second-order effects: who gets paid what, and why."}, {"name": "Security reviewer", "role": "Asks how this gets attacked, exploited, or leaked."}, {"name": "Child-of-five explainer", "role": "Demands a simple explanation; if it can't be explained simply, it isn't understood."}, {"name": "10-year historian", "role": "Asks what the record will say about this decision in 2036."}, {"name": "Devil's accountant", "role": "Prices the true cost, including hidden and compounding ones."}, {"name": "Field operator", "role": "Asks who runs it day to day, and what their worst Tuesday looks like."}, {"name": "Systems thinker", "role": "Maps feedback loops, bottlenecks, and what this breaks elsewhere."}, {"name": "Risk underwriter", "role": "Prices the downside: the tail risk, and who is exposed to it."}, {"name": "Open-source maintainer", "role": "Asks what this looks like if strangers must read, fork, and trust it."}, {"name": "Negotiator", "role": "Asks what the other side's best move is, and what our walk-away looks like."}, {"name": "Time traveler (2036)", "role": "Looks back from 2036: was this the move, or the near-miss?"}, {"name": "First-principles physicist", "role": "Strips the decision to irreducible facts; asks what must be true."}, {"name": "Ethicist", "role": "Asks who can be harmed, who can't consent, and whether this is the right thing anyway."}, {"name": "Competitor analyst", "role": "Asks how the strongest competitor would answer, and what they see that we don't."}, {"name": "Black's chair", "role": "Asks what Black would actually do, given his grants, carve-outs, and stated style: results only, $0 path first, verify before asserting, never ship simulations as products, no spending or wallet signing without him."}];
const SCHEMA_VERSION = "1.0.0";
const MAX_FACTS = 5;
const CONFIDENCE_LEVELS = ["high", "medium", "low"];
const DUPLICATE_SIMILARITY_THRESHOLD = 0.90;

const PERSPECTIVE_NAMES = PERSPECTIVES.map((p) => p.name);
const ROLE_BY_NAME = Object.fromEntries(PERSPECTIVES.map((p) => [p.name, p.role]));

function makeBrief(question, facts) {
  question = (question || "").trim();
  if (!question) throw new Error("DecisionBrief requires a non-empty question.");
  facts = (facts || []).map((f) => (f || "").trim()).filter(Boolean);
  if (!facts.length) throw new Error("DecisionBrief requires at least 1 fact.");
  if (facts.length > MAX_FACTS)
    throw new Error(
      `DecisionBrief accepts at most ${MAX_FACTS} facts; got ${facts.length}.`
    );
  return { question, facts };
}

function makeVerdict(perspective, verdict, risk) {
  if (!PERSPECTIVE_NAMES.includes((perspective || "").trim()))
    throw new Error(`Unknown perspective: ${JSON.stringify(perspective)}`);
  verdict = (verdict || "").trim();
  risk = (risk || "").trim();
  if (!verdict) throw new Error("MindVerdict requires a non-empty verdict.");
  if (!risk) throw new Error("MindVerdict requires a non-empty risk.");
  return { perspective: perspective.trim(), verdict, risk };
}

/* Mirrors prompts.build_prompt exactly. */
function buildPrompt(perspectiveName, brief) {
  const role = ROLE_BY_NAME[perspectiveName];
  const facts = brief.facts.map((f, i) => `${i + 1}. ${f}`).join("\n");
  return (
    `You are the ${perspectiveName} mind in a 20-mind adversarial decision protocol.\n` +
    `\n` +
    `Role: ${role}\n` +
    `\n` +
    `Decision question: ${brief.question}\n` +
    `\n` +
    `Facts (argue ONLY from these facts; if your verdict needs a fact you do not ` +
    `have, say so plainly in the verdict instead of inventing one):\n` +
    `${facts}\n` +
    `\n` +
    `STRICT OUTPUT FORMAT — obey exactly:\n` +
    `- Exactly one sentence for your verdict.\n` +
    `- Exactly one sentence for the risk.\n` +
    `- No extra prose, no preamble, no bullet points, no markdown.\n` +
    `\n` +
    `Return exactly two lines:\n` +
    `Verdict: <one sentence>\n` +
    `Risk: <one sentence>\n`
  );
}

function normalize(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter(Boolean)
    .join(" ");
}

function jaccard(a, b) {
  const A = new Set(a.split(" ").filter(Boolean));
  const B = new Set(b.split(" ").filter(Boolean));
  if (!A.size || !B.size) return 0;
  let inter = 0;
  for (const t of A) if (B.has(t)) inter++;
  return inter / (A.size + B.size - inter);
}

/* Mirrors protocol.check_distinctness. */
function checkDistinctness(verdicts) {
  const flags = [];
  const normed = verdicts.map((v) => [v.perspective, normalize(v.verdict)]);
  for (let i = 0; i < normed.length; i++) {
    const [nameA, textA] = normed[i];
    if (!textA) continue;
    for (let j = i + 1; j < normed.length; j++) {
      const [nameB, textB] = normed[j];
      if (!textB) continue;
      if (textA === textB) {
        flags.push({ perspective_a: nameA, perspective_b: nameB, similarity: 1.0, kind: "exact" });
        continue;
      }
      const sim = jaccard(textA, textB);
      if (sim >= DUPLICATE_SIMILARITY_THRESHOLD) {
        flags.push({
          perspective_a: nameA,
          perspective_b: nameB,
          similarity: Math.round(sim * 1000) / 1000,
          kind: "near",
        });
      }
    }
  }
  return flags;
}

function buildSynthesis(decision, why, dissentRecorded, confidence, changedLean) {
  decision = (decision || "").trim();
  why = (why || "").trim();
  dissentRecorded = (dissentRecorded || "").trim();
  if (!decision) throw new Error("Synthesis requires a non-empty decision.");
  if (!why) throw new Error("Synthesis requires a non-empty why.");
  if (!dissentRecorded)
    throw new Error(
      "Synthesis requires a non-empty dissent_recorded field. " +
        "A synthesis without a recorded minority view is a press release — record the dissent."
    );
  confidence = (confidence || "").trim().toLowerCase();
  if (!CONFIDENCE_LEVELS.includes(confidence))
    throw new Error(
      `Synthesis confidence must be one of ${CONFIDENCE_LEVELS.join(", ")}; got ${JSON.stringify(confidence)}.`
    );
  return { decision, why, dissent_recorded: dissentRecorded, confidence, changed_lean: !!changedLean };
}

function buildMarkdown(brief, verdicts, synthesis, flags, generatedAt) {
  const L = [];
  L.push(`# Twenty Minds — ${brief.question}`);
  L.push("");
  L.push(`_Generated ${generatedAt} · schema ${SCHEMA_VERSION}_`);
  L.push("");
  L.push("## Decision question");
  L.push("");
  L.push(brief.question);
  L.push("");
  L.push("## Facts (max 5)");
  L.push("");
  brief.facts.forEach((f, i) => L.push(`${i + 1}. ${f}`));
  L.push("");
  L.push("## Verdicts (one sentence + one risk each)");
  L.push("");
  verdicts.forEach((v, i) => {
    L.push(`${i + 1}. **${v.perspective}** — ${v.verdict}`);
    L.push(`   Risk: ${v.risk}`);
  });
  L.push("");
  if (flags.length) {
    L.push("## Distinctness flags");
    L.push("");
    L.push(
      "The protocol requires distinct verdicts. The following pairs were " +
        "flagged as duplicate or near-duplicate and should be rewritten:"
    );
    L.push("");
    flags.forEach((f) => {
      // Python renders the exact-case float 1.0 as "1.0"; near-case via str(round(s,3)).
      const simStr = f.kind === "exact" ? "1.0" : String(f.similarity);
      L.push(`- ${f.perspective_a} ↔ ${f.perspective_b} (${f.kind}, similarity ${simStr})`);
    });
    L.push("");
  }
  L.push("## Synthesis");
  L.push("");
  L.push(`- **Decision:** ${synthesis.decision}`);
  L.push(`- **Why:** ${synthesis.why}`);
  L.push(`- **Dissent recorded:** ${synthesis.dissent_recorded}`);
  L.push(`- **Confidence:** ${synthesis.confidence}`);
  L.push(`- **Changed the pre-run lean?** ${synthesis.changed_lean ? "yes" : "no"}`);
  L.push("");
  L.push("---");
  L.push(
    "_This report structures reasoning; it does not verify it. " +
      "Verdicts are only as good as the minds behind them. " +
      "Never present this report as verified truth._"
  );
  L.push("");
  return L.join("\n");
}

function buildJson(brief, verdicts, synthesis, flags, generatedAt) {
  return {
    schema_version: SCHEMA_VERSION,
    generated_at: generatedAt,
    question: brief.question,
    facts: brief.facts.slice(),
    verdicts: verdicts.map((v) => ({
      perspective: v.perspective,
      verdict: v.verdict,
      risk: v.risk,
    })),
    synthesis: {
      decision: synthesis.decision,
      why: synthesis.why,
      dissent_recorded: synthesis.dissent_recorded,
      confidence: synthesis.confidence,
      changed_lean: synthesis.changed_lean,
    },
    distinctness_flags: flags.map((f) => ({
      perspective_a: f.perspective_a,
      perspective_b: f.perspective_b,
      similarity: f.similarity,
      kind: f.kind,
    })),
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    PERSPECTIVES, PERSPECTIVE_NAMES, ROLE_BY_NAME, SCHEMA_VERSION, MAX_FACTS,
    CONFIDENCE_LEVELS, DUPLICATE_SIMILARITY_THRESHOLD,
    makeBrief, makeVerdict, buildPrompt, checkDistinctness, buildSynthesis,
    buildMarkdown, buildJson,
  };
}
