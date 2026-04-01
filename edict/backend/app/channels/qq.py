from __future__ import annotations

import json
import time
import threading
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import ClassVar

from .base import NotificationChannel

# Token cache (isolated by appid:secret)
_token_cache: dict[str, dict] = {}
_token_lock = threading.Lock()


def _get_access_token(appid: str, secret: str) -> str | None:
    """Get access_token with local cache (7200s TTL, refresh 300s early)."""
    cache_key = f"{appid}:{secret}"
    with _token_lock:
        cached = _token_cache.get(cache_key)
        if cached and cached["expires_at"] > time.time() + 300:
            return cached["token"]

    try:
        token_url = "https://bots.qq.com/app/getAppAccessToken"
        payload = json.dumps({
            "appId": appid,
            "clientSecret": secret,
        }).encode()
        req = Request(token_url, data=payload, headers={"Content-Type": "application/json"})
        resp = urlopen(req, timeout=10)
        data = json.loads(resp.read())
        token = data.get("access_token")
        expires_in = int(data.get("expires_in", 7200))
        if token:
            with _token_lock:
                _token_cache[cache_key] = {
                    "token": token,
                    "expires_at": time.time() + expires_in,
                }
        return token
    except Exception:
        return None


def _resolve_api_url_and_token(base_url: str) -> tuple[str, str]:
    """Resolve final API URL and access token from webhook URL params.

    Supports two modes:
      - appid + secret: auto-fetch token from QQ API
      - access_token: use directly
    """
    parsed = urlparse(base_url)
    params = parse_qs(parsed.query)

    appid = params.get("appid", [None])[0]
    secret = params.get("secret", [None])[0]
    at_param = params.get("access_token", [None])[0]

    if appid and secret:
        token = _get_access_token(appid, secret)
    elif at_param:
        token = at_param
    else:
        token = None

    # Strip auth params from URL
    clean_params = {
        k: v[0] for k, v in params.items()
        if k not in ("appid", "secret", "access_token")
    }
    clean_query = urlencode(clean_params) if clean_params else ""
    api_url = urlunparse(parsed._replace(query=clean_query))

    return api_url, token or ""


class QQChannel(NotificationChannel):
    name: ClassVar[str] = "qq"
    label: ClassVar[str] = "QQ 机器人"
    icon: ClassVar[str] = "🐧"
    placeholder: ClassVar[str] = (
        "https://api.sgroup.qq.com/v2/users/{openid}/messages?appid=XXX&secret=YYY"
    )
    allowed_domains: ClassVar[tuple[str, ...]] = (
        "api.sgroup.qq.com",
    )

    @classmethod
    def validate_webhook(cls, webhook: str) -> bool:
        if not cls._validate_url_scheme(webhook):
            return False
        domain = cls._extract_domain(webhook)
        return any(domain.endswith(d) for d in cls.allowed_domains)

    @classmethod
    def send(cls, webhook: str, title: str, content: str, url: str | None = None) -> bool:
        api_url, access_token = _resolve_api_url_and_token(webhook)
        if not access_token:
            return False

        # Compose message text
        text = f"【{title}】\n{content}"
        if url:
            text += f"\n🔗 {url}"

        payload = json.dumps({
            "content": text,
            "msg_type": 0,
        }).encode()

        try:
            req = Request(
                api_url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"QQBot {access_token}",
                },
                method="POST",
            )
            resp = urlopen(req, timeout=10)
            return resp.status == 200
        except (URLError, HTTPError, Exception):
            return False
