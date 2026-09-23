"""Tests for twenty_minds.protocol: perspectives, briefs, distinctness, synthesis."""

import unittest

from twenty_minds.protocol import (
    MAX_FACTS,
    PERSPECTIVE_NAMES,
    PERSPECTIVES,
    DecisionBrief,
    MindVerdict,
    build_synthesis,
    check_distinctness,
)


def _brief(n_facts: int = 2) -> DecisionBrief:
    return DecisionBrief(
        question="Should we test the protocol?",
        facts=[f"Fact {i + 1}." for i in range(n_facts)],
    )


class TestPerspectives(unittest.TestCase):
    def test_twenty_perspectives_present(self):
        self.assertEqual(len(PERSPECTIVES), 20)
        self.assertEqual(len(PERSPECTIVE_NAMES), 20)

    def test_perspective_names_unique(self):
        self.assertEqual(len(set(PERSPECTIVE_NAMES)), 20)

    def test_each_has_one_line_role_description(self):
        for name, role in PERSPECTIVES:
            self.assertTrue(name.strip(), "perspective name must be non-empty")
            self.assertTrue(role.strip(), f"{name} needs a role description")
            self.assertNotIn("\n", role, f"{name} role must be one line")

    def test_required_perspectives_present(self):
        for required in ("Skeptic", "Black's chair", "Time traveler (2036)"):
            self.assertIn(required, PERSPECTIVE_NAMES)


class TestDecisionBrief(unittest.TestCase):
    def test_accepts_one_to_five_facts(self):
        for n in (1, 2, 5):
            brief = _brief(n)
            self.assertEqual(len(brief.facts), n)

    def test_rejects_six_facts(self):
        with self.assertRaises(ValueError):
            _brief(6)

    def test_rejects_zero_facts(self):
        with self.assertRaises(ValueError):
            DecisionBrief(question="Q?", facts=[])

    def test_rejects_empty_question(self):
        with self.assertRaises(ValueError):
            DecisionBrief(question="   ", facts=["Fact 1."])

    def test_max_facts_constant_is_five(self):
        self.assertEqual(MAX_FACTS, 5)


class TestDistinctnessGuard(unittest.TestCase):
    def _verdict(self, perspective, verdict):
        return MindVerdict(perspective=perspective, verdict=verdict, risk="Some risk.")

    def test_flags_exact_duplicate_verdicts(self):
        verdicts = [
            self._verdict("Skeptic", "Proceed with the launch now."),
            self._verdict("Contrarian", "Proceed with the launch now."),
        ]
        flags = check_distinctness(verdicts)
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0].kind, "exact")
        self.assertEqual(flags[0].perspective_a, "Skeptic")
        self.assertEqual(flags[0].perspective_b, "Contrarian")

    def test_flags_case_and_punctuation_variants_as_exact(self):
        verdicts = [
            self._verdict("Skeptic", "Proceed with the launch now!"),
            self._verdict("Contrarian", "proceed with the launch now"),
        ]
        flags = check_distinctness(verdicts)
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0].kind, "exact")

    def test_flags_near_duplicates(self):
        # Two long verdicts differing by exactly one word: Jaccard ~= 0.913,
        # above the 0.90 near-duplicate threshold.
        base = (
            "Proceed with the launch immediately because the data supports it fully "
            "and every engineer on the team confirmed readiness yesterday "
            "without any remaining objections"
        )
        near = base.replace("yesterday", "today")
        verdicts = [
            self._verdict("Skeptic", base + "."),
            self._verdict("Contrarian", near + "."),
        ]
        flags = check_distinctness(verdicts)
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0].kind, "near")

    def test_passes_distinct_verdicts(self):
        verdicts = [
            self._verdict("Skeptic", "Kill the launch; the core claim is unproven."),
            self._verdict("Contrarian", "Delay a week; the team needs sleep first."),
        ]
        self.assertEqual(check_distinctness(verdicts), [])

    def test_no_self_flags(self):
        verdicts = [self._verdict("Skeptic", "A unique verdict here.")]
        self.assertEqual(check_distinctness(verdicts), [])


class TestSynthesisBuilder(unittest.TestCase):
    def _kwargs(self, **overrides):
        kwargs = dict(
            decision="Launch.",
            why="The engineer and the data scientist carried it.",
            dissent_recorded="The skeptic dissents: the core claim is unproven.",
            confidence="medium",
            changed_lean=False,
        )
        kwargs.update(overrides)
        return kwargs

    def test_builds_valid_synthesis(self):
        s = build_synthesis(**self._kwargs())
        self.assertEqual(s.decision, "Launch.")
        self.assertEqual(s.confidence, "medium")
        self.assertFalse(s.changed_lean)

    def test_raises_without_dissent(self):
        with self.assertRaises(ValueError):
            build_synthesis(**self._kwargs(dissent_recorded=""))
        with self.assertRaises(ValueError):
            build_synthesis(**self._kwargs(dissent_recorded="   "))

    def test_raises_without_decision_or_why(self):
        with self.assertRaises(ValueError):
            build_synthesis(**self._kwargs(decision=""))
        with self.assertRaises(ValueError):
            build_synthesis(**self._kwargs(why="  "))

    def test_rejects_bad_confidence(self):
        with self.assertRaises(ValueError):
            build_synthesis(**self._kwargs(confidence="extreme"))

    def test_confidence_normalized_to_lowercase(self):
        s = build_synthesis(**self._kwargs(confidence="HIGH"))
        self.assertEqual(s.confidence, "high")


if __name__ == "__main__":
    unittest.main()
