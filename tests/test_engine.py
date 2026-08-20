from datetime import datetime

from tests.helpers import monthly_dates, msg, series_mail
from subscripz.engine import hunt
from subscripz.extract import is_one_off_order


NOW = datetime(2026, 8, 20, 12, 0, 0)


def _fixture():
    netflix_dates = monthly_dates(datetime(2026, 8, 1), 6)
    spotify_dates = monthly_dates(datetime(2026, 8, 5), 5)
    adobe_dates = monthly_dates(datetime(2026, 8, 3), 4)
    gym_dates = monthly_dates(datetime(2026, 3, 20), 3)
    hulu_early = monthly_dates(datetime(2026, 4, 10), 4)
    hulu_late = monthly_dates(datetime(2026, 8, 10), 2)

    messages = []
    messages += series_mail(
        "Your Netflix subscription has been renewed — $15.99/month",
        "noreply@netflix.com",
        netflix_dates,
    )
    messages += series_mail(
        "Spotify Premium — charged $10.99 monthly",
        "no-reply@spotify.com",
        spotify_dates,
    )
    for when in adobe_dates:
        messages.append(
            msg(
                "Adobe Creative Cloud invoice $54.99",
                "noreply@adobe.com",
                when,
                recipient="a@example.com",
            )
        )
        messages.append(
            msg(
                "Adobe Creative Cloud invoice $54.99",
                "noreply@adobe.com",
                when,
                recipient="b@example.com",
            )
        )
    messages += series_mail(
        "Planet Fitness membership dues $24.99/month",
        "billing@planetfitness.com",
        gym_dates,
        recipient="me@example.com",
    )
    messages += series_mail(
        "Hulu — $5.99/month",
        "no-reply@hulu.com",
        hulu_early,
    )
    messages += series_mail(
        "Hulu — $9.99/month",
        "no-reply@hulu.com",
        hulu_late,
    )
    messages.append(
        msg(
            "Your order has shipped — $49.99",
            "shipment-tracking@amazon.com",
            datetime(2026, 8, 10),
        )
    )
    messages.append(
        msg(
            "Invoice #9988 from Acme Supplies total $200.00",
            "billing@acme-supplies.example",
            datetime(2026, 8, 2),
        )
    )
    messages.append(
        msg(
            "Your Cursor Pro free trial started",
            "noreply@cursor.com",
            datetime(2026, 8, 18),
        )
    )
    return messages


def test_one_off_order_helper():
    assert is_one_off_order("Your order has shipped — $49.99")
    assert not is_one_off_order("Your Netflix subscription has shipped? no — $15.99/month")


def test_hunt_finds_cadence_and_drops_one_offs():
    result = hunt(_fixture(), now=NOW, days_back=400, source="messages")
    names = {s.merchant_name for s in result.series}
    assert "Netflix" in names
    assert "Spotify" in names
    assert "Adobe" in names
    assert "Planet Fitness" in names
    assert "Hulu" in names
    assert "Amazon" not in names
    assert "Acme Supplies" not in names and "Acme-Supplies" not in names

    netflix = next(s for s in result.series if s.merchant_name == "Netflix")
    assert netflix.frequency == "monthly"
    assert netflix.amount == 15.99
    assert netflix.confidence >= 0.7


def test_action_plan_ranks_money_moves():
    result = hunt(_fixture(), now=NOW, days_back=400, source="messages")
    kinds = {(a.kind, a.merchant_name) for a in result.actions}
    assert ("cancel_unused", "Planet Fitness") in kinds
    assert ("consolidate", "Adobe") in kinds
    assert ("review_price_hike", "Hulu") in kinds
    assert ("review_trial", "Cursor") in kinds

    gym = next(a for a in result.actions if a.merchant_name == "Planet Fitness")
    assert gym.monthly_impact == 24.99

    adobe = next(a for a in result.actions if a.kind == "consolidate")
    assert adobe.monthly_impact == 54.99

    money = result.financials()
    assert money["recoverable_monthly"] >= 24.99
    assert money["monthly_total"] > 0


def test_single_annual_plan_survives():
    messages = [
        msg(
            "Annual membership renewed for $120.00/year",
            "members@economist.com",
            datetime(2026, 7, 1),
        )
    ]
    result = hunt(messages, now=NOW, days_back=365, source="messages")
    assert len(result.series) == 1
    series = result.series[0]
    assert series.merchant_name == "The Economist"
    assert series.frequency == "annual"
    assert series.monthly_equivalent() == 10.0
