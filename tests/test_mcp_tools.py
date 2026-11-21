
import getpass
import httpx


MCP_URL = "http://127.0.0.1:8001/mcp"


def main():
    token = getpass.getpass("Enter Firebase ID token (hidden): ")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": "2025-03-26",
    }

    with httpx.Client(timeout=20) as client:

        # 1. Initialize MCP session
        initialize_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "m-pilot-test-client",
                    "version": "1.0.0",
                },
            },
        }

        response = client.post(
            MCP_URL,
            headers=headers,
            json=initialize_payload,
        )

        print("Initialization status:", response.status_code)
        response.raise_for_status()

        session_id = response.headers.get("mcp-session-id")

        if not session_id:
            print("MCP session ID missing.")
            return

        headers["Mcp-Session-Id"] = session_id

        # Send initialized notification
        client.post(
            MCP_URL,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            },
        )

        # 2. Discover registered tools
        response = client.post(
            MCP_URL,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            },
        )

        print("\nTool discovery status:", response.status_code)
        print("Tool discovery response:")
        print(response.text)

        response.raise_for_status()

        # 3. Execute get_connected_providers
        tool_call_payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_connected_providers",
                "arguments": {},
            },
        }

        response = client.post(
            MCP_URL,
            headers=headers,
            json=tool_call_payload,
        )

        response.raise_for_status()

        print("\nTool execution status:", response.status_code)
        print("get_connected_providers response:")
        print(response.text)

        # 4. Execute get_latest_health_records
        tool_call_payload = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "get_latest_health_records",
                "arguments": {
                    "metric_type": "steps",
                    "limit": 5,
                },
            },
        }

        response = client.post(
            MCP_URL,
            headers=headers,
            json=tool_call_payload,
        )

        response.raise_for_status()

        print("\nHealth records execution status:", response.status_code)
        print("get_latest_health_records response:")
        print(response.text)

        # 5. Execute get_health_metrics
        tool_call_payload = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "get_health_metrics",
                "arguments": {},
            },
        }

        response = client.post(
            MCP_URL,
            headers=headers,
            json=tool_call_payload,
        )

        response.raise_for_status()

        print("\nHealth metrics execution status:", response.status_code)
        print("get_health_metrics response:")
        print(response.text)

        # 6. Execute get_health_history - First Page
        tool_call_payload = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "get_health_history",
                "arguments": {
                    "metric_type": "steps",
                    "start_date": "2026-11-01T00:00:00Z",
                    "end_date": "2026-11-14T23:59:59Z",
                    "limit": 10,
                    "offset": 0,
                },
            },
        }

        response = client.post(
            MCP_URL,
            headers=headers,
            json=tool_call_payload,
        )

        response.raise_for_status()

        print("\nHealth history execution status:", response.status_code)
        print("get_health_history response:")
        print(response.text)

        # 7. Execute get_health_history - Second Page
        second_page_payload = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "get_health_history",
                "arguments": {
                    "metric_type": "steps",
                    "start_date": "2026-11-01T00:00:00Z",
                    "end_date": "2026-11-14T23:59:59Z",
                    "limit": 10,
                    "offset": 10,
                },
            },
        }

        response = client.post(
            MCP_URL,
            headers=headers,
            json=second_page_payload,
        )

        response.raise_for_status()

        print("\nSecond page execution status:", response.status_code)
        print("get_health_history - Second Page:")
        print(response.text)

        # 8. Execute get_health_summary
        summary_payload = {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "get_health_summary",
                "arguments": {},
            },
        }

        response = client.post(
            MCP_URL,
            headers=headers,
            json=summary_payload,
        )

        response.raise_for_status()

        print("\nHealth Summary execution status:", response.status_code)
        print("get_health_summary response:")
        print(response.text)



        # 9. Execute sync_health_data - Synthetic Data
        sync_payload = {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {
                "name": "sync_health_data",
                "arguments": {
                    "provider_id": 4,
                },
            },
        }

        response = client.post(
            MCP_URL,
            headers=headers,
            json=sync_payload,
        )

        response.raise_for_status()

        print("\nHealth data synchronization status:", response.status_code)
        print("sync_health_data response:")
        print(response.text)


if __name__ == "__main__":
    main()
