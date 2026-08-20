"""Shared builders for recurrence-engine tests."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from dateutil.relativedelta import relativedelta

from subscripz.models import Message


def monthly_dates(last: datetime, count: int) -> List[datetime]:
    return [last - relativedelta(months=count - 1 - i) for i in range(count)]


def msg(
    subject: str,
    sender: str,
    when: datetime,
    *,
    recipient: str = "me@example.com",
    message_id: Optional[str] = None,
    snippet: str = "",
) -> Message:
    return Message(
        message_id=message_id or f"{sender}-{when.isoformat()}",
        subject=subject,
        sender=sender,
        recipient=recipient,
        date_received=when,
        snippet=snippet,
    )


def series_mail(
    subject: str,
    sender: str,
    dates: Iterable[datetime],
    recipient: str = "me@example.com",
) -> List[Message]:
    return [msg(subject, sender, when, recipient=recipient) for when in dates]
