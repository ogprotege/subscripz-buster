"""Infer billing cadence from charge dates and amounts."""

from __future__ import annotations

import statistics
from datetime import datetime
from typing import List, Optional, Sequence, Tuple

from subscripz.models import Charge, Series

# (name, typical_days, tolerance_days)
INTERVAL_BUCKETS: Tuple[Tuple[str, float, float], ...] = (
    ("weekly", 7.0, 2.0),
    ("biweekly", 14.0, 3.0),
    ("monthly", 30.4, 6.0),
    ("quarterly", 91.0, 14.0),
    ("semiannual", 183.0, 21.0),
    ("annual", 365.0, 30.0),
)


def _unique_days(dates: Sequence[datetime]) -> List[datetime]:
    seen = {}
    for dt in dates:
        seen[dt.date()] = datetime(dt.year, dt.month, dt.day)
    return sorted(seen.values())


def infer_interval(
    dates: Sequence[datetime],
) -> Tuple[Optional[str], Optional[float], float]:
    """
    Return (frequency, median_gap_days, consistency 0-1).
    Consistency is the share of gaps within 20% (min 3 days) of the median.
    """
    days = _unique_days(dates)
    if len(days) < 2:
        return None, None, 0.0

    gaps = [(days[i] - days[i - 1]).days for i in range(1, len(days))]
    gaps = [g for g in gaps if g > 0]
    if not gaps:
        return None, None, 0.0

    median_gap = float(statistics.median(gaps))
    slop = max(3.0, 0.2 * median_gap)
    close = sum(1 for g in gaps if abs(g - median_gap) <= slop)
    consistency = close / len(gaps)

    for name, center, tolerance in INTERVAL_BUCKETS:
        if abs(median_gap - center) <= tolerance:
            return name, median_gap, consistency
    return None, median_gap, consistency


def amounts_consistent(amounts: Sequence[float], ratio: float = 0.2) -> bool:
    values = [a for a in amounts if a and a > 0]
    if len(values) < 2:
        return True
    median = statistics.median(values)
    if median <= 0:
        return False
    return all(abs(a - median) / median <= ratio for a in values)


def score_series(
    *,
    n_charges: int,
    frequency: Optional[str],
    consistency: float,
    has_amount: bool,
    amount_ok: bool,
    hint_matches: bool,
    subscription_language: bool,
    known_merchant: bool,
) -> float:
    score = 0.12
    if frequency:
        score += 0.40 * max(consistency, 0.35)
    if n_charges >= 4:
        score += 0.22
    elif n_charges == 3:
        score += 0.16
    elif n_charges == 2:
        score += 0.08
    if has_amount:
        score += 0.10
    if amount_ok and has_amount:
        score += 0.08
    if hint_matches:
        score += 0.08
    if subscription_language:
        score += 0.08
    if known_merchant:
        score += 0.04
    return round(min(score, 0.99), 2)


def choose_amount(charges: Sequence[Charge]) -> Tuple[Optional[float], str]:
    amounts = [(c.amount, c.currency or "USD") for c in charges if c.amount]
    if not amounts:
        return None, "USD"
    # Prefer the latest observed amount — that is what they will be charged next.
    latest = next((c.amount for c in reversed(charges) if c.amount), None)
    currency = next((c.currency for c in reversed(charges) if c.currency), "USD")
    return latest, currency or "USD"


def build_series(merchant_key: str, merchant_name: str, charges: List[Charge]) -> Series:
    charges = sorted(charges, key=lambda c: c.message.date_received)
    dates = [c.message.date_received for c in charges]
    frequency, interval_days, consistency = infer_interval(dates)
    amount, currency = choose_amount(charges)
    amount_ok = amounts_consistent([c.amount for c in charges if c.amount])

    hints = [c.frequency_hint for c in charges if c.frequency_hint]
    hint = hints[-1] if hints else None
    hint_matches = bool(hint and frequency and hint == frequency)

    statuses = [c.status_hint for c in charges if c.status_hint]
    if statuses and statuses[-1] == "cancelled":
        status = "cancelled"
    elif statuses and statuses[-1] == "failed":
        status = "failed"
    elif statuses and statuses[-1] == "trial" and not frequency:
        status = "trial"
    else:
        status = "active"

    texts = [c.message.text for c in charges]
    subscription_language = any(
        any(
            word in t.lower()
            for word in ("subscription", "membership", "renewal", "recurring", "auto-renew")
        )
        for t in texts
    )
    from subscripz.merchants import KNOWN_DOMAINS

    known = merchant_name in set(KNOWN_DOMAINS.values())

    confidence = score_series(
        n_charges=len(charges),
        frequency=frequency,
        consistency=consistency,
        has_amount=amount is not None,
        amount_ok=amount_ok,
        hint_matches=hint_matches,
        subscription_language=subscription_language,
        known_merchant=known,
    )

    # Single receipt with no cadence is a weak candidate unless language is explicit.
    if len(charges) == 1 and not frequency:
        if status == "trial":
            confidence = max(confidence, 0.40)
        elif subscription_language and amount:
            confidence = max(confidence, 0.36)
            status = "active"
        else:
            confidence = min(confidence, 0.24)
            status = "one_off"

    accounts = sorted(
        {
            c.message.recipient
            for c in charges
            if c.message.recipient and "@" in c.message.recipient
        }
    )

    evidence = []
    if frequency:
        evidence.append(f"median gap {interval_days:.0f}d → {frequency}")
    if hint:
        evidence.append(f"text hint: {hint}")
    if amount:
        evidence.append(f"latest amount {currency} {amount:.2f}")
    if subscription_language:
        evidence.append("subscription language in subjects")

    return Series(
        merchant_key=merchant_key,
        merchant_name=merchant_name,
        charges=charges,
        frequency=frequency or hint,
        interval_days=interval_days,
        amount=amount,
        currency=currency,
        status=status,
        confidence=confidence,
        accounts=accounts,
        first_seen=charges[0].message.date_received,
        last_seen=charges[-1].message.date_received,
        cadence_consistent=bool(frequency) and consistency >= 0.6,
        amount_consistent=amount_ok,
        evidence=evidence,
    )
