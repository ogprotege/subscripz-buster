"""Human and machine-readable hunt reports."""

from __future__ import annotations

import json

from subscripz.models import HuntResult


KIND_LABEL = {
    "cancel_unused": "CANCEL",
    "consolidate": "CONSOLIDATE",
    "review_price_hike": "REVIEW PRICE",
    "review_trial": "REVIEW TRIAL",
    "keep": "KEEP",
}


def format_money(amount: float, currency: str = "USD") -> str:
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "CAD": "C$", "AUD": "A$", "JPY": "¥"}
    symbol = symbols.get(currency, currency + " ")
    return f"{symbol}{amount:,.2f}"


def render_text(result: HuntResult) -> str:
    money = result.financials()
    lines = [
        "SUBSCRIPZ HUNT",
        "=" * 72,
        (
            f"{money['series_count']} recurring series · "
            f"{format_money(money['monthly_total'])}/mo · "
            f"{format_money(money['annual_total'])}/yr"
        ),
        (
            f"{money['action_count']} actions · "
            f"{format_money(money['recoverable_monthly'])}/mo recoverable"
        ),
        f"source={result.source}  window={result.days_back}d  "
        f"messages={result.total_messages}  candidates={result.candidate_count}",
    ]
    for note in result.notes:
        lines.append(f"note: {note}")

    actionable = [a for a in result.actions if a.kind != "keep"]
    lines.append("")
    lines.append("ACTION PLAN")
    lines.append("-" * 72)
    if not actionable:
        lines.append("No cancel/consolidate/review actions. Everything looks consistent.")
    else:
        for i, action in enumerate(actionable, 1):
            impact = (
                f"{format_money(action.monthly_impact)}/mo"
                if action.monthly_impact
                else "n/a"
            )
            lines.append(
                f"{i}. {KIND_LABEL.get(action.kind, action.kind.upper()):<14} "
                f"{action.merchant_name:<22} {impact:>10}  {action.reason}"
            )

    lines.append("")
    lines.append("LEDGER (highest monthly first)")
    lines.append("-" * 72)
    if not result.series:
        lines.append("No series.")
        return "\n".join(lines)

    header = f"{'#':<3} {'merchant':<22} {'monthly':>10} {'freq':<10} {'conf':>5} {'last':>6} {'status':<10} accounts"
    lines.append(header)
    for i, series in enumerate(result.series, 1):
        days = (result.now - series.last_seen).days
        accounts = ",".join(series.accounts) if series.accounts else "-"
        if len(accounts) > 36:
            accounts = accounts[:33] + "..."
        lines.append(
            f"{i:<3} {series.merchant_name[:22]:<22} "
            f"{format_money(series.monthly_equivalent(), series.currency):>10} "
            f"{(series.frequency or '?'):<10} {series.confidence:>5.2f} "
            f"{days:>5}d {series.status:<10} {accounts}"
        )
    return "\n".join(lines)


def render_json(result: HuntResult, pretty: bool = True) -> str:
    return json.dumps(result.to_dict(), indent=2 if pretty else None)


def write_json(result: HuntResult, path: str) -> None:
    with open(path, "w") as handle:
        handle.write(render_json(result))
