"""Twenty Minds protocol core: perspectives, briefs, verdicts, synthesis.

Stdlib only. No network, no telemetry, no secrets handling.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

SCHEMA_VERSION = "1.0.0"
MAX_FACTS = 5

# The 20 named adversarial perspectives. Order is fixed: verdicts are
# collected and reported in this order.
PERSPECTIVES: List[Tuple[str, str]] = [
    ("Skeptic", "Attacks the strongest argument for the decision; asks what would have to be false for it to fail."),
    ("Data scientist", "Asks what the numbers would have to show, and whether we actually have them."),
    ("User advocate", "Asks who the decision serves, and whether they will feel served."),
    ("Contrarian", "Takes the opposite side seriously, not performatively."),
    ("Engineer", "Asks whether it can be built, maintained, and debugged — and what breaks first."),
    ("Economist", "Maps incentives and second-order effects: who gets paid what, and why."),
    ("Security reviewer", "Asks how this gets attacked, exploited, or leaked."),
    ("Child-of-five explainer", "Demands a simple explanation; if it can't be explained simply, it isn't understood."),
    ("10-year historian", "Asks what the record will say about this decision in 2036."),
    ("Devil's accountant", "Prices the true cost, including hidden and compounding ones."),
    ("Field operator", "Asks who runs it day to day, and what their worst Tuesday looks like."),
    ("Systems thinker", "Maps feedback loops, bottlenecks, and what this breaks elsewhere."),
    ("Risk underwriter", "Prices the downside: the tail risk, and who is exposed to it."),
    ("Open-source maintainer", "Asks what this looks like if strangers must read, fork, and trust it."),
    ("Negotiator", "Asks what the other side's best move is, and what our walk-away looks like."),
    ("Time traveler (2036)", "Looks back from 2036: was this the move, or the near-miss?"),
    ("First-principles physicist", "Strips the decision to irreducible facts; asks what must be true."),
    ("Ethicist", "Asks who can be harmed, who can't consent, and whether this is the right thing anyway."),
    ("Competitor analyst", "Asks how the strongest competitor would answer, and what they see that we don't."),
    ("Black's chair", "Asks what Black would actually do, given his grants, carve-outs, and stated style: results only, $0 path first, verify before asserting, never ship simulations as products, no spending or wallet signing without him."),
]

PERSPECTIVE_NAMES: List[str] = [name for name, _ in PERSPECTIVES]
ROLE_BY_NAME: Dict[str, str] = dict(PERSPECTIVES)

CONFIDENCE_LEVELS = ("high", "medium", "low")

# Jaccard token similarity at or above this marks two verdicts as
# near-duplicates. Exact normalized matches are always flagged.
DUPLICATE_SIMILARITY_THRESHOLD = 0.90


@dataclass(frozen=True)
class DecisionBrief:
    """The decision question plus the facts every mind argues from."""

    question: str
    facts: Sequence[str]

    def __post_init__(self) -> None:
        question = (self.question or "").strip()
        if not question:
            raise ValueError("DecisionBrief requires a non-empty question.")
        facts = [f.strip() for f in (self.facts or []) if f and f.strip()]
        if not facts:
            raise ValueError("DecisionBrief requires at least 1 fact.")
        if len(facts) > MAX_FACTS:
            raise ValueError(
                f"DecisionBrief accepts at most {MAX_FACTS} facts; got {len(facts)}. "
                "Minds argue from the brief, not from fresh research — trim to the key facts."
            )
        object.__setattr__(self, "question", question)
        object.__setattr__(self, "facts", facts)


@dataclass(frozen=True)
class MindVerdict:
    """One perspective's verdict plus exactly one risk."""

    perspective: str
    verdict: str
    risk: str

    def __post_init__(self) -> None:
        if (self.perspective or "").strip() not in PERSPECTIVE_NAMES:
            raise ValueError(f"Unknown perspective: {self.perspective!r}")
        for field_name in ("verdict", "risk"):
            value = (getattr(self, field_name) or "").strip()
            if not value:
                raise ValueError(f"MindVerdict requires a non-empty {field_name}.")
            object.__setattr__(self, field_name, value)


@dataclass(frozen=True)
class Synthesis:
    """The synthesis: decision, why, recorded dissent, confidence."""

    decision: str
    why: str
    dissent_recorded: str
    confidence: str
    changed_lean: bool

    def __post_init__(self) -> None:
        for field_name in ("decision", "why"):
            value = (getattr(self, field_name) or "").strip()
            if not value:
                raise ValueError(f"Synthesis requires a non-empty {field_name}.")
            object.__setattr__(self, field_name, value)
        dissent = (self.dissent_recorded or "").strip()
        if not dissent:
            raise ValueError(
                "Synthesis requires a non-empty dissent_recorded field. "
                "A synthesis without a recorded minority view is a press release — record the dissent."
            )
        object.__setattr__(self, "dissent_recorded", dissent)
        confidence = (self.confidence or "").strip().lower()
        if confidence not in CONFIDENCE_LEVELS:
            raise ValueError(
                f"Synthesis confidence must be one of {CONFIDENCE_LEVELS}; got {self.confidence!r}."
            )
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "changed_lean", bool(self.changed_lean))


def build_synthesis(
    decision: str,
    why: str,
    dissent_recorded: str,
    confidence: str,
    changed_lean: bool,
) -> Synthesis:
    """Build a Synthesis, enforcing the mandatory recorded-dissent rule.

    Raises ValueError if the dissent is empty, or if any other field is invalid.
    """
    return Synthesis(
        decision=decision,
        why=why,
        dissent_recorded=dissent_recorded,
        confidence=confidence,
        changed_lean=changed_lean,
    )


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def _jaccard(a: str, b: str) -> float:
    tokens_a = set(a.split())
    tokens_b = set(b.split())
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


@dataclass(frozen=True)
class DuplicateFlag:
    """Two minds whose verdicts are identical or near-identical."""

    perspective_a: str
    perspective_b: str
    similarity: float
    kind: str  # "exact" or "near"


def check_distinctness(verdicts: Sequence[MindVerdict]) -> List[DuplicateFlag]:
    """Flag duplicate or near-duplicate verdicts across minds.

    Returns a (possibly empty) list of DuplicateFlag. Distinct verdicts
    produce no flags. The protocol rule: duplicates get rewritten until
    distinct — this function detects them; the caller decides how to handle.
    """
    flags: List[DuplicateFlag] = []
    normalized = [(v.perspective, _normalize(v.verdict)) for v in verdicts]
    for i in range(len(normalized)):
        name_a, text_a = normalized[i]
        if not text_a:
            continue
        for j in range(i + 1, len(normalized)):
            name_b, text_b = normalized[j]
            if not text_b:
                continue
            if text_a == text_b:
                flags.append(DuplicateFlag(name_a, name_b, 1.0, "exact"))
                continue
            similarity = _jaccard(text_a, text_b)
            if similarity >= DUPLICATE_SIMILARITY_THRESHOLD:
                flags.append(
                    DuplicateFlag(name_a, name_b, round(similarity, 3), "near")
                )
    return flags


def run_protocol(
    brief: DecisionBrief,
    router: Mapping[str, "Backend"],
    default_backend: "Backend",
    progress: Optional[Callable[[int, str, str], None]] = None,
) -> List[MindVerdict]:
    """Run all 20 minds over the brief, in fixed perspective order.

    router maps perspective name -> Backend; perspectives absent from the
    router use default_backend (this is how "combined minds of machines"
    routing works: different minds can run on different models).

    progress, if given, is called as progress(index, perspective_name,
    backend_name) before each mind runs.
    """
    # Local imports keep protocol importable without backend deps.
    from .backends import Backend, parse_mind_response
    from .prompts import build_prompt

    if not isinstance(router, Mapping):
        raise ValueError("router must be a mapping of perspective name -> Backend.")
    for name, backend in router.items():
        if name not in PERSPECTIVE_NAMES:
            raise ValueError(f"router has unknown perspective: {name!r}")
        if not isinstance(backend, Backend):
            raise ValueError(f"router backend for {name!r} is not a Backend instance.")
    if not isinstance(default_backend, Backend):
        raise ValueError("default_backend must be a Backend instance.")

    verdicts: List[MindVerdict] = []
    for index, (name, role) in enumerate(PERSPECTIVES):
        backend = router.get(name, default_backend)
        if progress is not None:
            progress(index, name, backend.name)
        prompt = build_prompt(name, role, brief)
        raw = backend.generate(prompt)
        verdict_text, risk_text = parse_mind_response(raw)
        verdicts.append(
            MindVerdict(perspective=name, verdict=verdict_text, risk=risk_text)
        )
    return verdicts
