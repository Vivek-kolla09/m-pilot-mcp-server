
import httpx
import pytest

from app.services.backend_client import BackendClient


@pytest.mark.asyncio
async def test_get_success():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/api/v1/health"
        return httpx.Response(200, json={"status": "success"})

    transport = httpx.MockTransport(handler)
    backend = BackendClient(
        base_url="https://test.example",
        transport=transport,
    )

    result = await backend.get("/api/v1/health")

    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_post_success():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/api/v1/health"
        return httpx.Response(201, json={"message": "created"})

    transport = httpx.MockTransport(handler)
    backend = BackendClient(
        base_url="https://test.example",
        transport=transport,
    )

    result = await backend.post(
        "/api/v1/health",
        json={"metric_type": "steps"},
    )

    assert result == {"message": "created"}


@pytest.mark.asyncio
async def test_get_forwards_firebase_token():
    def handler(request):
        assert request.headers["Authorization"] == "Bearer test-token"
        return httpx.Response(200, json={"authenticated": True})

    transport = httpx.MockTransport(handler)
    backend = BackendClient(
        base_url="https://test.example",
        transport=transport,
    )

    result = await backend.get(
        "/api/v1/auth/me",
        firebase_id_token="test-token",
    )

    assert result == {"authenticated": True}


@pytest.mark.asyncio
async def test_get_raises_http_status_error():
    def handler(request):
        return httpx.Response(401, json={"detail": "Unauthorized"})

    transport = httpx.MockTransport(handler)
    backend = BackendClient(
        base_url="https://test.example",
        transport=transport,
    )

    with pytest.raises(httpx.HTTPStatusError):
        await backend.get("/api/v1/auth/me")


@pytest.mark.asyncio
async def test_get_raises_network_error():
    def handler(request):
        raise httpx.ConnectError("Simulated connection failure")

    transport = httpx.MockTransport(handler)
    backend = BackendClient(
        base_url="https://test.example",
        transport=transport,
    )

    with pytest.raises(httpx.RequestError):
        await backend.get("/api/v1/health")



@pytest.mark.asyncio
async def test_post_forwards_firebase_token():
    def handler(request):
        assert request.headers["Authorization"] == "Bearer test-token"
        return httpx.Response(201, json={"message": "created"})

    transport = httpx.MockTransport(handler)
    backend = BackendClient(
        base_url="https://test.example",
        transport=transport,
    )

    result = await backend.post(
        "/api/v1/health",
        firebase_id_token="test-token",
        json={"metric_type": "steps"},
    )

    assert result == {"message": "created"}


@pytest.mark.asyncio
async def test_post_raises_http_status_error():
    def handler(request):
        return httpx.Response(500, json={"detail": "Internal Server Error"})

    transport = httpx.MockTransport(handler)
    backend = BackendClient(
        base_url="https://test.example",
        transport=transport,
    )

    with pytest.raises(httpx.HTTPStatusError):
        await backend.post("/api/v1/health")


@pytest.mark.asyncio
async def test_get_forwards_query_parameters():
    def handler(request):
        assert request.url.params["metric_type"] == "steps"
        assert request.url.params["limit"] == "5"
        return httpx.Response(200, json={"count": 5})

    transport = httpx.MockTransport(handler)
    backend = BackendClient(
        base_url="https://test.example",
        transport=transport,
    )

    result = await backend.get(
        "/api/v1/health",
        params={"metric_type": "steps", "limit": 5},
    )

    assert result == {"count": 5}

