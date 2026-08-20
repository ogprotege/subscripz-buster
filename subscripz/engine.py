"""Hunt pipeline: messages → charges → series → actions."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable, List, Optional

from subscripz.actions import plan_actions
from subscripz.extract import (
    extract_amount,
    extract_frequency_hint,
    extract_status_hint,
    is_one_off_order,
    looks_like_receipt,
    looks_like_subscription_language,
)
from subscripz.merchants import identify_merchant
from subscripz.models import Charge, HuntResult, Message
from subscripz.recurrence import build_series
from subscripz.merchants import KNOWN_DOMAINS


def charge_from_message(message: Message) -> Optional[Charge]:
    identity = identify_merchant(message.sender, message.subject, message.snippet)
    if not identity:
        return None
    merchant_key, merchant_name = identity
    text = message.text
    if is_one_off_order(text):
        return None

    amount, currency = extract_amount(text)
    freq = extract_frequency_hint(text)
    status = extract_status_hint(text)
    known = merchant_name in set(KNOWN_DOMAINS.values())
    sub_lang = looks_like_subscription_language(text)
    receipt = looks_like_receipt(text)

    if not (sub_lang or receipt or known or amount):
        return None

    reasons = []
    if sub_lang:
        reasons.append("subscription language")
    if receipt:
        reasons.append("receipt language")
    if known:
        reasons.append("known merchant")
    if amount:
        reasons.append("amount")

    return Charge(
        message=message,
        merchant_key=merchant_key,
        merchant_name=merchant_name,
        amount=amount,
        currency=currency,
        frequency_hint=freq,
        status_hint=status,
        reasons=reasons,
    )


def hunt(
    messages: Iterable[Message],
    *,
    now: Optional[datetime] = None,
    days_back: int = 365,
    source: str = "messages",
    min_confidence: float = 0.28,
) -> HuntResult:
    now = now or datetime.now()
    all_messages = list(messages)
    charges: List[Charge] = []
    for message in all_messages:
        charge = charge_from_message(message)
        if charge:
            charges.append(charge)

    grouped: dict[str, List[Charge]] = defaultdict(list)
    names: dict[str, str] = {}
    for charge in charges:
        grouped[charge.merchant_key].append(charge)
        names[charge.merchant_key] = charge.merchant_name

    series_list = [
        build_series(key, names[key], group) for key, group in grouped.items()
    ]
    series_list = [s for s in series_list if s.confidence >= min_confidence]
    series_list.sort(key=lambda s: (-s.monthly_equivalent(), -s.confidence, s.merchant_name.lower()))

    actions = plan_actions(series_list, now)
    notes = []
    if not all_messages:
        notes.append("No messages in range.")
    elif not series_list:
        notes.append("No recurring series passed the confidence floor.")

    return HuntResult(
        now=now,
        days_back=days_back,
        total_messages=len(all_messages),
        candidate_count=len(charges),
        series=series_list,
        actions=actions,
        source=source,
        notes=notes,
    )
