"""
PoC test for CWE-918: SSRF via add_remote_skill DNS rebinding / private hostname bypass.

The validate_url() function only checks if the hostname is a literal private IP.
When a domain name resolves to a private IP, it passes validation, enabling SSRF.

This test patches socket.getaddrinfo to simulate a domain resolving to a private IP
and verifies the fix blocks it.
"""
import ipaddress
import socket
import sys
import pathlib
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))

from utils import validate_url


class TestValidateUrlSSRF(unittest.TestCase):
    """Test that validate_url blocks hostnames that resolve to private IPs."""

    def test_literal_private_ip_blocked(self):
        """Literal private IPs should be blocked (existing behavior)."""
        self.assertFalse(validate_url('https://10.0.0.1/secret'))
        self.assertFalse(validate_url('https://127.0.0.1/secret'))
        self.assertFalse(validate_url('https://192.168.1.1/secret'))

    def test_domain_resolving_to_private_ip_blocked(self):
        """A domain that resolves to a private IP must be blocked (THE FIX)."""
        fake_result = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('10.0.0.1', 443))]
        with patch('socket.getaddrinfo', return_value=fake_result):
            result = validate_url('https://evil.com/internal-data')
            self.assertFalse(result,
                "validate_url should reject domains resolving to private IPs")

    def test_domain_resolving_to_loopback_blocked(self):
        """A domain that resolves to 127.0.0.1 must be blocked."""
        fake_result = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 443))]
        with patch('socket.getaddrinfo', return_value=fake_result):
            result = validate_url('https://loopback.evil.com/secret')
            self.assertFalse(result,
                "validate_url should reject domains resolving to loopback")

    def test_domain_resolving_to_link_local_blocked(self):
        """A domain resolving to 169.254.x.x (link-local / cloud metadata) must be blocked."""
        fake_result = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('169.254.169.254', 443))]
        with patch('socket.getaddrinfo', return_value=fake_result):
            result = validate_url('https://metadata.evil.com/latest/meta-data/')
            self.assertFalse(result,
                "validate_url should reject domains resolving to link-local (cloud metadata)")

    def test_domain_resolving_to_ipv6_loopback_blocked(self):
        """A domain resolving to ::1 must be blocked."""
        fake_result = [(socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('::1', 443, 0, 0))]
        with patch('socket.getaddrinfo', return_value=fake_result):
            result = validate_url('https://ipv6loop.evil.com/secret')
            self.assertFalse(result,
                "validate_url should reject domains resolving to IPv6 loopback")

    def test_public_domain_allowed(self):
        """A domain resolving to a public IP should be allowed."""
        fake_result = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('151.101.1.67', 443))]
        with patch('socket.getaddrinfo', return_value=fake_result):
            result = validate_url('https://raw.githubusercontent.com/some/file')
            self.assertTrue(result,
                "validate_url should allow domains resolving to public IPs")

    def test_http_scheme_rejected(self):
        """HTTP scheme should be rejected."""
        self.assertFalse(validate_url('http://example.com'))

    def test_dns_resolution_failure_rejected(self):
        """If DNS resolution fails, the URL should be rejected."""
        with patch('socket.getaddrinfo', side_effect=socket.gaierror('DNS failed')):
            result = validate_url('https://nonexistent.invalid/path')
            self.assertFalse(result,
                "validate_url should reject URLs with unresolvable hostnames")


if __name__ == '__main__':
    unittest.main()
