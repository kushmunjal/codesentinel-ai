import threading
import time

import pytest
import uvicorn
from playwright.sync_api import sync_playwright

from codesentinel.api.main import app

PORT = 8096
BASE_URL = f"http://127.0.0.1:{PORT}"

@pytest.fixture(scope="module")
def console_server():
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="error"))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    
    # Wait for server to start
    start_time = time.time()
    while time.time() - start_time < 5:
        try:
            import urllib.request
            with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=1) as resp:
                if resp.status == 200:
                    break
        except (OSError, urllib.error.URLError):
            time.sleep(0.1)
    yield BASE_URL
    server.should_exit = True

def test_api_health_route(console_server):
    with sync_playwright() as p:
        req = p.request.new_context(base_url=console_server)
        resp = req.get("/api/health")
        assert resp.status == 200
        data = resp.json()
        assert data.get("status") == "ok"

def test_api_stats_route(console_server):
    with sync_playwright() as p:
        req = p.request.new_context(base_url=console_server)
        resp = req.get("/api/stats")
        assert resp.status == 200
        data = resp.json()
        assert "open_prs" in data
        assert "open_issues" in data
        assert "ready_to_merge" in data

def test_api_prs_route(console_server):
    with sync_playwright() as p:
        req = p.request.new_context(base_url=console_server)
        resp = req.get("/api/prs")
        assert resp.status == 200
        assert isinstance(resp.json(), list)

def test_api_issues_route(console_server):
    with sync_playwright() as p:
        req = p.request.new_context(base_url=console_server)
        resp = req.get("/api/issues")
        assert resp.status == 200
        assert isinstance(resp.json(), list)

def test_api_not_found(console_server):
    with sync_playwright() as p:
        req = p.request.new_context(base_url=console_server)
        resp = req.get("/api/nonexistent_endpoint")
        assert resp.status == 404
        assert "error" in resp.json()

@pytest.mark.parametrize("route", [
    "/",
    "/prs",
    "/issues",
    "/eval",
    "/settings",
    "/activity"
])
def test_console_spa_routes(console_server, route):
    with sync_playwright() as p:
        req = p.request.new_context(base_url=console_server)
        resp = req.get(route)
        assert resp.status == 200
        text = resp.text()
        assert "<div id=\"root\">" in text
        assert "console" in text or "assets" in text
