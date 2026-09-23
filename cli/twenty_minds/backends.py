"""Backend implementations for the Twenty Minds protocol.

A Backend turns a mind's prompt into that mind's response. Three backends:

- ManualBackend: interactive stdin/stdout operator loop (the DEFAULT — $0, no keys).
- OllamaBackend: local Ollama HTTP API (localhost only unless configured).
- OpenAICompatBackend: any OpenAI-compatible chat-completions endpoint. The API
  key is read ONLY from an environment variable and is never logged or printed.

Hard rules: no network calls except to user-configured backends; no telemetry;
no API keys in files; no key values in logs, errors, or reports.
"""

from __future__ import annotations

import abc
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Optional, Tuple


class MindParseError(ValueError):
    """A backend response could not be parsed into verdict + risk."""


class Backend(abc.ABC):
    """Interface: generate a mind's response text from its prompt."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Short backend identifier used in routing and reports."""

    @abc.abstractmethod
    def generate(self, prompt: str) -> str:
        """Return the raw response text for the given prompt."""


def parse_mind_response(text: str) -> Tuple[str, str]:
    """Parse a mind's response into (verdict, risk).

    Accepts exactly the strict format: a "Verdict:" line and a "Risk:" line.
    Raises MindParseError if either is missing.
    """
    verdict: Optional[str] = None
    risk: Optional[str] = None
    for line in (text or "").splitlines():
        stripped = line.strip()
        lowered = stripped.lower()
        if verdict is None and lowered.startswith("verdict:"):
            verdict = stripped.split(":", 1)[1].strip()
        elif risk is None and lowered.startswith("risk:"):
            risk = stripped.split(":", 1)[1].strip()
    if not verdict:
        raise MindParseError(
            "Backend response is missing the 'Verdict:' line. Raw response was: "
            + (text or "").strip()[:300]
        )
    if not risk:
        raise MindParseError(
            "Backend response is missing the 'Risk:' line. Raw response was: "
            + (text or "").strip()[:300]
        )
    return verdict, risk


class ManualBackend(Backend):
    """Interactive backend: prints each mind's prompt; the operator pastes
    back the verdict and risk via stdin. Works with $0 and no API keys."""

    def __init__(self, label: str = "manual") -> None:
        self._label = label

    @property
    def name(self) -> str:
        return self._label

    def generate(self, prompt: str) -> str:
        print("=" * 72)
        print(prompt)
        print("-" * 72)
        try:
            verdict = input("Verdict (exactly one sentence): ").strip()
            risk = input("Risk (exactly one sentence): ").strip()
        except EOFError:
            raise RuntimeError(
                "ManualBackend needs an interactive terminal: stdin closed before "
                "the operator could answer. Pipe answers into stdin, or use the "
                "ollama / openai-compat backend."
            )
        if not verdict or not risk:
            raise MindParseError(
                "Both a verdict and a risk are required; one was left empty. "
                "Please answer both prompts."
            )
        return f"Verdict: {verdict}\nRisk: {risk}"


def _post_json(
    url: str, payload: dict, headers: dict, timeout: int
) -> dict:
    """POST a JSON payload with urllib (stdlib) and return the parsed JSON."""
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8")[:500]
        except Exception:
            detail = ""
        raise RuntimeError(
            f"Backend request failed: HTTP {exc.code} from {url}. {detail}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Backend request failed: could not reach {url} ({exc.reason})."
        ) from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Backend at {url} returned non-JSON: {body[:300]!r}"
        ) from exc


class OllamaBackend(Backend):
    """Local Ollama backend: POSTs to the Ollama generate API.

    Graceful when Ollama isn't running: raises a RuntimeError that says so,
    instead of a raw connection traceback.
    """

    def __init__(
        self,
        model: str = "llama3.1",
        host: str = "http://localhost:11434",
        timeout: int = 180,
        label: Optional[str] = None,
    ) -> None:
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout
        self._label = label or "ollama"

    @property
    def name(self) -> str:
        return self._label

    def generate(self, prompt: str) -> str:
        url = f"{self.host}/api/generate"
        try:
            result = _post_json(
                url,
                {"model": self.model, "prompt": prompt, "stream": False},
                {"Content-Type": "application/json"},
                self.timeout,
            )
        except RuntimeError as exc:
            raise RuntimeError(
                f"Ollama backend error: {exc} "
                f"Is Ollama running? Start it with `ollama serve` and pull the "
                f"model with `ollama pull {self.model}`."
            ) from exc
        response = result.get("response", "")
        if not response or not response.strip():
            raise RuntimeError(
                f"Ollama returned an empty response for model {self.model!r}."
            )
        return response


class OpenAICompatBackend(Backend):
    """Any OpenAI-compatible chat-completions endpoint.

    The API key is read ONLY from the named environment variable (default
    OPENAI_API_KEY). It is never logged, printed, or written to any file —
    error messages name the variable, never the value.
    """

    def __init__(
        self,
        model: str,
        base_url: str,
        env_var: str = "OPENAI_API_KEY",
        timeout: int = 180,
        label: Optional[str] = None,
    ) -> None:
        if not model or not model.strip():
            raise ValueError("OpenAICompatBackend requires a non-empty model name.")
        if not base_url or not base_url.strip():
            raise ValueError("OpenAICompatBackend requires a non-empty base_url.")
        self.model = model.strip()
        self.base_url = base_url.strip().rstrip("/")
        self.env_var = env_var
        self.timeout = timeout
        self._label = label or "openai-compat"

    @property
    def name(self) -> str:
        return self._label

    def _api_key(self) -> str:
        key = os.environ.get(self.env_var, "")
        if not key.strip():
            raise RuntimeError(
                f"OpenAI-compatible backend needs the {self.env_var} environment "
                f"variable set (e.g. `export {self.env_var}=...`). The key is read "
                "from the environment only — never from files, and never printed."
            )
        return key.strip()

    def generate(self, prompt: str) -> str:
        api_key = self._api_key()  # value stays local; never logged
        url = f"{self.base_url}/chat/completions"
        result = _post_json(
            url,
            {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            },
            {
                "Content-Type": "application/json",
                # The key travels only in this header, to the operator's own endpoint.
                "Authorization": f"Bearer {api_key}",
            },
            self.timeout,
        )
        try:
            content = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                f"OpenAI-compatible endpoint at {self.base_url} returned an "
                f"unexpected payload: {json.dumps(result)[:300]}"
            ) from exc
        if not content or not content.strip():
            raise RuntimeError(
                f"OpenAI-compatible endpoint at {self.base_url} returned empty content."
            )
        return content


BACKEND_NAMES = ("manual", "ollama", "openai-compat")


def build_backend(
    name: str,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    ollama_host: str = "http://localhost:11434",
    env_var: str = "OPENAI_API_KEY",
) -> Backend:
    """Instantiate a backend by name. Raises ValueError on unknown names."""
    if name == "manual":
        return ManualBackend()
    if name == "ollama":
        return OllamaBackend(model=model or "llama3.1", host=ollama_host)
    if name == "openai-compat":
        return OpenAICompatBackend(
            model=model or "", base_url=base_url or "", env_var=env_var
        )
    raise ValueError(
        f"Unknown backend {name!r}. Choose from: {', '.join(BACKEND_NAMES)}."
    )
