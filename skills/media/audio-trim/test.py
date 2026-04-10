"""Tests for media.audio-trim skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("media_audio_trim_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

def test_basic_trim(w):
    out = w.run(SkillInput(data={"audio_data": "dGVzdA==", "start_ms": 0, "end_ms": 5000}))
    assert out.success and out.data["trimmed_duration_ms"] == 5000

def test_fade_in_out(w):
    out = w.run(SkillInput(data={"audio_data": "dGVzdA==", "start_ms": 0, "end_ms": 3000, "fade_in_ms": 500, "fade_out_ms": 500}))
    assert out.success

def test_no_end(w):
    out = w.run(SkillInput(data={"audio_data": "dGVzdA==", "start_ms": 1000}))
    assert out.success

def test_normalize(w):
    out = w.run(SkillInput(data={"audio_data": "dGVzdA==", "start_ms": 0, "normalize": True}))
    assert out.success

def test_empty_error(w):
    out = w.run(SkillInput(data={"audio_data": ""}))
    assert out.success is False
