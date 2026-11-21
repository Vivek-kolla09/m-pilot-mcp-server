
import httpx
import pytest

from app.auth.firebase_token_verifier import FirebaseTokenVerifier
from mcp.server.auth.provider import AccessToken


@pytest.fixture
def verifier():
    return FirebaseTokenVerifier()


@pytest.mark.asyncio
async def test_valid_firebase_token_returns_access_token(
    verifier,
    monkeypatch,
):
    async def mock_backend_get(
        endpoint,
        firebase_id_token=None,
        params=None,
    ):
        assert endpoint == "/api/v1/auth/me"
        assert firebase_id_token == "valid-test-token"

        return {
            "user": {
                "firebase_uid": "test-user-123",
                "email": "test@example.com",
            }
        }

    monkeypatch.setattr(
        verifier.backend,
        "get",
        mock_backend_get,
    )

    result = await verifier.verify_token("valid-test-token")

    assert isinstance(result, AccessToken)
    assert result.subject == "test-user-123"
    assert result.client_id == "firebase"
    assert result.claims["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_missing_firebase_uid_returns_none(
    verifier,
    monkeypatch,
):
    async def mock_backend_get(
        endpoint,
        firebase_id_token=None,
        params=None,
    ):
        return {
            "user": {
                "email": "test@example.com",
            }
        }

    monkeypatch.setattr(
        verifier.backend,
        "get",
        mock_backend_get,
    )

    result = await verifier.verify_token("test-token")

    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [401, 403])
async def test_rejected_firebase_token_returns_none(
    verifier,
    monkeypatch,
    status_code,
):
    async def mock_backend_get(
        endpoint,
        firebase_id_token=None,
        params=None,
    ):
        request = httpx.Request(
            "GET",
            "https://backend.example.com/api/v1/auth/me",
        )

        response = httpx.Response(
            status_code,
            request=request,
        )

        raise httpx.HTTPStatusError(
            "Authentication rejected",
            request=request,
            response=response,
        )

    monkeypatch.setattr(
        verifier.backend,
        "get",
        mock_backend_get,
    )

    result = await verifier.verify_token("rejected-test-token")

    assert result is None


@pytest.mark.asyncio
async def test_backend_network_failure_returns_none(
    verifier,
    monkeypatch,
):
    async def mock_backend_get(
        endpoint,
        firebase_id_token=None,
        params=None,
    ):
        raise httpx.ConnectError("Simulated network failure")

    monkeypatch.setattr(
        verifier.backend,
        "get",
        mock_backend_get,
    )

    result = await verifier.verify_token("test-token")

    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "malformed_response",
    [
        None,
        [],
        {"user": None},
        {"user": "invalid"},
    ],
)
async def test_malformed_backend_response_returns_none(
    verifier,
    monkeypatch,
    malformed_response,
):
    async def mock_backend_get(
        endpoint,
        firebase_id_token=None,
        params=None,
    ):
        return malformed_response

    monkeypatch.setattr(
        verifier.backend,
        "get",
        mock_backend_get,
    )

    result = await verifier.verify_token("test-token")

    assert result is None
