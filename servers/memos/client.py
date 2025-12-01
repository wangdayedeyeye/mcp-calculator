import os
import json
import time
from typing import Optional, Dict, Any
import requests


def _request_json(method: str, url: str, token: Optional[str] = None, body: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, timeout: int = 15, retries: int = 2, backoff: float = 0.6):
    session = requests.Session()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    attempt = 0
    last_err = None
    while attempt <= retries:
        try:
            resp = session.request(
                method=method,
                url=url,
                headers=headers,
                json=body,
                params=params,
                timeout=timeout,
                verify=False,
            )
            text = resp.text
            try:
                parsed = resp.json()
            except ValueError:
                parsed = {"raw": text}
            if 200 <= resp.status_code < 300:
                return {"ok": True, "status": resp.status_code, "request": body, "response": parsed}
            last_err = {"ok": False, "status": resp.status_code, "request": body, "error": parsed}
            if 500 <= resp.status_code < 600 and attempt < retries:
                time.sleep(backoff * (attempt + 1))
                attempt += 1
                continue
            return last_err
        except requests.RequestException as e:
            last_err = {"ok": False, "status": None, "request": body, "error": str(e)}
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
                attempt += 1
                continue
            return last_err


def _get_base_and_token(api_url: Optional[str], token: Optional[str]):
    base = api_url or os.getenv("MEMOS_API_URL") or os.getenv("API_URL")
    tok = token or os.getenv("MEMOS_API_TOKEN") or os.getenv("API_TOKEN")
    if not base:
        return None, tok
    return base.rstrip("/"), tok


def add_memo(payload: Dict[str, Any], api_url: Optional[str] = None, token: Optional[str] = None):
    base, tok = _get_base_and_token(api_url, token)
    if not base:
        return {"ok": False, "error": "missing MEMOS_API_URL/API_URL"}
    url = f"{base}/api/v1/memo"
    return _request_json("POST", url, tok, payload)


def get_memos(params: Optional[Dict[str, Any]] = None, api_url: Optional[str] = None, token: Optional[str] = None):
    base, tok = _get_base_and_token(api_url, token)
    if not base:
        return {"ok": False, "error": "missing MEMOS_API_URL/API_URL"}
    url = f"{base}/api/v1/memos"
    return _request_json("GET", url, tok, None, params)


def delete_memo(memo_id: str | int, api_url: Optional[str] = None, token: Optional[str] = None):
    base, tok = _get_base_and_token(api_url, token)
    if not base:
        return {"ok": False, "error": "missing MEMOS_API_URL/API_URL"}
    url = f"{base}/api/v1/memo/{memo_id}"
    return _request_json("DELETE", url, tok, None)


def update_memo(memo_id: str | int, patch: Dict[str, Any], api_url: Optional[str] = None, token: Optional[str] = None):
    base, tok = _get_base_and_token(api_url, token)
    if not base:
        return {"ok": False, "error": "missing MEMOS_API_URL/API_URL"}
    url = f"{base}/api/v1/memo/{memo_id}"
    return _request_json("PATCH", url, tok, patch)

