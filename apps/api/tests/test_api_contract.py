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

    revisions = client.get(f"/api/v1/processes/{initial['id']}/revisions")
    assert revisions.status_code == 200
    revisions_payload = revisions.json()
    assert len(revisions_payload) >= 2
    assert revisions_payload[0]["version"] == initial["version"] + 1
    assert revisions_payload[1]["version"] == initial["version"]


def test_generate_narrative_requires_generated_graph() -> None:
    created = client.post("/api/v1/processes", json={"title": "Narrative Without Graph", "description": "Sample"})
    assert created.status_code == 201
    process_id = created.json()["id"]

    response = client.post(f"/api/v1/processes/{process_id}/generate-narrative")

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "graph_missing"
    assert payload["error"]["message"] == "Graph is empty. Generate graph before requesting narrative"


def test_generate_narrative_success_returns_structured_sections() -> None:
    created = client.post(
        "/api/v1/processes",
        json={
            "title": "Narrative Demo",
            "description": "User submits form. Backend validates data. Service stores report in database.",
        },
    )
    assert created.status_code == 201
    process_id = created.json()["id"]

    generated = client.post(f"/api/v1/processes/{process_id}/generate-graph", json={"text": None})
    assert generated.status_code == 200

    response = client.post(f"/api/v1/processes/{process_id}/generate-narrative")
    assert response.status_code == 200
    payload = response.json()

    assert payload["processId"] == process_id
    assert payload["version"] >= 1
    assert isinstance(payload["summary"], str)
    assert payload["summary"]
    assert isinstance(payload["steps"], list)
    assert len(payload["steps"]) >= 1
    assert {"id", "title", "detail"} <= set(payload["steps"][0].keys())
    assert isinstance(payload["keyDependencies"], list)
    assert isinstance(payload["references"], list)
    assert len(payload["references"]) >= 1
    assert payload["generatedBy"] == "generated:rule-based:narrative:v1"
    assert "generated:rule-based:v2" in payload["sourceRefs"]


def test_lifecycle_transition_and_locking() -> None:
    created = client.post(
        "/api/v1/processes",
        json={"title": "Lifecycle Demo", "description": "One. Two."},
    )
    assert created.status_code == 201
    process = created.json()
    process_id = process["id"]
    assert process["status"] == "draft"

    review = client.post(
        f"/api/v1/processes/{process_id}/status",
        json={"targetStatus": "in_review"},
    )
    assert review.status_code == 200
    assert review.json()["status"] == "in_review"

    locked_generation = client.post(
        f"/api/v1/processes/{process_id}/generate-graph",
        json={"text": "One. Two."},
    )
    assert locked_generation.status_code == 409
    assert locked_generation.json()["error"]["code"] == "process_locked"

    approved = client.post(
        f"/api/v1/processes/{process_id}/status",
        json={"targetStatus": "approved"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    invalid_back_transition = client.post(
        f"/api/v1/processes/{process_id}/status",
        json={"targetStatus": "draft"},
    )
    assert invalid_back_transition.status_code == 409
    assert invalid_back_transition.json()["error"]["code"] == "invalid_status_transition"


def test_comments_for_process_node_and_edge() -> None:
    created = client.post(
        "/api/v1/processes",
        json={"title": "Comment Flow", "description": "Receive input. Validate. Produce output."},
    )
    assert created.status_code == 201
    process_id = created.json()["id"]

    generated = client.post(f"/api/v1/processes/{process_id}/generate-graph", json={"text": None})
    assert generated.status_code == 200
    graph = generated.json()["graph"]
    node_id = graph["nodes"][0]["id"]
    edge_id = graph["edges"][0]["id"]

    process_comment = client.post(
        f"/api/v1/processes/{process_id}/comments",
        json={"targetType": "process", "message": "Looks clear", "author": "lead"},
    )
    assert process_comment.status_code == 200
    assert process_comment.json()["targetType"] == "process"
    assert process_comment.json()["targetId"] is None

    node_comment = client.post(
        f"/api/v1/processes/{process_id}/comments",
        json={"targetType": "node", "targetId": node_id, "message": "Need more detail"},
    )
    assert node_comment.status_code == 200
    assert node_comment.json()["targetType"] == "node"
    assert node_comment.json()["targetId"] == node_id

    edge_comment = client.post(
        f"/api/v1/processes/{process_id}/comments",
        json={"targetType": "edge", "targetId": edge_id, "message": "Confirm dependency direction"},
    )
    assert edge_comment.status_code == 200
    assert edge_comment.json()["targetType"] == "edge"
    assert edge_comment.json()["targetId"] == edge_id

    listed = client.get(f"/api/v1/processes/{process_id}/comments")
    assert listed.status_code == 200
    payload = listed.json()
    assert len(payload) == 3
    assert payload[0]["id"] == edge_comment.json()["id"]
    assert payload[1]["id"] == node_comment.json()["id"]
    assert payload[2]["id"] == process_comment.json()["id"]


def test_comment_with_invalid_target_returns_bad_request() -> None:
    created = client.post(
        "/api/v1/processes",
        json={"title": "Comment Validation", "description": "Start. Continue. End."},
    )
    assert created.status_code == 201
    process_id = created.json()["id"]

    generated = client.post(f"/api/v1/processes/{process_id}/generate-graph", json={"text": None})
    assert generated.status_code == 200

    invalid_node = client.post(
        f"/api/v1/processes/{process_id}/comments",
        json={"targetType": "node", "targetId": "node-missing", "message": "Bad node"},
    )
    assert invalid_node.status_code == 400
    assert invalid_node.json()["error"]["code"] == "invalid_comment_target"

    invalid_edge = client.post(
        f"/api/v1/processes/{process_id}/comments",
        json={"targetType": "edge", "targetId": "edge-missing", "message": "Bad edge"},
    )
    assert invalid_edge.status_code == 400
    assert invalid_edge.json()["error"]["code"] == "invalid_comment_target"
