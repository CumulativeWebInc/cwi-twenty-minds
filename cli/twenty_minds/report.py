"""Report writer: report.md (human) + report.json (machine-readable).

Stdlib only. No network, no telemetry.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Sequence, Tuple
import json

from .protocol import (
    SCHEMA_VERSION,
    DecisionBrief,
    DuplicateFlag,
    MindVerdict,
    Synthesis,
)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_markdown(
    brief: DecisionBrief,
    verdicts: Sequence[MindVerdict],
    synthesis: Synthesis,
    flags: Sequence[DuplicateFlag],
) -> str:
    lines: List[str] = []
    lines.append(f"# Twenty Minds — {brief.question}")
    lines.append("")
    lines.append(f"_Generated {_timestamp()} · schema {SCHEMA_VERSION}_")
    lines.append("")
    lines.append("## Decision question")
    lines.append("")
    lines.append(brief.question)
    lines.append("")
    lines.append("## Facts (max 5)")
    lines.append("")
    for i, fact in enumerate(brief.facts, 1):
        lines.append(f"{i}. {fact}")
    lines.append("")
    lines.append("## Verdicts (one sentence + one risk each)")
    lines.append("")
    for i, v in enumerate(verdicts, 1):
        lines.append(f"{i}. **{v.perspective}** — {v.verdict}")
        lines.append(f"   Risk: {v.risk}")
    lines.append("")
    if flags:
        lines.append("## Distinctness flags")
        lines.append("")
        lines.append(
            "The protocol requires distinct verdicts. The following pairs were "
            "flagged as duplicate or near-duplicate and should be rewritten:"
        )
        lines.append("")
        for f in flags:
            lines.append(
                f"- {f.perspective_a} ↔ {f.perspective_b} "
                f"({f.kind}, similarity {f.similarity})"
            )
        lines.append("")
    lines.append("## Synthesis")
    lines.append("")
    lines.append(f"- **Decision:** {synthesis.decision}")
    lines.append(f"- **Why:** {synthesis.why}")
    lines.append(f"- **Dissent recorded:** {synthesis.dissent_recorded}")
    lines.append(f"- **Confidence:** {synthesis.confidence}")
    lines.append(
        f"- **Changed the pre-run lean?** {'yes' if synthesis.changed_lean else 'no'}"
    )
    lines.append("")
    lines.append("---")
    lines.append(
        "_This report structures reasoning; it does not verify it. "
        "Verdicts are only as good as the minds behind them. "
        "Never present this report as verified truth._"
    )
    lines.append("")
    return "\n".join(lines)


def build_json(
    brief: DecisionBrief,
    verdicts: Sequence[MindVerdict],
    synthesis: Synthesis,
    flags: Sequence[DuplicateFlag],
) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _timestamp(),
        "question": brief.question,
        "facts": list(brief.facts),
        "verdicts": [
            {
                "perspective": v.perspective,
                "verdict": v.verdict,
                "risk": v.risk,
            }
            for v in verdicts
        ],
        "synthesis": {
            "decision": synthesis.decision,
            "why": synthesis.why,
            "dissent_recorded": synthesis.dissent_recorded,
            "confidence": synthesis.confidence,
            "changed_lean": synthesis.changed_lean,
        },
        "distinctness_flags": [
            {
                "perspective_a": f.perspective_a,
                "perspective_b": f.perspective_b,
                "similarity": f.similarity,
                "kind": f.kind,
            }
            for f in flags
        ],
    }


def write_report(
    brief: DecisionBrief,
    verdicts: Sequence[MindVerdict],
    synthesis: Synthesis,
    flags: Sequence[DuplicateFlag],
    out_dir: str | Path,
) -> Tuple[Path, Path]:
    """Write report.md and report.json into out_dir. Returns (md_path, json_path)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    md_path = out / "report.md"
    json_path = out / "report.json"
    md_path.write_text(
        build_markdown(brief, verdicts, synthesis, flags), encoding="utf-8"
    )
    json_path.write_text(
        json.dumps(build_json(brief, verdicts, synthesis, flags), indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    return md_path, json_path
