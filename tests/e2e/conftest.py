"""Playwright e2e: runs the real app (uvicorn) with isolated state and export paths."""
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def server(tmp_path_factory):
    work = tmp_path_factory.mktemp("pmos_e2e")
    port = _free_port()
    env = {**os.environ, "PMOS_STATE_DIR": str(work / "state"), "PMOS_EXPORT_PATH": str(work / "ROADMAP.md")}
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port)],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    for _ in range(120):
        try:
            urllib.request.urlopen(url + "/api/pmos/sources?limit=1", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    else:
        proc.terminate()
        raise RuntimeError("app did not start")
    yield {"url": url, "state": work / "state", "export": work / "ROADMAP.md"}
    proc.terminate()
    proc.wait(timeout=10)


@pytest.fixture(scope="session")
def base_url(server):
    return server["url"]


@pytest.fixture(autouse=True)
def clean_state(server):
    """Every test starts with an empty event log (state is read from files per request)."""
    shutil.rmtree(server["state"], ignore_errors=True)
    server["export"].unlink(missing_ok=True) if sys.version_info >= (3, 8) else None
    yield


@pytest.fixture(scope="session")
def commitment_items():
    """(item id, due date) for each commitment, from the derived backlog on disk."""
    bl = json.load(open(os.path.join(ROOT, "data/companies/12labs/derived/backlog.json")))
    com = {c["id"]: c for c in json.load(open(os.path.join(ROOT, "data/companies/12labs/commitments.json")))}
    return [(i["id"], com[i["commitment_id"]]["due_date"]) for i in bl["items"] if i.get("commitment_id")]
