"""Tests for api.rate-limit-check skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("api_rate_limit_check_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_successful_requests(w):
    out = w.run(SkillInput(data={"url": "https://api.test.com/health", "request_count": 10}))
    assert out.success and out.data["total_requests"] == 10

def test_rate_limit_simulation(w):
    out = w.run(SkillInput(data={"url": "https://api.test.com/data", "request_count": 20}))
    assert out.data["rate_limited"] > 0

def test_timeline(w):
    out = w.run(SkillInput(data={"url": "https://api.test.com/x", "request_count": 5}))
    assert len(out.data["timeline"]) == 5

def test_max_100_requests(w):
    out = w.run(SkillInput(data={"url": "https://api.test.com", "request_count": 200}))
    assert out.data["total_requests"] <= 100

def test_empty_url_error(w):
    out = w.run(SkillInput(data={"url": ""}))
    assert out.success is False
