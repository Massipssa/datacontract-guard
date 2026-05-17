"""Demo script to validate MCPAdapter and LocalMCPAdapter against a mock server.

Runs the FastAPI mock server (if `uvicorn` and `fastapi` are available) and
exercises both adapters. Designed for local manual runs, not as unit tests.
"""
import time
import os
import sys
from threading import Thread


def _start_mock():
    from tests.mocks.mcp_mock import run

    run()


def main():
    port = int(os.environ.get("MCP_MOCK_PORT", "8001"))

    # ensure project path is on sys.path so the server thread can import modules
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    thr = None
    try:
        # attempt to start mock server in a background thread
        thr = Thread(target=_start_mock, daemon=True)
        thr.start()
        time.sleep(1.0)
    except Exception as e:
        print("Could not start mock server:", e)
    try:
        from contract_agent.adapters.mcp_adapter import MCPAdapter, LocalMCPAdapter
    except Exception as e:
        print("Import error:", e)
        return

    base = f"http://127.0.0.1:{port}"
    try:
        m = MCPAdapter(base)
        print("MCPAdapter.get_contract:")
        print(m.get_contract("example.yaml"))
        print("MCPAdapter.get_schema:")
        print(m.get_schema("datasource", "table"))
    except Exception as e:
        print("MCPAdapter failed:", e)

    print("\nLocalMCPAdapter demo:")
    try:
        local = LocalMCPAdapter()
        print(local.get_contract("example.yaml"))
        print(local.get_schema("datasource", "table"))
    except Exception as e:
        print("Local adapter failed:", e)

    # no special termination needed for the thread (daemon thread)


if __name__ == "__main__":
    main()
