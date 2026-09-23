"""Twenty Minds Decision Engine — command-line interface.

Usage:
    python -m twenty_minds "Should we launch?" --fact "fact 1" --fact "fact 2"
    python -m twenty_minds "A vs B?" --fact f1 --backend ollama --model llama3.1 --out ./run-001
    python -m twenty_minds --list-perspectives
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional

from .backends import (
    BACKEND_NAMES,
    Backend,
    ManualBackend,
    MindParseError,
    build_backend,
)
from .prompts import build_synthesis_prompt, parse_synthesis_fields
from .protocol import (
    CONFIDENCE_LEVELS,
    MAX_FACTS,
    PERSPECTIVE_NAMES,
    PERSPECTIVES,
    DecisionBrief,
    Synthesis,
    build_synthesis,
    check_distinctness,
    run_protocol,
)
from .report import write_report


def _default_out_dir() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"./run-{stamp}"


def _parse_route(route_json: Optional[str]) -> Dict[str, str]:
    """Parse --route '{"Skeptic":"ollama"}' into perspective -> backend-name."""
    if not route_json:
        return {}
    try:
        mapping = json.loads(route_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--route is not valid JSON: {exc}") from exc
    if not isinstance(mapping, dict):
        raise ValueError("--route must be a JSON object mapping perspective names to backend names.")
    for perspective, backend_name in mapping.items():
        if perspective not in PERSPECTIVE_NAMES:
            raise ValueError(
                f"--route has unknown perspective {perspective!r}. "
                f"Valid names: {', '.join(PERSPECTIVE_NAMES)}."
            )
        if backend_name not in BACKEND_NAMES:
            raise ValueError(
                f"--route maps {perspective!r} to unknown backend {backend_name!r}. "
                f"Choose from: {', '.join(BACKEND_NAMES)}."
            )
    return mapping


def _prompt(message: str) -> str:
    try:
        return input(message).strip()
    except EOFError:
        raise RuntimeError(
            "stdin closed while reading an answer. Provide answers interactively, "
            "pipe them into stdin, or use a non-manual backend."
        )


def collect_synthesis_manual() -> Synthesis:
    """Collect the synthesis from the operator via stdin (dissent enforced)."""
    print("=" * 72)
    print("SYNTHESIS — you write the decision from the 20 verdicts above.")
    print("The dissent field is MANDATORY: name the strongest minority view and who holds it.")
    print("-" * 72)
    decision = _prompt("Decision (one sentence, A or B / yes or no): ")
    why = _prompt("Why (the 2-3 minds that carried it, with reasons): ")
    dissent = ""
    while not dissent:
        dissent = _prompt("Dissent recorded (strongest minority view + who holds it): ")
        if not dissent:
            print("Dissent cannot be empty — a synthesis without dissent is rejected. Try again.")
    confidence = ""
    while confidence not in CONFIDENCE_LEVELS:
        confidence = _prompt(f"Confidence ({' / '.join(CONFIDENCE_LEVELS)}): ").lower()
        if confidence not in CONFIDENCE_LEVELS:
            print(f"Please answer one of: {', '.join(CONFIDENCE_LEVELS)}.")
    changed_raw = _prompt("Changed the pre-run lean? (yes/no): ").lower()
    changed_lean = changed_raw in ("yes", "y", "true", "1")
    return build_synthesis(decision, why, dissent, confidence, changed_lean)


def collect_synthesis_backend(brief: DecisionBrief, verdicts, backend: Backend) -> Synthesis:
    """Draft the synthesis with a backend, then validate (dissent enforced)."""
    prompt = build_synthesis_prompt(brief, verdicts)
    raw = backend.generate(prompt)
    fields = parse_synthesis_fields(raw)
    return build_synthesis(**fields)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="twenty-minds",
        description="Run a decision through 20 named adversarial perspectives, "
        "then synthesize with recorded dissent.",
    )
    parser.add_argument("question", nargs="?", help="The decision question.")
    parser.add_argument(
        "--fact",
        action="append",
        default=[],
        metavar="FACT",
        help="A key fact every mind argues from. Repeat up to 5 times. (1-5 required)",
    )
    parser.add_argument(
        "--backend",
        default="manual",
        choices=BACKEND_NAMES,
        help="Default backend for all minds (default: manual).",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name for ollama / openai-compat backends.",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Base URL for the openai-compat backend (required with that backend).",
    )
    parser.add_argument(
        "--ollama-host",
        default="http://localhost:11434",
        help="Ollama host (default: http://localhost:11434).",
    )
    parser.add_argument(
        "--env-var",
        default="OPENAI_API_KEY",
        help="Env var holding the API key for openai-compat (default: OPENAI_API_KEY). "
        "The key is never logged or printed.",
    )
    parser.add_argument(
        "--route",
        default=None,
        metavar="JSON",
        help="Per-mind backend routing, e.g. '{\"Skeptic\":\"ollama\"}'. "
        "Perspectives not listed use --backend.",
    )
    parser.add_argument(
        "--synthesis",
        default="manual",
        choices=BACKEND_NAMES,
        help="Who writes the synthesis: manual (operator via stdin, default) or a backend.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output directory for report.md + report.json (default: ./run-<timestamp>).",
    )
    parser.add_argument(
        "--list-perspectives",
        action="store_true",
        help="List the 20 perspectives and exit.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_perspectives:
        for i, (name, role) in enumerate(PERSPECTIVES, 1):
            print(f"{i:2d}. {name} — {role}")
        return 0

    if not args.question:
        parser.error("the decision question is required (unless --list-perspectives).")
    if not args.fact:
        parser.error("at least 1 --fact is required (max 5).")
    if len(args.fact) > MAX_FACTS:
        parser.error(f"at most {MAX_FACTS} --fact flags allowed; got {len(args.fact)}.")

    try:
        brief = DecisionBrief(question=args.question, facts=args.fact)
    except ValueError as exc:
        parser.error(str(exc))

    # Instantiate one instance per backend name; route maps perspective -> instance.
    instances: Dict[str, Backend] = {}
    try:
        instances[args.backend] = build_backend(
            args.backend,
            model=args.model,
            base_url=args.base_url,
            ollama_host=args.ollama_host,
            env_var=args.env_var,
        )
        route = _parse_route(args.route)
        for backend_name in set(route.values()):
            if backend_name not in instances:
                instances[backend_name] = build_backend(
                    backend_name,
                    model=args.model,
                    base_url=args.base_url,
                    ollama_host=args.ollama_host,
                    env_var=args.env_var,
                )
        if args.synthesis != "manual" and args.synthesis not in instances:
            instances[args.synthesis] = build_backend(
                args.synthesis,
                model=args.model,
                base_url=args.base_url,
                ollama_host=args.ollama_host,
                env_var=args.env_var,
            )
    except ValueError as exc:
        parser.error(str(exc))

    default_backend = instances[args.backend]
    router = {perspective: instances[backend_name] for perspective, backend_name in route.items()}

    print(f"Twenty Minds — {brief.question}")
    print(f"Facts: {len(brief.facts)} · minds: {len(PERSPECTIVE_NAMES)}")

    def progress(index: int, name: str, backend_name: str) -> None:
        print(f"[{index + 1:2d}/20] {name}  ({backend_name})", flush=True)

    try:
        verdicts = run_protocol(brief, router, default_backend, progress=progress)
    except (RuntimeError, MindParseError) as exc:
        print(f"\nERROR during the run: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nAborted by operator.", file=sys.stderr)
        return 130

    flags = check_distinctness(verdicts)
    if flags:
        print("\nDistinctness flags (protocol requires distinct verdicts — rewrite these):")
        for f in flags:
            print(f"  - {f.perspective_a} ↔ {f.perspective_b} ({f.kind}, similarity {f.similarity})")
    else:
        print("\nDistinctness check: all 20 verdicts distinct. OK.")

    try:
        if args.synthesis == "manual":
            synthesis = collect_synthesis_manual()
        else:
            synthesis = collect_synthesis_backend(
                brief, verdicts, instances[args.synthesis]
            )
    except (RuntimeError, MindParseError, ValueError) as exc:
        print(f"\nERROR collecting synthesis: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nAborted by operator.", file=sys.stderr)
        return 130

    out_dir = args.out or _default_out_dir()
    md_path, json_path = write_report(brief, verdicts, synthesis, flags, out_dir)
    print("\nDone.")
    print(f"  report.md:   {md_path}")
    print(f"  report.json: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
