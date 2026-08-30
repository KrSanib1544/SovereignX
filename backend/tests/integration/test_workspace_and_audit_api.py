# backend/tests/integration/test_workspace_and_audit_api.py
"""
Integration tests for Workspace, Document Ingestion, Query, and Audit APIs.
"""

import io
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_workspace_crud_and_query_flow():
    # 1. Create workspace
    create_res = client.post("/api/v1/workspaces", json={
        "name": "Integration Test Unit 9",
        "description": "Test workspace for API verification",
        "classification_level": "INTERNAL_ENGINEERING"
    })
    assert create_res.status_code == 201
    ws_data = create_res.json()
    ws_id = ws_data["id"]
    assert ws_data["name"] == "Integration Test Unit 9"

    # 2. List workspaces
    list_res = client.get("/api/v1/workspaces")
    assert list_res.status_code == 200
    workspaces = list_res.json()
    assert any(w["id"] == ws_id for w in workspaces)

    # 3. Get single workspace
    get_res = client.get(f"/api/v1/workspaces/{ws_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == ws_id

    # 4. Upload a text document
    file_content = b"Pump 4C impeller inspection record. Vibration level: 2.4 mm/s RMS."
    upload_res = client.post(
        f"/api/v1/workspaces/{ws_id}/documents",
        files=[("files", ("pump_4c_log.txt", io.BytesIO(file_content), "text/plain"))],
        data={"enable_ocr": "false"}
    )
    assert upload_res.status_code == 201
    upload_data = upload_res.json()
    assert upload_data["ingested_count"] == 1

    # 5. List documents
    docs_res = client.get(f"/api/v1/workspaces/{ws_id}/documents")
    assert docs_res.status_code == 200
    docs = docs_res.json()
    assert len(docs) >= 1
    doc_id = docs[0]["id"]

    # 6. Get single document details
    doc_detail_res = client.get(f"/api/v1/workspaces/{ws_id}/documents/{doc_id}")
    assert doc_detail_res.status_code == 200
    assert doc_detail_res.json()["filename"] == "pump_4c_log.txt"

    # 7. Semantic query
    query_res = client.post(f"/api/v1/workspaces/{ws_id}/query", json={
        "query": "impeller vibration level",
        "top_k": 3
    })
    assert query_res.status_code == 200
    assert isinstance(query_res.json(), list)

    # 8. Audit verification
    audit_verify_res = client.post("/api/v1/audit/verify")
    assert audit_verify_res.status_code == 200
    assert audit_verify_res.json()["is_valid"] is True

    # 9. List audit events
    audit_list_res = client.get(f"/api/v1/audit?workspace_id={ws_id}")
    assert audit_list_res.status_code == 200
    events = audit_list_res.json()
    assert len(events) >= 1

    # 10. Delete workspace
    del_res = client.delete(f"/api/v1/workspaces/{ws_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "DELETED"
