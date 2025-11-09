import json
import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# The URL of your real bridge (the current Render service)
REAL_BRIDGE = os.getenv("REAL_BRIDGE", "https://lyra-mcp-bridge.onrender.com/sse")

app = FastAPI(title="Lyra MCP Compatibility Proxy")

# --------------- helpers ---------------

def ok(req_id, result):
    return {"jsonrpc": "2.0", "id": req_id, "result": result}

# --------------- endpoints ---------------

@app.post("/sse")
async def proxy_rpc(req: Request):
    """Emulate old handshake; forward everything else."""
    payload = await req.json()
    method  = payload.get("method")
    req_id  = payload.get("id")

    print(f"Proxy got: {method}")  # <-- add this line

    # --- 1️⃣  old-style handshake ---
    if method == "initialize":
        print("Proxy: replying to initialize with 2023-10-10")
        return JSONResponse(ok(req_id, {
            "protocolVersion": "2023-10-10",
            "serverInfo": {"name": "Lyra MCP Bridge (compat)", "version": "1.0.0"},
            "capabilities": {"tools": {"list": True, "call": True}}
        }))

    # --- 2️⃣  everything else -> forward to the real bridge ---
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post(REAL_BRIDGE, json=payload)
            return JSONResponse(r.json())
        except Exception as e:
            return JSONResponse(
                {"jsonrpc": "2.0", "id": req_id,
                 "error": {"code": -32000, "message": f"Proxy error: {e}"}},
                status_code=500,
            )

# optional health endpoint
@app.get("/")
def root():
    return {"ok": True, "proxy_for": REAL_BRIDGE}
