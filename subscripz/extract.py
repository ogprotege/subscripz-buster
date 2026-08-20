"""Pull amount, frequency hint, and status from message text."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from payment_extractor import PaymentExtractor  # noqa: E402

SUBSCRIPTION_LANGUAGE = (
    "subscription",
    "subscribe",
    "renewal",
    "renewed",
    "auto-renew",
    "autorenew",
    "recurring",
    "membership",
    "premium plan",
    "your plan",
    "billed",
    "billing",
)

RECEIPT_LANGUAGE = (
    "invoice",
    "receipt",
    "payment",
    "charged",
    "charge",
    "paid",
    "order confirmation",
)

CANCEL_LANGUAGE = ("cancel", "cancelled", "canceled", "terminated", "unsubscribed")
TRIAL_LANGUAGE = ("trial", "free trial", "trial ending", "trial ends")
FAILED_LANGUAGE = ("failed", "declined", "unsuccessful", "past due", "couldn't process")
REFUND_LANGUAGE = ("refund", "refunded", "credit issued")


def _contains(text: str, phrases: Tuple[str, ...] | tuple) -> bool:
    lowered = text.lower()
    return any(p in lowered for p in phrases)


def extract_amount(text: str) -> Tuple[Optional[float], Optional[str]]:
    return PaymentExtractor.extract_amount(text)


def extract_frequency_hint(text: str) -> Optional[str]:
    return PaymentExtractor.extract_frequency(text)


def extract_status_hint(text: str) -> Optional[str]:
    if _contains(text, CANCEL_LANGUAGE):
        return "cancelled"
    if _contains(text, FAILED_LANGUAGE):
        return "failed"
    if _contains(text, REFUND_LANGUAGE):
        return "refunded"
    if _contains(text, TRIAL_LANGUAGE):
        return "trial"
    return None


def looks_like_subscription_language(text: str) -> bool:
    return _contains(text, SUBSCRIPTION_LANGUAGE)


def looks_like_receipt(text: str) -> bool:
    return _contains(text, RECEIPT_LANGUAGE) or _contains(text, SUBSCRIPTION_LANGUAGE)


def is_one_off_order(text: str) -> bool:
    """Shipping / one-time purchase language without subscription words."""
    lowered = text.lower()
    one_off = (
        "has shipped",
        "out for delivery",
        "your order",
        "order shipped",
        "package",
        "tracking",
        "delivered",
    )
    if looks_like_subscription_language(text):
        return False
    return any(p in lowered for p in one_off)
