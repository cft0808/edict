from __future__ import annotations

import ipaddress
import socket
from typing import Protocol, ClassVar
from abc import abstractmethod


class NotificationChannel(Protocol):
    name: ClassVar[str]
    label: ClassVar[str]
    icon: ClassVar[str]
    placeholder: ClassVar[str]
    allowed_domains: ClassVar[tuple[str, ...]]

    @classmethod
    @abstractmethod
    def validate_webhook(cls, webhook: str) -> bool:
        ...

    @classmethod
    @abstractmethod
    def send(cls, webhook: str, title: str, content: str, url: str | None = None) -> bool:
        ...

    @classmethod
    def _validate_url_scheme(cls, url: str) -> bool:
        return url.startswith('https://')

    @classmethod
    def _extract_domain(cls, url: str) -> str:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return ''

    @classmethod
    def _is_public_host(cls, url: str) -> bool:
        """Return True only if the URL host resolves exclusively to public IPs.

        Blocks SSRF vectors: loopback, link-local (incl. 169.254.169.254 cloud
        metadata), private (RFC1918), multicast, reserved and unspecified
        addresses, plus IPv6 equivalents.
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
        except Exception:
            return False
        host = parsed.hostname
        if not host:
            return False
        # Reject hosts that are already raw IP literals pointing at unsafe ranges
        # plus any DNS name that resolves to one. We must check *all* resolved
        # addresses, not just the first, to avoid bypass via multi-A records.
        try:
            infos = socket.getaddrinfo(host, None)
        except socket.gaierror:
            return False
        if not infos:
            return False
        for info in infos:
            sockaddr = info[4]
            ip_str = sockaddr[0]
            try:
                ip = ipaddress.ip_address(ip_str)
            except ValueError:
                return False
            if (ip.is_private or ip.is_loopback or ip.is_link_local
                    or ip.is_multicast or ip.is_reserved
                    or ip.is_unspecified):
                return False
            # Additionally block IPv4-mapped/compatible IPv6 to private space
            if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
                mapped = ip.ipv4_mapped
                if (mapped.is_private or mapped.is_loopback or mapped.is_link_local
                        or mapped.is_multicast or mapped.is_reserved
                        or mapped.is_unspecified):
                    return False
        return True
