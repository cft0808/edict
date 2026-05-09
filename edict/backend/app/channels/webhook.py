from __future__ import annotations

import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from typing import ClassVar

from .base import NotificationChannel


class WebhookChannel(NotificationChannel):
    name: ClassVar[str] = 'webhook'
    label: ClassVar[str] = '通用 Webhook'
    icon: ClassVar[str] = '🔗'
    placeholder: ClassVar[str] = 'https://your-server.com/webhook/...'
    allowed_domains: ClassVar[tuple[str, ...]] = ()

    @classmethod
    def validate_webhook(cls, webhook: str) -> bool:
        # Require HTTPS and that the destination resolves to a public IP only.
        # Without this SSRF guard, the generic webhook channel would happily
        # POST to internal services (e.g. http(s)://169.254.169.254/, RFC1918
        # hosts, localhost) when an operator pastes such a URL into the
        # notification config.
        if not cls._validate_url_scheme(webhook):
            return False
        return cls._is_public_host(webhook)

    @classmethod
    def send(cls, webhook: str, title: str, content: str, url: str | None = None) -> bool:
        # Re-validate at send time as a defence-in-depth measure against
        # config tampering / DNS rebinding between validation and send.
        if not cls.validate_webhook(webhook):
            return False
        payload = json.dumps({
            'title': title,
            'content': content,
            'url': url,
            'source': 'edict'
        }).encode()
        try:
            req = Request(webhook, data=payload, headers={'Content-Type': 'application/json'})
            resp = urlopen(req, timeout=10)
            return 200 <= resp.status < 300
        except (URLError, HTTPError, Exception):
            return False
