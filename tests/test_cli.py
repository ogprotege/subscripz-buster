import json
from datetime import datetime
from pathlib import Path

from tests.helpers import monthly_dates
from subscripz.cli import main
from subscripz.sources.apple_mail import write_envelope_index


def test_cli_messages_json(tmp_path, capsys):
    last = datetime(2026, 8, 1)
    rows = []
    for when in monthly_dates(last, 5):
        rows.append(
            {
                "subject": "Your Netflix subscription has been renewed — $15.99/month",
                "sender": "noreply@netflix.com",
                "recipient": "me@example.com",
                "date_received": when.isoformat(),
            }
        )
    path = tmp_path / "mail.json"
    path.write_text(json.dumps(rows))
    out_json = tmp_path / "hunt.json"

    code = main(
        [
            "scan",
            "--source",
            "messages",
            "--messages",
            str(path),
            "--output-json",
            str(out_json),
            "--format",
            "json",
        ]
    )
    assert code == 0
    payload = json.loads(out_json.read_text())
    merchants = {s["merchant"] for s in payload["series"]}
    assert "Netflix" in merchants
    printed = json.loads(capsys.readouterr().out)
    assert printed["engine"] == "subscripz.recurrence"


def test_cli_missing_messages_is_usage_error(capsys):
    code = main(["scan", "--source", "messages"])
    assert code == 2
    err = capsys.readouterr().err
    assert "error:" in err
    assert "fix:" in err


def test_cli_apple_mail_dry_run(tmp_path, capsys):
    rows = []
    for when in monthly_dates(datetime.now(), 3):
        rows.append(
            {
                "subject": "Spotify Premium receipt $10.99",
                "sender": "no-reply@spotify.com",
                "recipient": "me@example.com",
                "date_received": when,
            }
        )
    db = tmp_path / "Envelope Index"
    write_envelope_index(db, rows)
    code = main(["scan", "--mail-db", str(db), "--dry-run", "--days", "400"])
    assert code == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out
    assert "Subscription emails found" in out


def test_cli_apple_mail_full_hunt(tmp_path):
    rows = []
    for when in monthly_dates(datetime.now(), 6):
        rows.append(
            {
                "subject": "Your Netflix subscription has been renewed — $15.99/month",
                "sender": "noreply@netflix.com",
                "recipient": "me@example.com",
                "date_received": when,
            }
        )
    db = tmp_path / "Envelope Index"
    write_envelope_index(db, rows)
    out_json = tmp_path / "out.json"
    code = main(
        [
            "scan",
            "--mail-db",
            str(db),
            "--days",
            "400",
            "--output-json",
            str(out_json),
            "--quiet",
        ]
    )
    assert code == 0
    payload = json.loads(out_json.read_text())
    assert payload["series"][0]["merchant"] == "Netflix"
    assert payload["series"][0]["frequency"] == "monthly"
