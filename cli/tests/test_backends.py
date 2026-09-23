"""Tests for twenty_minds.backends: interface, parsing, graceful failures."""

import unittest

from twenty_minds.backends import (
    Backend,
    MindParseError,
    OllamaBackend,
    OpenAICompatBackend,
    build_backend,
    parse_mind_response,
)
from twenty_minds.protocol import (
    PERSPECTIVE_NAMES,
    DecisionBrief,
    check_distinctness,
    run_protocol,
)


class StubBackend(Backend):
    """Deterministic stub: distinct verdict+risk per mind, no network."""

    def __init__(self, label: str = "stub") -> None:
        self._label = label
        self.calls = 0

    @property
    def name(self) -> str:
        return self._label

    def generate(self, prompt: str) -> str:
        self.calls += 1
        # Derive a mind-specific marker from the prompt's first line (the name).
        first_line = prompt.splitlines()[0]
        return (
            f"Verdict: The stub mind speaking as {first_line} says proceed carefully with plan {self.calls}.\n"
            f"Risk: The stub risk for {first_line} is untested assumption number {self.calls}."
        )


class TestBackendInterface(unittest.TestCase):
    def test_stub_implements_interface(self):
        stub = StubBackend()
        self.assertIsInstance(stub, Backend)
        self.assertEqual(stub.name, "stub")
        verdict, risk = parse_mind_response(stub.generate("You are the Skeptic mind\n..."))
        self.assertTrue(verdict)
        self.assertTrue(risk)


class TestParseMindResponse(unittest.TestCase):
    def test_parses_strict_format(self):
        verdict, risk = parse_mind_response("Verdict: Go.\nRisk: It might fail.")
        self.assertEqual(verdict, "Go.")
        self.assertEqual(risk, "It might fail.")

    def test_missing_verdict_raises(self):
        with self.assertRaises(MindParseError):
            parse_mind_response("Risk: Only a risk here.")

    def test_missing_risk_raises(self):
        with self.assertRaises(MindParseError):
            parse_mind_response("Verdict: Only a verdict here.")

    def test_empty_response_raises(self):
        with self.assertRaises(MindParseError):
            parse_mind_response("")


class TestRunProtocolEndToEnd(unittest.TestCase):
    def test_full_run_produces_twenty_distinct_verdicts(self):
        stub = StubBackend()
        brief = DecisionBrief(
            question="Should we ship the stub run?",
            facts=["The stub is deterministic.", "No network is involved."],
        )
        verdicts = run_protocol(brief, {}, stub)
        self.assertEqual(len(verdicts), 20)
        self.assertEqual(
            [v.perspective for v in verdicts], PERSPECTIVE_NAMES
        )
        for v in verdicts:
            self.assertTrue(v.verdict.strip())
            self.assertTrue(v.risk.strip())
        # Distinctness guard must pass on the stub's distinct verdicts.
        self.assertEqual(check_distinctness(verdicts), [])
        self.assertEqual(stub.calls, 20)

    def test_per_mind_routing_uses_mapped_backend(self):
        stub_a = StubBackend("a")
        stub_b = StubBackend("b")
        brief = DecisionBrief(question="Q?", facts=["F1."])
        seen = []
        verdicts = run_protocol(
            brief,
            {"Skeptic": stub_b},
            stub_a,
            progress=lambda i, name, backend: seen.append((name, backend)),
        )
        self.assertEqual(len(verdicts), 20)
        by_name = dict(seen)
        self.assertEqual(by_name["Skeptic"], "b")
        self.assertEqual(by_name["Engineer"], "a")
        self.assertEqual(stub_b.calls, 1)
        self.assertEqual(stub_a.calls, 19)

    def test_router_rejects_unknown_perspective(self):
        stub = StubBackend()
        brief = DecisionBrief(question="Q?", facts=["F1."])
        with self.assertRaises(ValueError):
            run_protocol(brief, {"Not a mind": stub}, stub)

    def test_router_rejects_non_backend(self):
        stub = StubBackend()
        brief = DecisionBrief(question="Q?", facts=["F1."])
        with self.assertRaises(ValueError):
            run_protocol(brief, {"Skeptic": "not-a-backend"}, stub)


class TestOllamaBackendGracefulFailure(unittest.TestCase):
    def test_unreachable_host_raises_helpful_runtime_error(self):
        # Port 1 on loopback refuses fast; no real Ollama needed.
        backend = OllamaBackend(model="tiny", host="http://127.0.0.1:1", timeout=5)
        with self.assertRaises(RuntimeError) as ctx:
            backend.generate("Verdict: x\nRisk: y")
        message = str(ctx.exception)
        self.assertIn("Ollama", message)
        self.assertIn("ollama serve", message)


class TestOpenAICompatBackendKeyHandling(unittest.TestCase):
    def test_missing_env_var_raises_without_leaking_anything(self):
        backend = OpenAICompatBackend(
            model="some-model",
            base_url="http://127.0.0.1:1",
            env_var="TM_TEST_DEFINITELY_MISSING_KEY_9ZQ",
        )
        with self.assertRaises(RuntimeError) as ctx:
            backend.generate("hello")
        self.assertIn("TM_TEST_DEFINITELY_MISSING_KEY_9ZQ", str(ctx.exception))

    def test_requires_model_and_base_url(self):
        with self.assertRaises(ValueError):
            OpenAICompatBackend(model="", base_url="http://x")
        with self.assertRaises(ValueError):
            OpenAICompatBackend(model="m", base_url="")


class TestBuildBackend(unittest.TestCase):
    def test_unknown_backend_name_raises(self):
        with self.assertRaises(ValueError):
            build_backend("telepathy")

    def test_builds_manual(self):
        self.assertEqual(build_backend("manual").name, "manual")


if __name__ == "__main__":
    unittest.main()
