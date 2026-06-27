"""Smoke test for /api/chat/stream SSE endpoint."""
import asyncio
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


async def run_stream_smoke_test() -> None:
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream(
            "POST",
            "http://127.0.0.1:8000/api/chat/stream",
            json={"customer_id": "shop_001", "message": "我的快递什么时候发货？"},
        ) as resp:
            print(f"Status: {resp.status_code}")
            resp.raise_for_status()
            buffer = ""
            saw_final = False
            async for chunk in resp.aiter_text():
                buffer += chunk.replace("\r\n", "\n")
                while "\n\n" in buffer:
                    event_str, buffer = buffer.split("\n\n", 1)
                    for line in event_str.split("\n"):
                        if not line.startswith("data:"):
                            continue
                        data = json.loads(line[5:].strip())
                        event_type = data.get("type", "?")
                        if event_type == "final":
                            saw_final = True
                            response = data.get("response", {})
                            answer = response.get("answer", "")[:120]
                            action = response.get("action", "")
                            print(f"[final] action={action} answer={answer}")
                            if action != "auto_reply":
                                raise SystemExit(f"Expected auto_reply, got {action}")
                        else:
                            step = data.get("step", "")
                            display = data.get("display", "")
                            summary = (data.get("output") or {}).get("summary", "")
                            print(f"[{event_type}] {step} ({display}) -> {summary}")
            if not saw_final:
                raise SystemExit("Stream ended without final event")
            print("OK: Stream completed successfully")


if __name__ == "__main__":
    asyncio.run(run_stream_smoke_test())
