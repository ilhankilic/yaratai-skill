"""Tests for mediscreen.triage skill."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from skillforge.base import SkillInput, SkillOutput
from skills.mediscreen.triage.worker import Worker

MOCK_LLM_RESPONSE_RED = '{"priority":"KIRMIZI","department":"Kardiyoloji","warning_signs":["göğüs ağrısı","sol kola yayılım"],"reasoning":"Akut koroner sendrom şüphesi."}'
MOCK_LLM_RESPONSE_GREEN = '{"priority":"YESIL","department":"Genel Poliklinik","warning_signs":[],"reasoning":"Hafif üst solunum yolu enfeksiyonu."}'
MOCK_LLM_RESPONSE_MALFORMED = "Bu bir JSON değil, düz metin cevap."


@pytest.fixture
def worker() -> Worker:
    return Worker()


# ── Happy path ───────────────────────────────────────────────────────

def test_triage_red_priority(worker: Worker) -> None:
    """Chest pain radiating to left arm should trigger KIRMIZI."""
    inp = SkillInput(data={
        "age": 55,
        "gender": "erkek",
        "complaint": "Göğüs ağrısı, sol kola yayılıyor",
        "duration": "1 saat",
        "vitals": {"heart_rate": 110, "blood_pressure": "160/95"},
    })
    with patch.object(Worker, "_call_ollama", return_value=MOCK_LLM_RESPONSE_RED):
        out = worker.run(inp)

    assert out.success is True
    assert out.data["priority"] == "KIRMIZI"
    assert out.data["estimated_wait_minutes"] == 0
    assert "göğüs ağrısı" in out.data["warning_signs"]


def test_triage_green_priority(worker: Worker) -> None:
    """Mild cold symptoms should be YESIL."""
    inp = SkillInput(data={
        "age": 25,
        "gender": "kadın",
        "complaint": "Hafif öksürük ve burun akıntısı",
        "duration": "3 gün",
    })
    with patch.object(Worker, "_call_ollama", return_value=MOCK_LLM_RESPONSE_GREEN):
        out = worker.run(inp)

    assert out.success is True
    assert out.data["priority"] == "YESIL"
    assert out.data["estimated_wait_minutes"] == 60


# ── Edge cases ───────────────────────────────────────────────────────

def test_missing_complaint(worker: Worker) -> None:
    """Missing complaint should return failure."""
    inp = SkillInput(data={"age": 30, "gender": "erkek"})
    out = worker.run(inp)
    assert out.success is False
    assert "complaint" in out.error.lower()


def test_malformed_llm_response(worker: Worker) -> None:
    """Non-JSON LLM output should still produce a valid SkillOutput."""
    inp = SkillInput(data={
        "age": 40,
        "gender": "kadın",
        "complaint": "Baş ağrısı",
    })
    with patch.object(Worker, "_call_ollama", return_value=MOCK_LLM_RESPONSE_MALFORMED):
        out = worker.run(inp)

    assert out.success is True
    assert out.data["priority"] == "SARI"  # fallback


# ── Error handling ───────────────────────────────────────────────────

def test_ollama_connection_error(worker: Worker) -> None:
    """Connection error to Ollama should return a graceful failure."""
    import httpx

    inp = SkillInput(data={
        "age": 50,
        "gender": "erkek",
        "complaint": "Karın ağrısı",
    })
    with patch.object(Worker, "_call_ollama", side_effect=httpx.ConnectError("refused")):
        out = worker.run(inp)

    assert out.success is False
    assert "bağlantı" in out.error.lower() or "ollama" in out.error.lower()


def test_ollama_timeout(worker: Worker) -> None:
    """Timeout from Ollama should produce a clear error."""
    import httpx

    inp = SkillInput(data={
        "age": 60,
        "gender": "kadın",
        "complaint": "Nefes darlığı",
    })
    with patch.object(Worker, "_call_ollama", side_effect=httpx.TimeoutException("timeout")):
        out = worker.run(inp)

    assert out.success is False
    assert "zaman aşımı" in out.error.lower() or "timeout" in out.error.lower()


# ── Prompt building ──────────────────────────────────────────────────

def test_build_prompt_includes_all_fields() -> None:
    """Generated prompt should contain all patient data."""
    prompt = Worker._build_prompt(
        age=30,
        gender="erkek",
        complaint="Baş ağrısı",
        duration="2 saat",
        vitals={"temperature": 38.5},
    )
    assert "30" in prompt
    assert "erkek" in prompt
    assert "Baş ağrısı" in prompt
    assert "2 saat" in prompt
    assert "38.5" in prompt

