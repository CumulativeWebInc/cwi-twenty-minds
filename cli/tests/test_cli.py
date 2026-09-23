"""CLI smoke + end-to-end tests.

The full-run test drives the REAL CLI (`python -m twenty_minds`) with the
manual backend, piping 20 verdict/risk pairs plus a synthesis through stdin.
No network, no API keys.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent.parent
PERSPECTIVE_COUNT = 20


def _stdin_for_full_run() -> str:
    lines = []
    for i in range(1, PERSPECTIVE_COUNT + 1):
        lines.append(f"The {i}th mind verdict is to proceed with caution on point {i}.")
        lines.append(f"The {i}th mind risk is untested assumption number {i}.")
    lines.append("Proceed with the v1 launch.")  # decision
    lines.append("The engineer and the data scientist carried it with receipts.")  # why
    lines.append("The skeptic dissents: the core claim still needs one more check.")  # dissent
    lines.append("medium")  # confidence
    lines.append("yes")  # changed lean
    return "\n".join(lines) + "\n"


class TestListPerspectives(unittest.TestCase):
    def test_list_perspectives_exits_zero(self):
        result = subprocess.run(
            [sys.executable, "-m", "twenty_minds", "--list-perspectives"],
            cwd=ENGINE_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Skeptic", result.stdout)
        self.assertIn("Black's chair", result.stdout)
        # Exactly 20 numbered entries.
        numbered = [l for l in result.stdout.splitlines() if l[:2].strip().rstrip(".").isdigit()]
        self.assertEqual(len(numbered), 20)


class TestValidation(unittest.TestCase):
    def _run(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "twenty_minds", *args],
            cwd=ENGINE_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_six_facts_rejected(self):
        args = ["Q?"] + [x for i in range(6) for x in ("--fact", f"F{i}")]
        result = self._run(*args)
        self.assertNotEqual(result.returncode, 0)

    def test_zero_facts_rejected(self):
        result = self._run("Q?")
        self.assertNotEqual(result.returncode, 0)

    def test_unknown_backend_rejected(self):
        result = self._run("Q?", "--fact", "F1.", "--backend", "telepathy")
        self.assertNotEqual(result.returncode, 0)

    def test_bad_route_json_rejected(self):
        result = self._run("Q?", "--fact", "F1.", "--route", "{not json")
        self.assertNotEqual(result.returncode, 0)

    def test_route_unknown_perspective_rejected(self):
        result = self._run("Q?", "--fact", "F1.", "--route", '{"Not a mind":"manual"}')
        self.assertNotEqual(result.returncode, 0)


class TestFullRunEndToEnd(unittest.TestCase):
    def test_manual_run_writes_valid_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "run-001"
            result = subprocess.run(
                [
                    sys.executable, "-m", "twenty_minds",
                    "Should we ship Twenty Minds v1?",
                    "--fact", "The code is stdlib-only with zero dependencies.",
                    "--fact", "All tests pass locally.",
                    "--fact", "No price is published yet.",
                    "--out", str(out_dir),
                ],
                cwd=ENGINE_DIR,
                input=_stdin_for_full_run(),
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            md_path = out_dir / "report.md"
            json_path = out_dir / "report.json"
            self.assertTrue(md_path.exists(), "report.md must be written")
            self.assertTrue(json_path.exists(), "report.json must be written")

            data = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(data["schema_version"], "1.0.0")
            self.assertEqual(data["question"], "Should we ship Twenty Minds v1?")
            self.assertEqual(len(data["facts"]), 3)
            self.assertEqual(len(data["verdicts"]), 20)

            perspectives = [v["perspective"] for v in data["verdicts"]]
            self.assertEqual(len(set(perspectives)), 20)
            self.assertIn("Skeptic", perspectives)
            self.assertIn("Black's chair", perspectives)
            for v in data["verdicts"]:
                self.assertTrue(v["verdict"].strip())
                self.assertTrue(v["risk"].strip())

            synthesis = data["synthesis"]
            self.assertTrue(synthesis["decision"].strip())
            self.assertTrue(synthesis["dissent_recorded"].strip())
            self.assertIn(synthesis["confidence"], ("high", "medium", "low"))
            self.assertTrue(synthesis["changed_lean"])

            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("Should we ship Twenty Minds v1?", md_text)
            self.assertIn("## Synthesis", md_text)
            self.assertIn("Dissent recorded", md_text)


if __name__ == "__main__":
    unittest.main()
