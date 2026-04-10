"""Tests for devops.nginx-conf skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("devops_nginx_conf_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_single_domain_http(w):
    out = w.run(SkillInput(data={"domains": [{"server_name": "example.com", "upstream_port": 3000}], "use_ssl": False}))
    assert "listen 80" in out.data["nginx_conf"]

def test_ssl_certbot(w):
    out = w.run(SkillInput(data={"domains": [{"server_name": "x.com", "upstream_port": 3000}], "use_ssl": True}))
    assert len(out.data["certbot_commands"]) == 1

def test_www_redirect(w):
    out = w.run(SkillInput(data={"domains": [{"server_name": "x.com", "upstream_port": 80, "www_redirect": True}], "use_ssl": True}))
    assert "return 301" in out.data["nginx_conf"]

def test_rate_limiting(w):
    out = w.run(SkillInput(data={"domains": [{"server_name": "x.com", "upstream_port": 80}], "rate_limiting": True}))
    assert "limit_req" in out.data["nginx_conf"]

def test_empty_domains_error(w):
    out = w.run(SkillInput(data={"domains": []}))
    assert out.success is False
