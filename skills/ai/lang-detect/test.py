"""Tests for ai.lang-detect skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("ai_lang_detect_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_turkish_heuristic(w):
    out = w.run(SkillInput(data={"text": "Merhaba dünya, bu güzel bir gün."}))
    assert out.success and out.data["detected_language"] == "tr"

def test_english_detection(w):
    out = w.run(SkillInput(data={"text": "Hello world, this is a test."}))
    assert out.data["detected_language"] == "en"

def test_short_text_low_confidence(w):
    out = w.run(SkillInput(data={"text": "Hi"}))
    assert out.data["detection_confidence"] <= 0.5

def test_translate_task(w):
    out = w.run(SkillInput(data={"text": "Merhaba", "task": "translate", "target_language": "en"}))
    assert out.data["translated_text"] != ""

def test_mixed_language(w):
    out = w.run(SkillInput(data={"text": "This is mixed içerik with Türkçe."}))
    assert out.success

def test_empty_text_error(w):
    out = w.run(SkillInput(data={"text": ""}))
    assert out.success is False
