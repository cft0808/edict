from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
import urllib.parse
from typing import ClassVar
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .base import NotificationChannel

log = logging.getLogger('channel.dingtalk')

SECRET_PARAM = 'secret'


class DingtalkChannel(NotificationChannel):
    """钉钉自定义机器人渠道。

    加签模式：把 secret 作为查询参数附加在 webhook 上，
        https://oapi.dingtalk.com/robot/send?access_token=XXX&secret=SECXXX
    发送时自动剥离 secret、生成 timestamp+sign（HMAC-SHA256）后请求。
    不填 secret 时按「关键词 / IP 白名单」模式直接发送。
    """

    name: ClassVar[str] = 'dingtalk'
    label: ClassVar[str] = '钉钉 DingTalk'
    icon: ClassVar[str] = '📌'
    placeholder: ClassVar[str] = (
        'https://oapi.dingtalk.com/robot/send?access_token=...&secret=SEC...'
    )
    allowed_domains: ClassVar[tuple[str, ...]] = ('oapi.dingtalk.com',)

    @classmethod
    def validate_webhook(cls, webhook: str) -> bool:
        if not cls._validate_url_scheme(webhook):
            return False
        domain = cls._extract_domain(webhook)
        return any(domain.endswith(d) for d in cls.allowed_domains)

    # ---------- 内部工具 ----------

    @staticmethod
    def _split_secret(webhook: str) -> tuple[str, str]:
        """返回 (去掉 secret 的 URL, secret)。"""
        parsed = urllib.parse.urlsplit(webhook)
        pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        secret = ''
        kept: list[tuple[str, str]] = []
        for k, v in pairs:
            if k == SECRET_PARAM:
                secret = (v or '').strip()
            else:
                kept.append((k, v))
        clean = urllib.parse.urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path,
             urllib.parse.urlencode(kept), parsed.fragment)
        )
        return clean, secret

    @staticmethod
    def _sign(secret: str, timestamp: str) -> str:
        string_to_sign = f'{timestamp}\n{secret}'
        digest = hmac.new(
            secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256,
        ).digest()
        return urllib.parse.quote_plus(base64.b64encode(digest).decode('utf-8'))

    @classmethod
    def _build_payload(cls, title: str, content: str, url: str | None) -> dict:
        text = f'### {title}\n{content}'
        if url:
            text += f'\n\n[查看详情]({url})'
        return {'msgtype': 'markdown', 'markdown': {'title': title, 'text': text}}

    @classmethod
    def send(cls, webhook: str, title: str, content: str, url: str | None = None) -> bool:
        clean_url, secret = cls._split_secret(webhook)
        if secret:
            ts = str(round(time.time() * 1000))
            sep = '&' if '?' in clean_url else '?'
            clean_url = f'{clean_url}{sep}timestamp={ts}&sign={cls._sign(secret, ts)}'

        payload = json.dumps(
            cls._build_payload(title, content, url), ensure_ascii=False
        ).encode('utf-8')
        try:
            req = Request(clean_url, data=payload,
                          headers={'Content-Type': 'application/json'})
            resp = urlopen(req, timeout=10)
            body = resp.read().decode('utf-8', errors='replace')
        except (URLError, HTTPError) as e:
            log.warning(f'钉钉推送请求失败: {e}')
            return False
        except Exception as e:
            log.warning(f'钉钉推送异常: {e}')
            return False

        if not (200 <= resp.status < 300):
            log.warning(f'钉钉推送 HTTP {resp.status}: {body[:200]}')
            return False
        # 钉钉出错时仍返回 HTTP 200，必须查 errcode，否则会假报成功
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            log.warning(f'钉钉返回非 JSON: {body[:200]}')
            return False
        if data.get('errcode') != 0:
            log.warning(
                f"钉钉推送被拒: errcode={data.get('errcode')} "
                f"errmsg={data.get('errmsg')}"
            )
            return False
        return True
