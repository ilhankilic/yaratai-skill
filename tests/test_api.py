"""Tests for the SkillForge REST API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from skillforge.api.app import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


# ── Health ───────────────────────────────────────────────────────────

def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert "skills_loaded" in body
    assert "version" in body


# ── Skills list ──────────────────────────────────────────────────────

def test_list_skills(client: TestClient) -> None:
    r = client.get("/api/skills")
    assert r.status_code == 200
    skills = r.json()
    assert isinstance(skills, list)
    assert len(skills) > 0
    assert "skill_id" in skills[0]


def test_list_skills_filter_category(client: TestClient) -> None:
    r = client.get("/api/skills?category=data")
    assert r.status_code == 200
    skills = r.json()
    for s in skills:
        assert s["skill_id"].startswith("data.")


# ── Skill info ───────────────────────────────────────────────────────

def test_skill_info(client: TestClient) -> None:
    r = client.get("/api/skills/data.json-to-csv/info")
    assert r.status_code == 200
    body = r.json()
    assert body["skill_id"] == "data.json-to-csv"
    assert "schema_input" in body


def test_skill_info_not_found(client: TestClient) -> None:
    r = client.get("/api/skills/nonexistent.skill/info")
    assert r.status_code == 404


# ── Skill execution ─────────────────────────────────────────────────

def test_run_json_to_csv(client: TestClient) -> None:
    r = client.post("/api/skills/data.json-to-csv/run", json={
        "data": {
            "records": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25},
            ]
        }
    })
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "csv" in body["data"]
    assert body["data"]["row_count"] == 2


def test_run_skill_not_found(client: TestClient) -> None:
    r = client.post("/api/skills/fake.skill/run", json={"data": {}})
    assert r.status_code == 404


def test_run_skill_validation_error(client: TestClient) -> None:
    """Running json-to-csv with empty records should return success=False."""
    r = client.post("/api/skills/data.json-to-csv/run", json={
        "data": {"records": []}
    })
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False


# ── Sync validation ──────────────────────────────────────────────────

def test_validate_existing_skill(client: TestClient) -> None:
    r = client.post("/api/sync/validate", json={
        "skill_path": "data/json-to-csv"
    })
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert body["skill_id"] == "data.json-to-csv"


def test_validate_nonexistent(client: TestClient) -> None:
    r = client.post("/api/sync/validate", json={
        "skill_path": "nonexistent/skill"
    })
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is False


# ── Panel ────────────────────────────────────────────────────────────

def test_panel_loads(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "SkillForge" in r.text

