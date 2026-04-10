"""Cloud node adapter (RunPod / GCP) for SkillForge."""

from __future__ import annotations

import logging
import os
from typing import Any, AsyncIterator

import httpx

logger = logging.getLogger(__name__)

RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY", "")
RUNPOD_ENDPOINT = os.environ.get("RUNPOD_ENDPOINT", "")
DEFAULT_TIMEOUT = int(os.environ.get("CLOUD_TIMEOUT", "120"))


class RunPodNode:
    """Adapter for RunPod serverless GPU endpoints.

    Usage::

        node = RunPodNode(api_key="...", endpoint="https://api.runpod.ai/v2/xxx")
        response = await node.call("gemma3:4b", "Summarise this …")
    """

    def __init__(
        self,
        api_key: str = RUNPOD_API_KEY,
        endpoint: str = RUNPOD_ENDPOINT,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key:
            raise ValueError("RUNPOD_API_KEY is required for RunPodNode.")
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout

    async def call(
        self,
        model: str,
        prompt: str,
        *,
        system: str = "",
        options: dict[str, Any] | None = None,
    ) -> str:
        """Submit a synchronous run request to RunPod and return the result."""
        payload: dict[str, Any] = {
            "input": {
                "model": model,
                "prompt": prompt,
                "system": system,
                "options": options or {},
            }
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.endpoint}/runsync",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            body = resp.json()

        output = body.get("output", {})
        if isinstance(output, str):
            return output
        return output.get("response", output.get("text", ""))

    async def call_stream(
        self,
        model: str,
        prompt: str,
        *,
        system: str = "",
        options: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Submit a streaming run request to RunPod."""
        payload: dict[str, Any] = {
            "input": {
                "model": model,
                "prompt": prompt,
                "system": system,
                "stream": True,
                "options": options or {},
            }
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Start async run
            resp = await client.post(
                f"{self.endpoint}/run",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            run_id = resp.json().get("id", "")

            # Poll for stream chunks
            stream_url = f"{self.endpoint}/stream/{run_id}"
            while True:
                stream_resp = await client.get(stream_url, headers=headers)
                stream_resp.raise_for_status()
                data = stream_resp.json()

                for chunk in data.get("stream", []):
                    text = chunk.get("output", "")
                    if text:
                        yield text

                if data.get("status") in ("COMPLETED", "FAILED"):
                    break

    async def health(self) -> bool:
        """Return ``True`` if the RunPod endpoint responds."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.endpoint}/health",
                    headers=headers,
                )
                return resp.status_code == 200
        except Exception:
            return False

