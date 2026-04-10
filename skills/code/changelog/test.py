"""Tests for code.changelog skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("changelog_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

GIT_LOG = """abc1234abc1234abc1234abc1234abc12345|feat: add user auth|Ali|2024-01-10
def5678def5678def5678def5678def56789|fix: login redirect bug|Ayse|2024-01-11
aaa9012aaa9012aaa9012aaa9012aaa90123|docs: update README|Ali|2024-01-12
bbb3456bbb3456bbb3456bbb3456bbb34567|feat(api): add pagination|Ayse|2024-01-13
ccc7890ccc7890ccc7890ccc7890ccc78901|fix!: change auth endpoint|Ali|2024-01-14"""

def test_feat_and_fix_counts(w) -> None:
    out = w.run(SkillInput(data={"git_log": GIT_LOG, "version": "1.2.0"}))
    assert out.success is True
    assert out.data["feat_count"] == 2
    assert out.data["fix_count"] == 2
    assert out.data["total_commits"] == 5

def test_breaking_change_detected(w) -> None:
    out = w.run(SkillInput(data={"git_log": GIT_LOG, "version": "2.0.0"}))
    assert out.data["breaking_count"] == 1
    assert "Breaking Changes" in out.data["changelog_md"]

def test_repo_url_links(w) -> None:
    out = w.run(SkillInput(data={
        "git_log": "abc1234|feat: cool feature|Dev|2024-01-01",
        "version": "1.0.0",
        "repo_url": "https://github.com/user/repo",
    }))
    assert "github.com/user/repo/commit/abc1234" in out.data["changelog_md"]

def test_empty_log_error(w) -> None:
    out = w.run(SkillInput(data={"git_log": "", "version": "1.0.0"}))
    assert out.success is False

def test_mixed_commit_types(w) -> None:
    log = "a1|feat: new|D|D\nb2|chore: cleanup|D|D\nc3|perf: speed up|D|D"
    out = w.run(SkillInput(data={"git_log": log, "version": "1.1.0"}))
    assert out.success is True
    md = out.data["changelog_md"]
    assert "Features" in md
    assert "Maintenance" in md
    assert "Performance" in md

