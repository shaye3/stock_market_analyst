"""
Base agent class — wraps the Anthropic Claude client with retry logic and JSON parsing.
"""
import json
import logging
import os
import re
import time

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-6"


class BaseAgent:
    """Shared Claude client and helpers for all specialized agents."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self._client: Anthropic | None = None

    @property
    def client(self) -> Anthropic:
        """Lazy-initialize the Anthropic client on first use."""
        if self._client is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY is not set. "
                    "Add it to your .env file or export it as an environment variable."
                )
            self._client = Anthropic(api_key=api_key)
        return self._client

    # ── Claude call ──────────────────────────────────────────────────────────

    def call_claude(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        retries: int = 3,
    ) -> str:
        """Call Claude with exponential-backoff retry on failure."""
        for attempt in range(retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                return response.content[0].text
            except Exception as e:
                logger.warning(f"Claude call attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2**attempt)
                else:
                    raise
        return ""

    # ── JSON extraction ──────────────────────────────────────────────────────

    def extract_json(self, text: str) -> dict:
        """
        Robustly extract a JSON object from Claude's response.
        Tries: outermost {…} scan → fenced code block → full text parse.
        """
        if not text:
            return {}

        # 1. Find outermost { … } by counting brace depth (handles nesting)
        start = text.find("{")
        if start != -1:
            depth = 0
            in_string = False
            escape_next = False
            for i, ch in enumerate(text[start:], start):
                if escape_next:
                    escape_next = False
                    continue
                if ch == "\\" and in_string:
                    escape_next = True
                    continue
                if ch == '"' and not escape_next:
                    in_string = not in_string
                if not in_string:
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            candidate = text[start:i + 1]
                            try:
                                return json.loads(candidate)
                            except json.JSONDecodeError:
                                break  # fall through to other strategies

        # 2. Strip code fence markers and retry
        stripped = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

        logger.error("Could not parse JSON from response: %s…", text[:300])
        return {"error": "Failed to parse JSON", "raw_snippet": text[:500]}

    # ── Convenience ──────────────────────────────────────────────────────────

    def call_and_parse(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
    ) -> dict:
        """Call Claude and return the parsed JSON dict."""
        try:
            text = self.call_claude(system_prompt, user_prompt, max_tokens)
            return self.extract_json(text)
        except Exception as e:
            logger.error("Agent call_and_parse failed: %s", e)
            return {"error": str(e)}
