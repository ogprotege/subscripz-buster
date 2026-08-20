import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _rpc(payload: dict) -> str:
    return json.dumps(payload)


def test_mcp_lists_new_hunt_tools():
    sequence = "\n".join(
        [
            _rpc(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "pytest", "version": "0"},
                    },
                }
            ),
            _rpc({"jsonrpc": "2.0", "method": "notifications/initialized"}),
            _rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
        ]
    ) + "\n"

    result = subprocess.run(
        [sys.executable, "server.py"],
        input=sequence,
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    names = set()
    for line in result.stdout.splitlines():
        try:
            body = json.loads(line)
        except json.JSONDecodeError:
            continue
        tools = (body.get("result") or {}).get("tools") or []
        for tool in tools:
            names.add(tool.get("name"))
    assert "hunt_recurring_charges" in names
    assert "subscription_action_plan" in names
    assert "scan_all_subscriptions" in names
