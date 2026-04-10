"""Local Ollama node adapter for SkillForge."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "60"))
MAX_RETRIES = 3


class OllamaNode:
    """Adapter for a locally running Ollama instance.

    Usage::

        node = OllamaNode()
        response = await node.call("gemma3:4b", "Summarise this text …")
    """

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        retries: int = MAX_RETRIES,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.retries = retries

    async def call(
        self,
        model: str,
        prompt: str,
        *,
        system: str = "",
        options: dict[str, Any] | None = None,
    ) -> str:
        """Send a generate request to Ollama and return the response text.

        Retries up to ``self.retries`` times on transient errors.
        """
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options

        last_exc: Exception | None = None

        for attempt in range(1, self.retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(
                        f"{self.base_url}/api/generate",
                        json=payload,
                    )
                    resp.raise_for_status()
                    return resp.json().get("response", "")
            except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as exc:
                last_exc = exc
                logger.warning(
                    "OllamaNode attempt %d/%d failed: %s",
                    attempt,
                    self.retries,
                    exc,
                )

        raise ConnectionError(
            f"OllamaNode: all {self.retries} attempts failed. Last error: {last_exc}"
        )

    async def health(self) -> bool:
        """Return ``True`` if Ollama is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

