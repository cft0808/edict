from __future__ import annotations

from typing import Type

from .base import NotificationChannel
from .feishu import FeishuChannel
from .wecom import WecomChannel
from .telegram import TelegramChannel
from .discord import DiscordChannel
from .slack import SlackChannel
from .webhook import WebhookChannel
from .qq import QQChannel


CHANNELS: dict[str, Type[NotificationChannel]] = {
    "feishu": FeishuChannel,
    "wecom": WecomChannel,
    "telegram": TelegramChannel,
    "discord": DiscordChannel,
    "slack": SlackChannel,
    "webhook": WebhookChannel,
    "qq": QQChannel,
}


def get_channel(channel_type: str) -> Type[NotificationChannel] | None:
    return CHANNELS.get(channel_type)


def get_all_channels() -> list[Type[NotificationChannel]]:
    return list(CHANNELS.values())


def get_channel_info() -> list[dict]:
    return [
        {
            "id": ch.name,
            "label": ch.label,
            "icon": ch.icon,
            "placeholder": ch.placeholder,
        }
        for ch in CHANNELS.values()
    ]


__all__ = [
    "NotificationChannel",
    "FeishuChannel",
    "WecomChannel",
    "TelegramChannel",
    "DiscordChannel",
    "SlackChannel",
    "WebhookChannel",
    "QQChannel",
    "CHANNELS",
    "get_channel",
    "get_all_channels",
    "get_channel_info",
]
