"""Twenty Minds Decision Engine — adversarial 20-perspective decision protocol."""

from .protocol import (
    SCHEMA_VERSION,
    MAX_FACTS,
    PERSPECTIVES,
    PERSPECTIVE_NAMES,
    CONFIDENCE_LEVELS,
    DecisionBrief,
    MindVerdict,
    Synthesis,
    DuplicateFlag,
    build_synthesis,
    check_distinctness,
    run_protocol,
)
from .backends import (
    Backend,
    ManualBackend,
    OllamaBackend,
    OpenAICompatBackend,
    MindParseError,
    parse_mind_response,
    build_backend,
)
from .prompts import build_prompt, build_synthesis_prompt
from .report import write_report

__all__ = [
    "SCHEMA_VERSION",
    "MAX_FACTS",
    "PERSPECTIVES",
    "PERSPECTIVE_NAMES",
    "CONFIDENCE_LEVELS",
    "DecisionBrief",
    "MindVerdict",
    "Synthesis",
    "DuplicateFlag",
    "build_synthesis",
    "check_distinctness",
    "run_protocol",
    "Backend",
    "ManualBackend",
    "OllamaBackend",
    "OpenAICompatBackend",
    "MindParseError",
    "parse_mind_response",
    "build_backend",
    "build_prompt",
    "build_synthesis_prompt",
    "write_report",
]

__version__ = "1.0.0"
