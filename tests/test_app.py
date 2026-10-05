import importlib
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    sys.modules.pop("routentool_mvp", None)
    module = importlib.import_module("routentool_mvp")
    module.app.config["TESTING"] = True
    return module.app.test_client()


def test_root_redirects_to_dashboard(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")


def test_dashboard_renders(client):
    assert client.get("/dashboard").status_code == 200


def test_add_manual_creates_delivery(client):
    response = client.post("/add_manual", data={"kunde": "DHL", "adresse": "Aschaffenburg", "type": "🚚 LKW", "priority": "VIP"})
    assert response.status_code == 302
    assert "Aschaffenburg" in client.get("/export").get_data(as_text=True)


def test_add_manual_rejects_invalid_vehicle(client):
    response = client.post("/add_manual", data={"kunde": "DHL", "adresse": "X", "type": "Rakete", "priority": "Normal"})
    assert response.status_code == 400


def test_customer_name_is_not_injected_into_script(client):
    payload = '</script><script>alert(1)</script>'
    client.post("/add_manual", data={"kunde": payload, "adresse": "X", "type": "🚚 LKW", "priority": "Normal"})
    html = client.get("/dashboard").get_data(as_text=True)
    assert payload not in html


def test_ai_dispatch_returns_reply(client):
    response = client.post("/ai_auto_dispatch")
    assert response.status_code == 200
    assert "reply" in response.get_json()
