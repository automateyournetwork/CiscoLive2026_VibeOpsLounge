#!/usr/bin/env python3
import json
import time
import subprocess
import threading
import sys

# ================================================================
# 1) Launch the MCP server subprocess
# ================================================================
SERVER_CMD = ["python3", "server.py"]

mcp_proc = subprocess.Popen(
    SERVER_CMD,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,  # line buffered
)

def _stderr_logger(proc):
    for line in proc.stderr:
        print("[MCP STDERR]", line.rstrip(), file=sys.stderr)

threading.Thread(target=_stderr_logger, args=(mcp_proc,), daemon=True).start()

# ================================================================
# 2) JSON-RPC Helpers
# ================================================================
_req_id = 0
def _next_id():
    global _req_id
    _req_id += 1
    return _req_id

def send(obj: dict):
    mcp_proc.stdin.write(json.dumps(obj) + "\n")
    mcp_proc.stdin.flush()


# ------------------------------------------------------------
# FINAL, CORRECT recv():
# - reads single-line JSON (your actual server behavior)
# - ignores empty lines
# - handles JSON parse errors gracefully
# ------------------------------------------------------------
def recv(timeout=10):
    start = time.time()

    while time.time() - start < timeout:
        line = mcp_proc.stdout.readline()

        if not line:
            time.sleep(0.01)
            continue

        line = line.strip()
        if not line:
            continue

        # Debug (optional): print("[RAW]", repr(line))

        try:
            return json.loads(line)
        except json.JSONDecodeError:
            # Your server never emits multi-line JSON or content-length,
            # so we do not buffer. Just continue until valid JSON arrives.
            continue

    raise TimeoutError("Timed out waiting for MCP JSON-RPC message")


# ================================================================
# 3) MCP Lifecycle + Tool Calls
# ================================================================
def initialize():
    rid = _next_id()

    send({
        "jsonrpc": "2.0",
        "id": rid,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "multiply-demo-client", "version": "1.0"},
        },
    })

    while True:
        resp = recv()
        if resp.get("id") == rid:
            break

    # Tell server "we are ready"
    send({
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    })


def tools_list():
    rid = _next_id()
    send({
        "jsonrpc": "2.0",
        "id": rid,
        "method": "tools/list",
    })

    while True:
        resp = recv()
        if resp.get("id") == rid:
            return resp["result"]["tools"]


def tools_call(name: str, arguments: dict):
    rid = _next_id()

    send({
        "jsonrpc": "2.0",
        "id": rid,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })

    while True:
        resp = recv()

        # skip notifications (no ID)
        if "id" not in resp:
            continue

        if resp["id"] != rid:
            continue

        # SUCCESSFUL TOOL EXECUTION
        result = resp.get("result", {})

        # FastMCP uses content blocks for tool output
        content = result.get("content")
        if content and isinstance(content, list):
            block = content[0]
            if block.get("type") == "text":
                text_block = block["text"]
                # server returns your dict as JSON *string* → parse it
                return json.loads(text_block)

        # fallback (should never happen with FastMCP)
        return result


# ================================================================
# 4) Tiny interactive REPL
# ================================================================
def main():
    try:
        print("[CLIENT] Initializing MCP…")
        initialize()

        tools = tools_list()
        names = [t["name"] for t in tools]
        print("[CLIENT] Tools available:", names)

        print("\nType two numbers separated by space (or 'exit'):")
        while True:
            raw = input("> ").strip()
            if raw in ("exit", "quit", ""):
                break

            try:
                a_str, b_str = raw.split()
                a = float(a_str)
                b = float(b_str)
            except Exception:
                print("Enter two numbers like: 3 7")
                continue

            result = tools_call("multiply", {"a": a, "b": b})
            print(result["summary"])

    finally:
        if mcp_proc:
            mcp_proc.terminate()
            try:
                mcp_proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                mcp_proc.kill()


if __name__ == "__main__":
    main()
