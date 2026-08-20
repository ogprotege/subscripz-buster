"""Turn series into a ranked cancel / consolidate / review plan."""

from __future__ import annotations

from datetime import datetime
from typing import List

from subscripz.models import Action, Series


KEEP = "keep"
CANCEL_UNUSED = "cancel_unused"
CONSOLIDATE = "consolidate"
PRICE_HIKE = "review_price_hike"
REVIEW_TRIAL = "review_trial"


def _cycle_days(series: Series) -> float:
    if series.interval_days:
        return series.interval_days
    mapping = {
        "weekly": 7,
        "biweekly": 14,
        "monthly": 30.4,
        "quarterly": 91,
        "semiannual": 183,
        "annual": 365,
    }
    return mapping.get(series.frequency or "", 30.4)


def plan_actions(series_list: List[Series], now: datetime) -> List[Action]:
    actions: List[Action] = []
    for series in series_list:
        if series.status == "one_off" or series.confidence < 0.28:
            continue

        monthly = series.monthly_equivalent()
        days_since = (now - series.last_seen).days
        cycle = _cycle_days(series)

        if series.status == "trial":
            actions.append(
                Action(
                    kind=REVIEW_TRIAL,
                    merchant_name=series.merchant_name,
                    merchant_key=series.merchant_key,
                    reason="Trial language with no paid cadence yet",
                    monthly_impact=monthly,
                    confidence=series.confidence,
                    details={"days_since_last": days_since},
                )
            )
            continue

        if (
            series.status != "cancelled"
            and series.frequency
            and days_since > 1.6 * cycle
        ):
            actions.append(
                Action(
                    kind=CANCEL_UNUSED,
                    merchant_name=series.merchant_name,
                    merchant_key=series.merchant_key,
                    reason=(
                        f"Last charge {days_since} days ago "
                        f"(cycle ≈ {cycle:.0f} days). Confirm it is cancelled "
                        f"or you are still being billed."
                    ),
                    monthly_impact=monthly,
                    confidence=series.confidence,
                    details={"days_since_last": days_since, "cycle_days": cycle},
                )
            )

        if len(series.accounts) >= 2:
            waste = round(monthly * (len(series.accounts) - 1), 2)
            actions.append(
                Action(
                    kind=CONSOLIDATE,
                    merchant_name=series.merchant_name,
                    merchant_key=series.merchant_key,
                    reason=f"Same merchant on {len(series.accounts)} accounts",
                    monthly_impact=waste,
                    confidence=series.confidence,
                    details={"accounts": series.accounts},
                )
            )

        amounts = [c.amount for c in series.charges if c.amount]
        if len(amounts) >= 2:
            earlier = amounts[:-1]
            latest = amounts[-1]
            median_earlier = sorted(earlier)[len(earlier) // 2]
            if median_earlier > 0 and latest >= median_earlier * 1.2:
                hike = latest - median_earlier
                freq = series.frequency or "monthly"
                divisors = {
                    "weekly": 7 / 30.4,
                    "biweekly": 14 / 30.4,
                    "monthly": 1.0,
                    "quarterly": 1 / 3,
                    "semiannual": 1 / 6,
                    "annual": 1 / 12,
                }
                hike_monthly = round(hike * divisors.get(freq, 1.0), 2)
                actions.append(
                    Action(
                        kind=PRICE_HIKE,
                        merchant_name=series.merchant_name,
                        merchant_key=series.merchant_key,
                        reason=f"Price moved {median_earlier:.2f} → {latest:.2f}",
                        monthly_impact=hike_monthly,
                        confidence=series.confidence,
                        details={"from": median_earlier, "to": latest},
                    )
                )

        kinds_for_merchant = {a.kind for a in actions if a.merchant_key == series.merchant_key}
        if not (kinds_for_merchant - {KEEP}):
            actions.append(
                Action(
                    kind=KEEP,
                    merchant_name=series.merchant_name,
                    merchant_key=series.merchant_key,
                    reason="Recent consistent charges on one account",
                    monthly_impact=0.0,
                    confidence=series.confidence,
                    details={"monthly_equivalent": monthly},
                )
            )

    priority = {
        CANCEL_UNUSED: 0,
        CONSOLIDATE: 1,
        PRICE_HIKE: 2,
        REVIEW_TRIAL: 3,
        KEEP: 9,
    }
    actions.sort(
        key=lambda a: (priority.get(a.kind, 5), -a.monthly_impact, a.merchant_name.lower())
    )
    return actions
