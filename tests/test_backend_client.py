
import asyncio
import httpx

from app.services.backend_client import BackendClient


async def main():
    backend = BackendClient()

    # Test 1: Public endpoint
    response = await backend.get("/openapi.json")

    print("Public endpoint:", response.status_code if hasattr(response, "status_code") else "200 OK")
    print("Backend reachable:", isinstance(response, dict))

    # Test 2: Protected endpoint without Firebase token
    try:
        await backend.get("/api/v1/auth/me")
        print("Authentication check: Unexpected success")

    except httpx.HTTPStatusError as error:
        print("Protected endpoint status:", error.response.status_code)

        if error.response.status_code == 401:
            print("Authentication enforcement: Passed")

    except httpx.RequestError as error:
        print("Network error:", str(error))


if __name__ == "__main__":
    asyncio.run(main())
