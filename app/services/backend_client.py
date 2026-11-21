
import httpx
from typing import Any

from app.config import settings


class BackendClient:
    """Async HTTP client for communicating with the M-Pilot backend."""

    def __init__(
        self,
        base_url: str = settings.BACKEND_BASE_URL,
        timeout: float = 15.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.transport = transport

    async def get(
        self,
        endpoint: str,
        firebase_id_token: str | None = None,
        params: dict | None = None,
    ) -> Any:
        """Send an authenticated GET request to the backend."""

        headers = {}

        if firebase_id_token:
            headers["Authorization"] = f"Bearer {firebase_id_token}"

        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            transport=self.transport,
        ) as client:

            response = await client.get(
                endpoint,
                headers=headers,
                params=params,
            )

            response.raise_for_status()
            return response.json()

    async def post(
        self,
        endpoint: str,
        firebase_id_token: str | None = None,
        json: dict | None = None,
    ) -> Any:
        """Send an authenticated POST request to the backend."""

        headers = {}

        if firebase_id_token:
            headers["Authorization"] = f"Bearer {firebase_id_token}"

        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            transport=self.transport,
        ) as client:

            response = await client.post(
                endpoint,
                headers=headers,
                json=json,
            )

            response.raise_for_status()
            return response.json()
