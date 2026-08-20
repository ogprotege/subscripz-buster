from datetime import datetime, timedelta

from subscripz.engine import hunt
from subscripz.sources.apple_mail import AppleMailSource, write_envelope_index


def test_write_and_load_envelope_index(tmp_path):
    now = datetime.now()
    rows = [
        {
            "subject": "GitHub Copilot subscription receipt $10.00",
            "sender": "noreply@github.com",
            "recipient": "dev@example.com",
            "date_received": now - timedelta(days=30 * i),
            "snippet": "Thanks for your payment of $10.00",
        }
        for i in range(4)
    ]
    db = tmp_path / "MailData" / "Envelope Index"
    write_envelope_index(db, rows)
    source = AppleMailSource(db)
    messages = source.load(days_back=200)
    assert len(messages) == 4
    assert messages[0].sender == "noreply@github.com"
    assert messages[0].recipient == "dev@example.com"
    assert "10.00" in (messages[0].snippet or messages[0].subject)

    result = hunt(messages, now=now, days_back=200, source="apple-mail")
    assert result.series
    assert result.series[0].merchant_name in {"GitHub", "GitHub Copilot"}
