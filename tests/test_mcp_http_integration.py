import httpx
import json
import app.tools.health.records as records_module
import pytest
from starlette.testclient import TestClient

from mcp.server.auth.provider import AccessToken

from app.main import app
from app.auth.firebase_token_verifier import FirebaseTokenVerifier


# @pytest.fixture(scope="module")
# def client():
#     """Start the MCP application once for this test module."""

#     with TestClient(app) as test_client:
#         yield test_client
@pytest.fixture(scope="module")
def client():
    """Start the MCP application once for this test module."""

    with TestClient(
        app,
        base_url="http://127.0.0.1:8001",
    ) as test_client:
        yield test_client

def test_mcp_route_is_registered():
    paths = [
        getattr(route, "path", None)
        for route in app.routes
    ]

    assert "/mcp" in paths


def test_unauthenticated_mcp_access_is_rejected(client):
    initialize_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {
                "name": "pytest-client",
                "version": "1.0.0",
            },
        },
    }

    response = client.post(
        "/mcp",
        json=initialize_payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )

    assert response.status_code == 401


def test_authenticated_initialization_and_tool_discovery(
    client, monkeypatch
):
    async def mock_verify_token(self, token):
        return AccessToken(
            token=token,
            client_id="pytest",
            scopes=[],
            subject="pytest-user",
            claims={},
        )

    monkeypatch.setattr(
        FirebaseTokenVerifier,
        "verify_token",
        mock_verify_token,
    )

    headers = {
        "Authorization": "Bearer pytest-token",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": "2025-03-26",
    }

    # Initialize MCP session
    response = client.post(
        "/mcp",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "pytest-client",
                    "version": "1.0.0",
                },
            },
        },
    )

    assert response.status_code == 200

    session_id = response.headers.get("mcp-session-id")
    assert session_id is not None

    session_headers = {
        **headers,
        "Mcp-Session-Id": session_id,
    }

    # Complete initialization
    notification_response = client.post(
        "/mcp",
        headers=session_headers,
        json={
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        },
    )

    assert notification_response.status_code in (200, 202)

    # Discover registered tools
    response = client.post(
        "/mcp",
        headers=session_headers,
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        },
    )

    assert response.status_code == 200

    if "text/event-stream" in response.headers.get(
        "content-type", ""
    ):
        rpc_result = None

        for line in response.text.splitlines():
            if line.startswith("data: "):
                rpc_result = json.loads(line[6:])
                break
    else:
        rpc_result = response.json()

    assert rpc_result is not None
    assert "result" in rpc_result

    tools = rpc_result["result"]["tools"]
    tool_names = {tool["name"] for tool in tools}

    expected_tools = {
        "get_connected_providers",
        "sync_health_data",
        "get_latest_health_records",
        "get_health_metrics",
        "get_health_history",
        "get_health_summary",
        "test_connection",
        "get_authenticated_user",
    }

    assert expected_tools.issubset(tool_names)

    # Execute an authenticated MCP tool
    response = client.post(
        "/mcp",
        headers=session_headers,
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "test_connection",
                "arguments": {},
            },
        },
    )

    assert response.status_code == 200

    if "text/event-stream" in response.headers.get(
        "content-type", ""
    ):
        rpc_result = None

        for line in response.text.splitlines():
            if line.startswith("data: "):
                rpc_result = json.loads(line[6:])
                break
    else:
        rpc_result = response.json()

    assert rpc_result is not None
    assert "result" in rpc_result

    tool_result = rpc_result["result"]

    assert tool_result.get("isError") is not True
    assert any(
        "Authenticated M-Pilot MCP server is running successfully!"
        in item.get("text", "")
        for item in tool_result.get("content", [])
    )

    # Verify authenticated user identity
    response = client.post(
        "/mcp",
        headers=session_headers,
        json={
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "get_authenticated_user",
                "arguments": {},
            },
        },
    )

    assert response.status_code == 200

    if "text/event-stream" in response.headers.get(
        "content-type", ""
    ):
        rpc_result = None

        for line in response.text.splitlines():
            if line.startswith("data: "):
                rpc_result = json.loads(line[6:])
                break
    else:
        rpc_result = response.json()

    assert rpc_result is not None
    assert "result" in rpc_result

    tool_result = rpc_result["result"]

    assert tool_result.get("isError") is not True

    identity_data = json.loads(
        tool_result["content"][0]["text"]
    )

    assert identity_data["firebase_uid"] == "pytest-user"


    # Test authenticated health-record retrieval
    captured_request = {}

    async def mock_backend_get(
        endpoint,
        firebase_id_token=None,
        params=None,
    ):
        captured_request["endpoint"] = endpoint
        captured_request["token"] = firebase_id_token
        captured_request["params"] = params

        return [
            {
                "id": 101,
                "provider_name": "Google Fit",
                "metric_type": "steps",
                "value": 8500,
                "unit": "steps",
                "recorded_at": "2026-11-21T08:00:00",
            },
            {
                "id": 102,
                "provider_name": "Fitbit",
                "metric_type": "steps",
                "value": 9200,
                "unit": "steps",
                "recorded_at": "2026-11-21T09:00:00",
            },
        ]

    monkeypatch.setattr(
        records_module.backend,
        "get",
        mock_backend_get,
    )

    response = client.post(
        "/mcp",
        headers=session_headers,
        json={
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "get_latest_health_records",
                "arguments": {
                    "metric_type": "steps",
                    "limit": 5,
                },
            },
        },
    )

    assert response.status_code == 200

    if "text/event-stream" in response.headers.get(
        "content-type", ""
    ):
        rpc_result = None

        for line in response.text.splitlines():
            if line.startswith("data: "):
                rpc_result = json.loads(line[6:])
                break
    else:
        rpc_result = response.json()

    assert rpc_result is not None
    assert "result" in rpc_result

    tool_result = rpc_result["result"]

    assert tool_result.get("isError") is not True

    health_data = json.loads(
        tool_result["content"][0]["text"]
    )

    assert health_data["count"] == 2
    assert len(health_data["records"]) == 2

    assert health_data["records"][0]["metric_type"] == "steps"
    assert health_data["records"][0]["value"] == 8500

    # Verify backend request
    assert captured_request["endpoint"] == "/api/v1/health-records/"
    assert captured_request["token"] == "pytest-token"
    assert captured_request["params"]["metric_type"] == "steps"
    assert captured_request["params"]["limit"] == 5


    # Test backend network failure handling
    async def mock_backend_network_failure(
        endpoint,
        firebase_id_token=None,
        params=None,
    ):
        raise httpx.ConnectError("Simulated network failure")

    monkeypatch.setattr(
        records_module.backend,
        "get",
        mock_backend_network_failure,
    )

    response = client.post(
        "/mcp",
        headers=session_headers,
        json={
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "get_latest_health_records",
                "arguments": {
                    "metric_type": "steps",
                    "limit": 5,
                },
            },
        },
    )

    assert response.status_code == 200

    if "text/event-stream" in response.headers.get(
        "content-type", ""
    ):
        rpc_result = None

        for line in response.text.splitlines():
            if line.startswith("data: "):
                rpc_result = json.loads(line[6:])
                break
    else:
        rpc_result = response.json()

    assert rpc_result is not None
    assert "result" in rpc_result

    tool_result = rpc_result["result"]

    assert tool_result.get("isError") is True

    error_text = tool_result["content"][0]["text"]

    assert "Unable to connect to the M-Pilot backend." in error_text
    assert "Simulated network failure" not in error_text


def test_invalid_bearer_token_is_rejected(client, monkeypatch):

    async def mock_verify_token(self, token):
        return None

    monkeypatch.setattr(
        FirebaseTokenVerifier,
        "verify_token",
        mock_verify_token,
    )

    response = client.post(
        "/mcp",
        headers={
            "Authorization": "Bearer invalid-test-token",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        json={
            "jsonrpc": "2.0",
            "id": 10,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "pytest-client",
                    "version": "1.0.0",
                },
            },
        },
    )

    assert response.status_code == 401

def test_backend_authentication_failure_rejects_request(
    client,
    monkeypatch,
):
    async def mock_verify_token(self, token):
        return None

    monkeypatch.setattr(
        FirebaseTokenVerifier,
        "verify_token",
        mock_verify_token,
    )

    response = client.post(
        "/mcp",
        headers={
            "Authorization": "Bearer backend-failure-token",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        json={
            "jsonrpc": "2.0",
            "id": 11,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "pytest-client",
                    "version": "1.0.0",
                },
            },
        },
    )

    assert response.status_code == 401