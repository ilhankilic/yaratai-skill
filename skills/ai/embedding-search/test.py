"""Tests for ai.embedding-search skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("ai_embedding_search_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

DOCS = [
    {"id": "1", "text": "Python is a programming language", "metadata": {}},
    {"id": "2", "text": "JavaScript runs in the browser", "metadata": {}},
    {"id": "3", "text": "Docker containers are lightweight", "metadata": {}},
]

def test_semantic_search(w):
    out = w.run(SkillInput(data={"documents": DOCS, "query": "programming language"}))
    assert out.success and out.data["results"][0]["id"] == "1"

def test_threshold_filter(w):
    out = w.run(SkillInput(data={"documents": DOCS, "query": "programming", "similarity_threshold": 0.9}))
    assert len(out.data["results"]) <= len(DOCS)

def test_top_k(w):
    out = w.run(SkillInput(data={"documents": DOCS, "query": "test", "top_k": 1}))
    assert len(out.data["results"]) <= 1

def test_documents_indexed(w):
    out = w.run(SkillInput(data={"documents": DOCS, "query": "Docker"}))
    assert out.data["documents_indexed"] == 3

def test_empty_query_error(w):
    out = w.run(SkillInput(data={"documents": DOCS, "query": ""}))
    assert out.success is False
