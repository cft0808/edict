#!/usr/bin/env python3
"""
三省六部 · 公共工具函数
避免 read_json / now_iso 等基础函数在多个脚本中重复定义
"""
import json, pathlib, datetime


def read_json(path, default=None):
    """安全读取 JSON 文件，失败返回 default"""
    try:
        return json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
    except Exception:
        return default if default is not None else {}


def now_iso():
    """返回 UTC ISO 8601 时间字符串（末尾 Z）"""
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')


def today_str(fmt='%Y%m%d'):
    """返回今天日期字符串，默认 YYYYMMDD"""
    return datetime.date.today().strftime(fmt)


def safe_name(s: str) -> bool:
    """检查名称是否只含安全字符（字母、数字、下划线、连字符、中文）"""
    import re
    return bool(re.match(r'^[a-zA-Z0-9_\-\u4e00-\u9fff]+$', s))


def _is_private_ip(ip_str: str) -> bool:
    """检查 IP 地址字符串是否为私有/回环/保留/链路本地地址"""
    import ipaddress
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local
    except ValueError:
        return False


def validate_url(url: str, allowed_schemes=('https',), allowed_domains=None) -> bool:
    """校验 URL 合法性，防 SSRF（含 DNS 解析检查）"""
    from urllib.parse import urlparse
    import socket
    try:
        parsed = urlparse(url)
        if parsed.scheme not in allowed_schemes:
            return False
        if allowed_domains and parsed.hostname not in allowed_domains:
            return False
        if not parsed.hostname:
            return False
        # 禁止内网地址（字面 IP）
        if _is_private_ip(parsed.hostname):
            return False
        # DNS 解析检查：解析 hostname 并检查所有返回的 IP 地址
        # 这能防御使用域名指向内网 IP 的 SSRF 攻击（DNS rebinding 等）
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        try:
            addrinfos = socket.getaddrinfo(parsed.hostname, port,
                                           socket.AF_UNSPEC, socket.SOCK_STREAM)
        except socket.gaierror:
            return False  # DNS 解析失败，拒绝
        if not addrinfos:
            return False
        for family, socktype, proto, canonname, sockaddr in addrinfos:
            ip_str = sockaddr[0]
            if _is_private_ip(ip_str):
                return False
        return True
    except Exception:
        return False
