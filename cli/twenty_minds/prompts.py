"""Prompt builders for the Twenty Minds protocol.

Stdlib only. Builds the per-perspective prompt and the synthesis prompt.
"""

from __future__ import annotations

from typing import Sequence, Tuple

from .protocol import DecisionBrief, MindVerdict


def build_prompt(
    perspective_name: str, role_description: str, brief: DecisionBrief
) -> str:
    """Build the prompt one mind receives: role + question + facts + format."""
    facts = "\n".join(f"{i + 1}. {fact}" for i, fact in enumerate(brief.facts))
    return (
        f"You are the {perspective_name} mind in a 20-mind adversarial decision protocol.\n"
        f"\n"
        f"Role: {role_description}\n"
        f"\n"
        f"Decision question: {brief.question}\n"
        f"\n"
        f"Facts (argue ONLY from these facts; if your verdict needs a fact you do not "
        f"have, say so plainly in the verdict instead of inventing one):\n"
        f"{facts}\n"
        f"\n"
        f"STRICT OUTPUT FORMAT — obey exactly:\n"
        f"- Exactly one sentence for your verdict.\n"
        f"- Exactly one sentence for the risk.\n"
        f"- No extra prose, no preamble, no bullet points, no markdown.\n"
        f"\n"
        f"Return exactly two lines:\n"
        f"Verdict: <one sentence>\n"
        f"Risk: <one sentence>\n"
    )


def build_synthesis_prompt(
    brief: DecisionBrief, verdicts: Sequence[MindVerdict]
) -> str:
    """Build the prompt used to draft the synthesis from the 20 verdicts."""
    lines = "\n".join(
        f"{i + 1}. {v.perspective}: {v.verdict} Risk: {v.risk}"
        for i, v in enumerate(verdicts)
    )
    return (
        "You are synthesizing a 20-mind adversarial decision run into one decision.\n"
        "\n"
        f"Decision question: {brief.question}\n"
        "\n"
        "The 20 verdicts (each: one-sentence verdict + one risk):\n"
        f"{lines}\n"
        "\n"
        "Write the synthesis. The dissent is MANDATORY: name the strongest minority "
        "view and who holds it. A synthesis without a recorded minority view is a "
        "press release, not a synthesis.\n"
        "\n"
        "STRICT OUTPUT FORMAT — obey exactly, no extra prose:\n"
        "Decision: <one sentence, A or B / yes or no>\n"
        "Why: <the 2-3 minds that carried the decision, with their reasons>\n"
        "Dissent: <the strongest minority view and who holds it — must not be empty>\n"
        "Confidence: <high | medium | low>\n"
        "ConfidenceFact: <the single fact that would change the confidence>\n"
        "ChangedLean: <yes | no — did this run change the operator's pre-run lean?>\n"
    )


def parse_synthesis_fields(text: str) -> dict:
    """Parse a synthesis response into its named fields.

    Raises ValueError if the mandatory Decision or Dissent fields are missing.
    """
    fields: dict = {}
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip().lower()] = value.strip()
    decision = fields.get("decision", "").strip()
    dissent = fields.get("dissent", "").strip()
    if not decision:
        raise ValueError("Synthesis response is missing the mandatory 'Decision:' field.")
    if not dissent:
        raise ValueError(
            "Synthesis response is missing the mandatory 'Dissent:' field. "
            "Record the strongest minority view — a synthesis without dissent is rejected."
        )
    changed_raw = fields.get("changedlean", fields.get("changed_lean", "")).strip().lower()
    changed_lean = changed_raw in ("yes", "true", "1", "y")
    why = fields.get("why", "").strip()
    confidence = fields.get("confidence", "").strip().lower()
    confidence_fact = fields.get("confidencefact", fields.get("confidence_fact", "")).strip()
    if confidence_fact and why and not why.rstrip().endswith("."):
        why = why + " "
    if confidence_fact:
        why = (why + f" Fact that would change it: {confidence_fact}").strip()
    return {
        "decision": decision,
        "why": why,
        "dissent_recorded": dissent,
        "confidence": confidence or "medium",
        "changed_lean": changed_lean,
    }


def synthesis_field_names() -> Tuple[str, ...]:
    return ("Decision", "Why", "Dissent", "Confidence", "ConfidenceFact", "ChangedLean")
