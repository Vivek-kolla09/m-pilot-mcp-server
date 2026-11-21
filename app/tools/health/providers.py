
import httpx

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.mcpserver.tools.base import ToolError

from app.services.backend_client import BackendClient


backend = BackendClient()


def validate_provider_id(provider_id: int) -> None:
    """Validate that the provider ID is a positive integer."""

    if (
        isinstance(provider_id, bool)
        or not isinstance(provider_id, int)
        or provider_id <= 0
    ):
        raise ValueError(
            "Provider ID must be a positive integer."
        )


def register_health_tools(mcp):
    """Register health-related tools with the M-Pilot MCP server."""

    @mcp.tool()
    async def get_connected_providers() -> dict:
        """
        Retrieve all health providers connected by the authenticated user.

        Returns provider names, connection status, sync status,
        and synchronization timestamps.
        """

        access_token = get_access_token()

        if access_token is None or not access_token.token:
            raise ToolError("Authentication required.")

        try:
            providers = await backend.get(
                endpoint="/api/v1/providers/",
                firebase_id_token=access_token.token,
            )

            if not isinstance(providers, list):
                raise ToolError(
                    "Unexpected response received from the backend."
                )

            safe_providers = []

            for provider in providers:
                if not isinstance(provider, dict):
                    raise ToolError(
                        "Invalid provider data received from the backend."
                    )

                safe_providers.append({
                    "id": provider.get("id"),
                    "provider_name": provider.get("provider_name"),
                    "status": provider.get("status"),
                    "sync_status": provider.get("sync_status"),
                    "last_synced_at": provider.get("last_synced_at"),
                    "created_at": provider.get("created_at"),
                })

            return {
                "count": len(safe_providers),
                "providers": safe_providers,
            }

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            if status_code == 401:
                raise ToolError(
                    "Authentication failed."
                ) from exc

            if status_code == 403:
                raise ToolError(
                    "Access to providers is forbidden."
                ) from exc

            if status_code == 404:
                raise ToolError(
                    "Authenticated user was not found."
                ) from exc

            raise ToolError(
                "Unable to retrieve connected providers from the backend."
            ) from exc

        except httpx.RequestError as exc:
            raise ToolError(
                "Unable to connect to the M-Pilot backend."
            ) from exc

    @mcp.tool()
    async def sync_health_data(provider_id: int) -> dict:
        """
        Synchronize health data from a selected connected provider.

        Requires an explicit provider ID obtained from
        get_connected_providers.

        Fetches health data and inserts or updates records
        through the authenticated M-Pilot backend.
        """

        # Step 1: Validate the provider ID
        validate_provider_id(provider_id)

        # Step 2: Retrieve the authenticated user's token
        access_token = get_access_token()

        if access_token is None or not access_token.token:
            raise ToolError("Authentication required.")

        # Step 3: Trigger synchronization through the backend
        try:
            result = await backend.post(
                endpoint=f"/api/v1/providers/{provider_id}/sync",
                firebase_id_token=access_token.token,
            )

            # Step 4: Validate the backend response
            if not isinstance(result, dict):
                raise ToolError(
                    "Unexpected synchronization response from the backend."
                )

            required_fields = [
                "message",
                "provider",
                "source",
                "records_inserted",
                "records_updated",
                "total_processed",
            ]

            if not all(field in result for field in required_fields):
                raise ToolError(
                    "Incomplete synchronization response received."
                )

            # Step 5: Return safe synchronization details
            return {
                "message": result["message"],
                "provider": result["provider"],
                "source": result["source"],
                "records_inserted": result["records_inserted"],
                "records_updated": result["records_updated"],
                "total_processed": result["total_processed"],
            }

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            if status_code == 401:
                raise ToolError(
                    "Authentication failed."
                ) from exc

            if status_code == 403:
                raise ToolError(
                    "You are not authorized to synchronize this provider."
                ) from exc

            if status_code == 404:
                raise ToolError(
                    "Provider or authenticated user was not found."
                ) from exc

            if status_code == 422:
                raise ToolError(
                    "Invalid provider ID supplied for synchronization."
                ) from exc

            raise ToolError(
                "Health data synchronization failed on the backend."
            ) from exc

        except httpx.RequestError as exc:
            raise ToolError(
                "Unable to connect to the M-Pilot backend."
            ) from exc
