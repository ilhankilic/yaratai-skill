"""Tests for ai.ollama-orchestrate skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("ai_ollama_orchestrate_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

PIPELINE = [
    {"model": "gemma3:4b", "prompt_template": "Summarize: {{initial_input.text}}", "output_key": "summary"},
    {"model": "gemma3:4b", "prompt_template": "Translate: {{results.summary}}", "output_key": "translation"},
]

def test_sequential_pipeline(w):
    out = w.run(SkillInput(data={"pipeline": PIPELINE, "initial_input": {"text": "Hello world"}}))
    assert out.success and "summary" in out.data["results"]

def test_template_filling(w):
    out = w.run(SkillInput(data={"pipeline": PIPELINE, "initial_input": {"text": "Test"}}))
    assert len(out.data["pipeline_log"]) == 2

def test_failed_step(w):
    out = w.run(SkillInput(data={"pipeline": [{"model": "x", "prompt_template": "hi", "output_key": "a"}], "initial_input": {"x": "y"}}))
    assert out.success

def test_empty_pipeline_error(w):
    out = w.run(SkillInput(data={"pipeline": [], "initial_input": {"x": 1}}))
    assert out.success is False

def test_duration_tracked(w):
    out = w.run(SkillInput(data={"pipeline": PIPELINE, "initial_input": {"text": "Hi"}}))
    assert out.data["total_duration_ms"] >= 0
