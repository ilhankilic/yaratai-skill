"""Tests for ai.fine-tune-prep skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("ai_fine_tune_prep_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

DATA = [{"question": "What is 1+1?", "answer": "2"}, {"question": "Capital of Turkey?", "answer": "Ankara"},
        {"question": "Python creator?", "answer": "Guido"}, {"question": "HTTP port?", "answer": "80"}]

def test_alpaca_format(w):
    out = w.run(SkillInput(data={"raw_data": DATA, "output_format": "alpaca", "shuffle": False}))
    assert out.success and "instruction" in out.data["format_example"]

def test_sharegpt_format(w):
    out = w.run(SkillInput(data={"raw_data": DATA, "output_format": "sharegpt", "shuffle": False}))
    assert "conversations" in out.data["format_example"]

def test_train_val_split(w):
    out = w.run(SkillInput(data={"raw_data": DATA, "train_split": 0.75, "shuffle": False}))
    assert out.data["train_count"] == 3 and out.data["val_count"] == 1

def test_system_prompt(w):
    out = w.run(SkillInput(data={"raw_data": DATA, "output_format": "chatml", "system_prompt": "Be helpful", "shuffle": False}))
    assert "system" in out.data["train_jsonl"]

def test_empty_data_error(w):
    out = w.run(SkillInput(data={"raw_data": []}))
    assert out.success is False
