"""Tests for ai.prompt-engineer skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("ai_prompt_engineer_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_code_generation(w):
    out = w.run(SkillInput(data={"raw_request": "Write a sorting function", "task_type": "code"}))
    assert out.success and "engineer" in out.data["system_prompt"]

def test_data_extraction(w):
    out = w.run(SkillInput(data={"raw_request": "Extract names from text", "task_type": "extraction"}))
    assert "extraction" in out.data["system_prompt"]

def test_json_format(w):
    out = w.run(SkillInput(data={"raw_request": "List items", "output_format": "json"}))
    assert "JSON" in out.data["system_prompt"]

def test_chain_of_thought(w):
    out = w.run(SkillInput(data={"raw_request": "Analyze this", "chain_of_thought": True}))
    assert "chain_of_thought" in out.data["techniques_used"]

def test_turkish_prompt(w):
    out = w.run(SkillInput(data={"raw_request": "Metin özetle", "language": "tr"}))
    assert "Türkçe" in out.data["system_prompt"]

def test_empty_request_error(w):
    out = w.run(SkillInput(data={"raw_request": ""}))
    assert out.success is False
