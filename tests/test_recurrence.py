from datetime import datetime

from dateutil.relativedelta import relativedelta

from subscripz.models import Charge, Message
from subscripz.recurrence import infer_interval, build_series, amounts_consistent


def _charge(when, amount=15.99, subject="Netflix subscription $15.99/month"):
    return Charge(
        message=Message("1", subject, "noreply@netflix.com", "a@x.com", when),
        merchant_key="netflix",
        merchant_name="Netflix",
        amount=amount,
        currency="USD",
        frequency_hint="monthly",
        status_hint=None,
    )


def test_monthly_gaps():
    last = datetime(2026, 8, 1)
    dates = [last - relativedelta(months=5 - i) for i in range(6)]
    freq, median, consistency = infer_interval(dates)
    assert freq == "monthly"
    assert 28 <= median <= 32
    assert consistency >= 0.8


def test_annual_gap():
    dates = [datetime(2024, 8, 20), datetime(2025, 8, 20), datetime(2026, 8, 18)]
    freq, median, consistency = infer_interval(dates)
    assert freq == "annual"
    assert consistency >= 0.6


def test_single_date_has_no_interval():
    freq, median, consistency = infer_interval([datetime(2026, 8, 1)])
    assert freq is None and median is None and consistency == 0


def test_amount_consistency():
    assert amounts_consistent([9.99, 9.99, 10.19])
    assert not amounts_consistent([9.99, 19.99])


def test_build_series_confidence_high_for_cadence():
    last = datetime(2026, 8, 1)
    charges = [
        _charge(last - relativedelta(months=5 - i))
        for i in range(6)
    ]
    series = build_series("netflix", "Netflix", charges)
    assert series.frequency == "monthly"
    assert series.confidence >= 0.7
    assert series.monthly_equivalent() == 15.99
