

import httpx
import logging

from datetime import datetime

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.mcpserver.tools.base import ToolError

from app.services.backend_client import BackendClient


logger = logging.getLogger(__name__)
backend = BackendClient()


# --------------------------------------------------
# INPUT VALIDATION HELPERS
# --------------------------------------------------

def validate_metric_type(metric_type: str | None) -> str | None:
    """Validate and normalize an optional metric type."""

    if metric_type is None:
        return None

    if not isinstance(metric_type, str):
        raise ValueError("Metric type must be a string.")

    metric_type = metric_type.strip()

    if not metric_type:
        raise ValueError("Metric type cannot be empty.")

    return metric_type


def validate_integer(
    value: int,
    field_name: str,
    minimum: int,
    maximum: int | None = None,
) -> None:
    """Validate an integer while explicitly rejecting booleans."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer.")

    if value < minimum:
        raise ValueError(
            f"{field_name} must be greater than or equal to {minimum}."
        )

    if maximum is not None and value > maximum:
        raise ValueError(
            f"{field_name} must be between {minimum} and {maximum}."
        )


def validate_date_range(
    start_date: str | None,
    end_date: str | None,
) -> None:
    """Validate ISO 8601 dates and their chronological order."""

    parsed_start = None
    parsed_end = None

    if start_date is not None:
        if not isinstance(start_date, str) or not start_date.strip():
            raise ValueError("Start date must be a valid ISO 8601 date.")

        try:
            parsed_start = datetime.fromisoformat(
                start_date.strip().replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise ValueError(
                "Invalid start date. Use ISO 8601 format."
            ) from exc

    if end_date is not None:
        if not isinstance(end_date, str) or not end_date.strip():
            raise ValueError("End date must be a valid ISO 8601 date.")

        try:
            parsed_end = datetime.fromisoformat(
                end_date.strip().replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise ValueError(
                "Invalid end date. Use ISO 8601 format."
            ) from exc

    if parsed_start is not None and parsed_end is not None:

        # Prevent comparisons between timezone-aware and naive dates.
        if (
            (parsed_start.tzinfo is None)
            != (parsed_end.tzinfo is None)
        ):
            raise ValueError(
                "Start date and end date must use compatible timezones."
            )

        if parsed_start > parsed_end:
            raise ValueError(
                "Start date must be before or equal to end date."
            )


def validate_filters(
    metric_type: str | None,
    start_date: str | None,
    end_date: str | None,
) -> str | None:
    """Validate metric and date filters."""

    metric_type = validate_metric_type(metric_type)
    validate_date_range(start_date, end_date)

    return metric_type


# --------------------------------------------------
# REGISTER HEALTH RECORD TOOLS
# --------------------------------------------------

def register_record_tools(mcp):
    """Register health-record tools with the M-Pilot MCP server."""

    # --------------------------------------------------
    # 1. GET LATEST HEALTH RECORDS
    # --------------------------------------------------

    @mcp.tool()
    async def get_latest_health_records(
        metric_type: str | None = None,
        limit: int = 10,
    ) -> dict:
        """
        Retrieve the latest health records of the authenticated user.

        Optionally filter by metric type and limit the number of records.
        """

        access_token = get_access_token()

        if access_token is None or not access_token.token:
            raise ToolError("Authentication required.")

        # Validate inputs
        metric_type = validate_metric_type(metric_type)
        validate_integer(limit, "Limit", 1, 50)

        params = {
            "limit": limit,
        }

        if metric_type:
            params["metric_type"] = metric_type

        try:
            records = await backend.get(
                endpoint="/api/v1/health-records/",
                firebase_id_token=access_token.token,
                params=params,
            )

            if not isinstance(records, list):
                raise ToolError(
                    "Unexpected response received from the backend."
                )

            safe_records = []

            for record in records:

                if not isinstance(record, dict):
                    raise ToolError(
                        "Invalid health record received from the backend."
                    )

                safe_records.append({
                    "id": record.get("id"),
                    "provider_name": record.get("provider_name"),
                    "metric_type": record.get("metric_type"),
                    "value": record.get("value"),
                    "unit": record.get("unit"),
                    "recorded_at": record.get("recorded_at"),
                })

            return {
                "count": len(safe_records),
                "records": safe_records,
            }

        except httpx.HTTPStatusError as exc:

            if exc.response.status_code == 401:
                raise ToolError(
                    "Authentication failed."
                ) from exc

            if exc.response.status_code == 403:
                raise ToolError(
                    "Access to health records is forbidden."
                ) from exc

            if exc.response.status_code == 404:
                raise ToolError(
                    "Authenticated user was not found."
                ) from exc

            raise ToolError(
                "Unable to retrieve health records from the backend."
            ) from exc

        except httpx.RequestError as exc:
            raise ToolError(
                "Unable to connect to the M-Pilot backend."
            ) from exc

    # --------------------------------------------------
    # 2. GET LATEST READING FOR EACH HEALTH METRIC
    # --------------------------------------------------

    @mcp.tool()
    async def get_health_metrics() -> dict:
        """
        Retrieve the latest available reading for each health metric
        belonging to the authenticated user.
        """

        access_token = get_access_token()

        if access_token is None or not access_token.token:
            raise ToolError("Authentication required.")

        try:
            metrics = await backend.get(
                endpoint="/api/v1/health-records/metrics/latest",
                firebase_id_token=access_token.token,
            )

            if not isinstance(metrics, list):
                raise ToolError(
                    "Unexpected response received from the backend."
                )

            safe_metrics = []

            for metric in metrics:

                if not isinstance(metric, dict):
                    raise ToolError(
                        "Invalid health metric received from the backend."
                    )

                safe_metrics.append({
                    "id": metric.get("id"),
                    "provider_name": metric.get("provider_name"),
                    "metric_type": metric.get("metric_type"),
                    "value": metric.get("value"),
                    "unit": metric.get("unit"),
                    "recorded_at": metric.get("recorded_at"),
                })

            return {
                "count": len(safe_metrics),
                "metrics": safe_metrics,
            }

        except httpx.HTTPStatusError as exc:

            if exc.response.status_code == 401:
                raise ToolError(
                    "Authentication failed."
                ) from exc

            if exc.response.status_code == 403:
                raise ToolError(
                    "Access to health metrics is forbidden."
                ) from exc

            if exc.response.status_code == 404:
                raise ToolError(
                    "Authenticated user was not found."
                ) from exc

            raise ToolError(
                "Unable to retrieve health metrics from the backend."
            ) from exc

        except httpx.RequestError as exc:
            raise ToolError(
                "Unable to connect to the M-Pilot backend."
            ) from exc

    # --------------------------------------------------
    # 3. GET HEALTH HISTORY
    # --------------------------------------------------

    @mcp.tool()
    async def get_health_history(
        metric_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """
        Retrieve historical health records of the authenticated user.

        Optionally filter records by metric type and date range.

        Dates should use ISO 8601 format.
        Example: 2026-11-16T00:00:00Z
        """

        access_token = get_access_token()

        if access_token is None or not access_token.token:
            raise ToolError("Authentication required.")

        # Validate filters
        metric_type = validate_filters(
            metric_type,
            start_date,
            end_date,
        )

        # Validate pagination
        validate_integer(limit, "Limit", 1, 500)
        validate_integer(offset, "Offset", 0)

        params = {
            "limit": limit,
            "offset": offset,
        }

        if metric_type:
            params["metric_type"] = metric_type

        if start_date:
            params["start_date"] = start_date.strip()

        if end_date:
            params["end_date"] = end_date.strip()

        try:
            records = await backend.get(
                endpoint="/api/v1/health-records/",
                firebase_id_token=access_token.token,
                params=params,
            )

            if not isinstance(records, list):
                raise ToolError(
                    "Unexpected response received from the backend."
                )

            safe_records = []

            for record in records:

                if not isinstance(record, dict):
                    raise ToolError(
                        "Invalid health record received from the backend."
                    )

                safe_records.append({
                    "id": record.get("id"),
                    "provider_name": record.get("provider_name"),
                    "metric_type": record.get("metric_type"),
                    "value": record.get("value"),
                    "unit": record.get("unit"),
                    "recorded_at": record.get("recorded_at"),
                })

            return {
                "count": len(safe_records),
                "metric_type": metric_type,
                "start_date": start_date,
                "end_date": end_date,
                "records": safe_records,
            }

        except httpx.HTTPStatusError as exc:

            if exc.response.status_code == 401:
                raise ToolError(
                    "Authentication failed."
                ) from exc

            if exc.response.status_code == 403:
                raise ToolError(
                    "Access to health history is forbidden."
                ) from exc

            if exc.response.status_code == 404:
                raise ToolError(
                    "Authenticated user was not found."
                ) from exc

            if exc.response.status_code == 422:
                raise ToolError(
                    "Invalid health history filters or date range."
                ) from exc

            raise ToolError(
                "Unable to retrieve health history from the backend."
            ) from exc

        except httpx.RequestError as exc:
            raise ToolError(
                "Unable to connect to the M-Pilot backend."
            ) from exc

    # --------------------------------------------------
    # 4. GET HEALTH SUMMARY
    # --------------------------------------------------

    @mcp.tool()
    async def get_health_summary(
        metric_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """
        Get aggregated health statistics for the authenticated user.

        Supports optional metric and date filters.

        Returns latest, average, minimum, maximum and record count
        for each metric.
        """

        access_token = get_access_token()

        if access_token is None or not access_token.token:
            raise ToolError("Authentication required.")

        # Validate filters
        metric_type = validate_filters(
            metric_type,
            start_date,
            end_date,
        )

        params = {}

        if metric_type:
            params["metric_type"] = metric_type

        if start_date:
            params["start_date"] = start_date.strip()

        if end_date:
            params["end_date"] = end_date.strip()

        try:
            response = await backend.get(
                endpoint="/api/v1/health-records/summary",
                firebase_id_token=access_token.token,
                params=params,
            )

            if not isinstance(response, dict):
                raise ToolError(
                    "Invalid health summary response from backend."
                )

            metrics = response.get("metrics", [])

            if not isinstance(metrics, list):
                raise ToolError(
                    "Invalid metrics data returned by backend."
                )

            safe_metrics = []

            for item in metrics:

                if not isinstance(item, dict):
                    raise ToolError(
                        "Invalid health summary metric received."
                    )

                safe_metrics.append({
                    "metric_type": item.get("metric_type"),
                    "unit": item.get("unit"),
                    "latest": item.get("latest"),
                    "latest_recorded_at": item.get(
                        "latest_recorded_at"
                    ),
                    "average": item.get("average"),
                    "minimum": item.get("minimum"),
                    "maximum": item.get("maximum"),
                    "count": item.get("count"),
                })

            return {
                "count": len(safe_metrics),
                "metric_type": response.get("metric_type"),
                "start_date": response.get("start_date"),
                "end_date": response.get("end_date"),
                "metrics": safe_metrics,
            }

        except httpx.HTTPStatusError as exc:

            if exc.response.status_code == 401:
                raise ToolError(
                    "Authentication failed."
                ) from exc

            if exc.response.status_code == 403:
                raise ToolError(
                    "Access to health summary is forbidden."
                ) from exc

            if exc.response.status_code == 404:
                raise ToolError(
                    "Authenticated user was not found."
                ) from exc

            if exc.response.status_code == 422:
                logger.warning(
                    "Backend validation failed while retrieving "
                    "health summary."
                )

                raise ToolError(
                    "Invalid health summary filters or date range."
                ) from exc

            raise ToolError(
                "Unable to retrieve health summary from the backend."
            ) from exc

        except httpx.RequestError as exc:
            raise ToolError(
                "Unable to connect to the M-Pilot backend."
            ) from exc

        except ToolError:
            # Preserve anticipated, safe tool errors.
            raise

        except Exception as exc:
            logger.exception(
                "Unexpected error occurred in get_health_summary."
            )

            raise ToolError(
                "An unexpected error occurred while retrieving "
                "health summary."
            ) from exc
