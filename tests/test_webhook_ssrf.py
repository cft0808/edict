"""PoC test for CWE-918 SSRF in WebhookChannel."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "edict" / "backend"))

from app.channels.webhook import WebhookChannel  # noqa: E402


def _patch_dns(host_to_ip):
    def fake_getaddrinfo(host, *_a, **_k):
        ip = host_to_ip.get(host)
        if ip is None:
            import socket
            raise socket.gaierror('mock')
        return [(2, 1, 6, '', (ip, 0))]
    return mock.patch('app.channels.base.socket.getaddrinfo',
                      side_effect=fake_getaddrinfo)


def test_blocks_loopback():
    with _patch_dns({'127.0.0.1': '127.0.0.1', 'localhost': '127.0.0.1'}):
        assert WebhookChannel.validate_webhook('https://127.0.0.1/x') is False
        assert WebhookChannel.validate_webhook('https://localhost/x') is False


def test_blocks_cloud_metadata():
    with _patch_dns({'169.254.169.254': '169.254.169.254',
                     'metadata.google.internal': '169.254.169.254'}):
        assert WebhookChannel.validate_webhook('https://169.254.169.254/latest/meta-data/') is False
        assert WebhookChannel.validate_webhook('https://metadata.google.internal/') is False


def test_blocks_rfc1918():
    with _patch_dns({'10.0.0.5': '10.0.0.5',
                     '192.168.1.1': '192.168.1.1',
                     '172.16.0.1': '172.16.0.1'}):
        assert WebhookChannel.validate_webhook('https://10.0.0.5/x') is False
        assert WebhookChannel.validate_webhook('https://192.168.1.1/x') is False
        assert WebhookChannel.validate_webhook('https://172.16.0.1/x') is False


def test_blocks_http_scheme():
    assert WebhookChannel.validate_webhook('http://example.com/x') is False


def test_allows_public_host():
    with _patch_dns({'example.com': '93.184.216.34'}):
        assert WebhookChannel.validate_webhook('https://example.com/hook') is True


def test_send_refuses_unsafe_url():
    with _patch_dns({'127.0.0.1': '127.0.0.1'}):
        with mock.patch('app.channels.webhook.urlopen') as uo:
            ok = WebhookChannel.send('https://127.0.0.1/x', 't', 'c')
            assert ok is False
            uo.assert_not_called()


if __name__ == '__main__':
    test_blocks_loopback()
    test_blocks_cloud_metadata()
    test_blocks_rfc1918()
    test_blocks_http_scheme()
    test_allows_public_host()
    test_send_refuses_unsafe_url()
    print('OK')
