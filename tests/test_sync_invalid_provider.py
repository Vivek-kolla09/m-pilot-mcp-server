
import getpass
import json
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

        # Initialize MCP session
        initialize_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "sync-reliability-test",
                    "version": "1.0.0",
                },
            },
        }

        response = client.post(
            MCP_URL,
            headers=headers,
            json=initialize_payload,
        )
        response.raise_for_status()

        session_id = response.headers.get("mcp-session-id")

        if not session_id:
            print("FAIL: MCP session creation failed.")
            return

        headers["Mcp-Session-Id"] = session_id

        # Complete initialization
        client.post(
            MCP_URL,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            },
        )

        # Call synchronization with a nonexistent provider ID
        response = client.post(
            MCP_URL,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "sync_health_data",
                    "arguments": {
                        "provider_id": 7,
                    },
                },
            },
        )

        print("HTTP status:", response.status_code)

        if response.status_code != 200:
            print("FAIL: MCP request failed.")
            print(response.text[:500])
            return

        # Extract the JSON-RPC response from SSE
        for line in response.text.splitlines():
            if line.startswith("data: "):
                result = json.loads(line[6:])

                if "error" in result:
                    print("MCP protocol error:", result["error"])
                    return

                tool_result = result.get("result", {})

                if tool_result.get("isError"):
                    print("PASS: Synchronization returned a controlled tool error.")

                    for item in tool_result.get("content", []):
                        if item.get("type") == "text":
                            print("Error message:", item["text"])

                    return

                print("FAIL: Nonexistent provider was accepted.")
                print("Unexpected result:", tool_result)
                return

        print("FAIL: No MCP response found.")


if __name__ == "__main__":
    main()
