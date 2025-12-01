from mcp.server.fastmcp import FastMCP
import os
import json
from urllib import request, error
import time
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("Watchlist Server", json_response=True)


def _post_json(api: str, tok: str, body: dict, timeout: int = 15, retries: int = 2, backoff: float = 0.6):
    data = json.dumps(body).encode("utf-8")
    attempt = 0
    last_err = None
    while attempt <= retries:
        req = request.Request(api, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {tok}")
        try:
            with request.urlopen(req, timeout=timeout) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                text = resp.read().decode(charset)
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    parsed = {"raw": text}
                return {"ok": True, "status": resp.status, "request": body, "response": parsed}
        except error.HTTPError as e:
            msg = e.read().decode("utf-8", errors="replace")
            last_err = {"ok": False, "status": e.code, "request": body, "error": msg}
            if 500 <= e.code < 600 and attempt < retries:
                time.sleep(backoff * (attempt + 1))
                attempt += 1
                continue
            return last_err
        except error.URLError as e:
            last_err = {"ok": False, "status": None, "request": body, "error": str(e.reason)}
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
                attempt += 1
                continue
            return last_err

@mcp.tool()
def update_symbols(coin: str, platform: str | None = None, operation: str = "append", api_url: str | None = None, token: str | None = None):
    """Update symbols on external platform watchlist

    platform: "aicoin" or "tradingview"
    coin: base symbol, e.g. "sol" or "doge"
    operation: one of [list, append, remove, replace]
    api_url/token: override env vars API_URL/API_TOKEN
    """
    plat = (platform or "aicoin").lower()
    if plat not in {"aicoin", "tradingview"}:
        return {"ok": False, "error": "unsupported platform", "platform": platform}

    api = api_url or os.getenv("API_URL", "https://trade-my-target-xtzihsmczn.ap-southeast-1.fcapp.run")
    tok = token or os.getenv("API_TOKEN", "token-ahgi2018haad6e2bafeia52d9fj2")

    if plat == "aicoin":
        base = coin.lower()
        symbol = f"{base}swapusdt:binance;tp"
        name = "46879974"
    else:
        base = coin.upper()
        symbol = f"BINANCE:{base}USDT"
        name = "d57802"

    body = {
        "symbols": [symbol],
        "operation": operation,
        "platform": plat,
        "name": name,
    }
    return _post_json(api, tok, body)

@mcp.tool()
def list_symbols(platform: str | None = None, api_url: str | None = None, token: str | None = None):
    plat = (platform or "aicoin").lower()
    if plat not in {"aicoin", "tradingview"}:
        return {"ok": False, "error": "unsupported platform", "platform": platform}
    api = api_url or os.getenv("API_URL", "https://trade-my-target-xtzihsmczn.ap-southeast-1.fcapp.run")
    tok = token or os.getenv("API_TOKEN", "token-ahgi2018haad6e2bafeia52d9fj2")
    name = "46879974" if plat == "aicoin" else "d57802"
    body = {
        "symbols": [],
        "operation": "list",
        "platform": plat,
        "name": name,
    }
    return _post_json(api, tok, body)

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    return f"Write a {style} greeting for someone named {name}."

if __name__ == "__main__":
    mcp.run(transport="stdio")
