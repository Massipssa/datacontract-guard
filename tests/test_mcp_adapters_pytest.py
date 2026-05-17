import pytest


def test_local_mcp_adapter_reads_contract():
    from contract_agent.adapters.mcp_adapter import LocalMCPAdapter

    local = LocalMCPAdapter()
    content = local.get_contract("example.yaml")
    assert "example contract" in content


def test_mcp_adapter_against_mock(monkeypatch):
    pytest.importorskip("fastapi")
    from tests.mocks.mcp_mock import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    import requests

    def fake_get(url, params=None, timeout=None, headers=None):
        base = "http://127.0.0.1:8001"
        assert url.startswith(base)
        path = url[len(base) :]
        resp = client.get(path, params=params, headers=headers)

        class Resp:
            def __init__(self, r):
                self._r = r

            def raise_for_status(self):
                if not self._r.ok:
                    raise Exception(self._r.text)

            def json(self):
                return self._r.json()

        return Resp(resp)

    def fake_post(url, json=None, timeout=None, headers=None):
        base = "http://127.0.0.1:8001"
        assert url.startswith(base)
        path = url[len(base) :]
        resp = client.post(path, json=json, headers=headers)

        class Resp:
            def __init__(self, r):
                self._r = r

            def raise_for_status(self):
                if not self._r.ok:
                    raise Exception(self._r.text)

            def json(self):
                return self._r.json()

        return Resp(resp)

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(requests, "post", fake_post)

    from contract_agent.adapters.mcp_adapter import MCPAdapter

    m = MCPAdapter("http://127.0.0.1:8001", token="t")
    cont = m.get_contract("example.yaml")
    assert "example contract" in cont
    schema = m.get_schema("datasource", "table")
    assert schema["name"] == "datasource.table"
    res = m.create_alert("slack", "t", "m")
    assert res.get("status") == "ok"
import json
import sys
from pathlib import Path

# ensure project package is importable when tests run directly
import os
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)


def test_local_mcp_adapter_reads_files(tmp_path):
    # use the sample data directory provided in tests/mocks/data
    base = Path(__file__).resolve().parent / "mocks" / "data"
    from contract_agent.adapters.mcp_adapter import LocalMCPAdapter

    adapter = LocalMCPAdapter(str(base))
    content = adapter.get_contract("example.yaml")
    assert "example contract" in content
    schema = adapter.get_schema("datasource", "table")
    assert schema.get("name") == "datasource.table"


def test_mcp_adapter_calls(monkeypatch):
    # monkeypatch requests.get/post to validate headers and responses
    from contract_agent.adapters.mcp_adapter import MCPAdapter

    captured = {}

    class DummyResp:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_get(url, params=None, timeout=None, headers=None):
        captured['last_get'] = dict(url=url, params=params, headers=headers)
        if url.endswith('/contracts'):
            return DummyResp({'content': 'ok'})
        if url.endswith('/schema'):
            return DummyResp({'name': 'x', 'columns': []})
        return DummyResp({})

    def fake_post(url, json=None, timeout=None, headers=None):
        captured['last_post'] = dict(url=url, json=json, headers=headers)
        return DummyResp({'status': 'ok'})

    monkeypatch.setattr('contract_agent.adapters.mcp_adapter.requests.get', fake_get)
    monkeypatch.setattr('contract_agent.adapters.mcp_adapter.requests.post', fake_post)

    m = MCPAdapter('http://127.0.0.1:8001', token='tok')
    assert m.get_contract('ref') == 'ok'
    assert m.get_schema('ds', 'tbl')['name'] == 'x'
    assert m.list_objects('b', 'p') == {}
    assert m.create_alert('c', 't', 'm')['status'] == 'ok'
    assert 'Authorization' in captured['last_get']['headers']
    assert captured['last_get']['headers']['Authorization'].startswith('Bearer')