"""Load fixture / interchange messages from JSON."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Union

from dateutil.parser import parse as parse_dt

from subscripz.models import Message


def _as_dt(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    return parse_dt(str(value))


def load_messages(path: Union[str, Path]) -> List[Message]:
    raw = json.loads(Path(path).read_text())
    if isinstance(raw, dict) and "messages" in raw:
        raw = raw["messages"]
    if not isinstance(raw, list):
        raise ValueError("Messages JSON must be a list or an object with a 'messages' list")
    return messages_from_dicts(raw)


def messages_from_dicts(rows: Iterable[dict]) -> List[Message]:
    messages = []
    for i, row in enumerate(rows):
        messages.append(
            Message(
                message_id=str(row.get("message_id", i + 1)),
                subject=row.get("subject") or "",
                sender=row.get("sender") or "",
                recipient=row.get("recipient") or "",
                date_received=_as_dt(row.get("date_received") or row.get("date")),
                snippet=row.get("snippet") or "",
                body=row.get("body") or "",
            )
        )
    return messages
