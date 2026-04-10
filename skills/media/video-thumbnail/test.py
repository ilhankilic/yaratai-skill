"""Tests for media.video-thumbnail skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("media_video_thumbnail_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

def test_timestamp_extraction(w):
    out = w.run(SkillInput(data={"video_path": "test.mp4", "timestamps": [1.0, 5.0]}))
    assert out.success and len(out.data["thumbnails"]) == 2

def test_single_frame(w):
    out = w.run(SkillInput(data={"video_path": "test.mp4", "timestamps": [0.0]}))
    assert out.data["thumbnails"][0]["timestamp"] == 0.0

def test_format_selection(w):
    out = w.run(SkillInput(data={"video_path": "test.mp4", "timestamps": [1.0], "output_format": "png"}))
    assert out.data["thumbnails"][0]["format"] == "png"

def test_video_info(w):
    out = w.run(SkillInput(data={"video_path": "test.mp4", "timestamps": [1.0]}))
    assert out.data["video_duration_seconds"] > 0

def test_empty_path_error(w):
    out = w.run(SkillInput(data={"video_path": "", "timestamps": []}))
    assert out.success is False
