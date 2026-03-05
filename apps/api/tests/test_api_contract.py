import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

os.environ["XPLAIN_STORAGE"] = "inmemory"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402


client = TestClient(app)


def test_not_found_returns_structured_error() -> None:
    response = client.get("/api/v1/processes/does-not-exist")

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "process_not_found"
    assert payload["error"]["message"] == "Process not found"


def test_create_with_blank_title_is_validation_error() -> None:
    response = client.post(
        "/api/v1/processes",
        json={"title": "   ", "description": "sample"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["message"] == "Request validation failed"
    assert isinstance(payload["error"]["details"], list)


def test_generate_graph_with_empty_text_is_bad_request() -> None:
    created = client.post("/api/v1/processes", json={"title": "Demo", "description": None})
    assert created.status_code == 201
    process_id = created.json()["id"]

    response = client.post(f"/api/v1/processes/{process_id}/generate-graph", json={"text": "   "})

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "source_text_empty"
    assert payload["error"]["message"] == "Source text is empty"


def test_generate_graph_success_increments_version() -> None:
    created = client.post(
        "/api/v1/processes",
        json={"title": "Order Processing", "description": "Receive order. Validate payment. Ship item."},
    )
    assert created.status_code == 201
    initial = created.json()

    generated = client.post(f"/api/v1/processes/{initial['id']}/generate-graph", json={"text": None})
    assert generated.status_code == 200

    payload = generated.json()
    assert payload["version"] == initial["version"] + 1
    assert len(payload["graph"]["nodes"]) >= 1
    assert len(payload["graph"]["edges"]) >= 1
    assert "generated:rule-based:v2" in payload["graph"]["sourceRefs"]
    assert "quality" in payload["graph"]
    assert payload["graph"]["quality"]["coverage_percent"] >= 0
    assert payload["graph"]["quality"]["naming_consistency_percent"] >= 0
    assert isinstance(payload["graph"]["quality"]["dangling_nodes"], list)
