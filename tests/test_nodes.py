"""Tests for OllamaNode and RunPodNode (mocked, no real services needed)."""

from __future__ import annotations

import pytest
import httpx

from unittest.mock import AsyncMock, patch, MagicMock

from skillforge.nodes.local_node import OllamaNode
from skillforge.nodes.cloud_node import RunPodNode


# ── OllamaNode ───────────────────────────────────────────────────────

class TestOllamaNode:
    @pytest.mark.asyncio
    async def test_call_success(self) -> None:
        node = OllamaNode()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Hello from Ollama"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            result = await node.call("gemma3:4b", "Say hello")

        assert result == "Hello from Ollama"

    @pytest.mark.asyncio
    async def test_call_retry_on_failure(self) -> None:
        node = OllamaNode(retries=2)

        with patch(
            "httpx.AsyncClient.post",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("refused"),
        ):
            with pytest.raises(ConnectionError, match="all 2 attempts failed"):
                await node.call("gemma3:4b", "test")

    @pytest.mark.asyncio
    async def test_health_unreachable(self) -> None:
        node = OllamaNode()
        with patch(
            "httpx.AsyncClient.get",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("refused"),
        ):
            assert await node.health() is False


# ── RunPodNode ───────────────────────────────────────────────────────

class TestRunPodNode:
    def test_missing_api_key_raises(self) -> None:
        with pytest.raises(ValueError, match="RUNPOD_API_KEY"):
            RunPodNode(api_key="", endpoint="https://api.runpod.ai/v2/test")

    @pytest.mark.asyncio
    async def test_call_success(self) -> None:
        node = RunPodNode(api_key="test-key", endpoint="https://api.runpod.ai/v2/xxx")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"output": {"response": "cloud reply"}}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            result = await node.call("gemma3:4b", "test prompt")

        assert result == "cloud reply"

    @pytest.mark.asyncio
    async def test_health_unreachable(self) -> None:
        node = RunPodNode(api_key="test-key", endpoint="https://api.runpod.ai/v2/xxx")
        with patch(
            "httpx.AsyncClient.get",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("refused"),
        ):
            assert await node.health() is False

