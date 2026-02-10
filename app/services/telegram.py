import hashlib
from dataclasses import dataclass
from datetime import datetime

import requests


@dataclass
class TelegramMessage:
    text: str
    payload_hash: str


def format_message(niche: str, scored: list[dict], timestamp: datetime) -> TelegramMessage:
    header = f"🔥 Rising videos (niche: {niche}) — {timestamp:%Y-%m-%d %H:%M}"
    lines = [header]
    for index, item in enumerate(scored, start=1):
        lines.append(
            f"{index}) {item['title']} — Score {item['score']:.2f}\n"
            f"   +{item['views_velocity']:.0f} views/h | age {item['age_hours']:.1f}h | ER {item['engagement_rate'] * 100:.1f}%\n"
            f"   {item['url']}"
        )
    text = "\n\n".join(lines)
    payload_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return TelegramMessage(text=text, payload_hash=payload_hash)


def send_message(bot_token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text[:4000],
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        },
        timeout=20,
    )
    response.raise_for_status()
