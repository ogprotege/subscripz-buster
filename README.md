# Subscripz-Buster

Local recurring-charge hunter for Apple Mail.

It reads receipt mail on your Mac and answers one question: **what is charging
you on a cadence, how much, and what should you cancel.** No bank login. No
upload. The mail database never leaves the machine.

A subscription here is the same merchant taking a similar amount on a regular
interval — not a subject line that happens to contain the word `payment`.

```text
SUBSCRIPZ HUNT
========================================================================
6 recurring series · $116.95/mo · $1,403.40/yr
4 actions · $83.98/mo recoverable

ACTION PLAN
------------------------------------------------------------------------
1. CANCEL         Planet Fitness          $24.99/mo  Last charge 153 days ago
2. CONSOLIDATE    Adobe                   $54.99/mo  Same merchant on 2 accounts
3. REVIEW PRICE   Hulu                     $4.00/mo  Price moved 5.99 → 9.99
4. REVIEW TRIAL   Cursor                        n/a  Trial language, no paid cadence

LEDGER (highest monthly first)
------------------------------------------------------------------------
#   merchant                  monthly freq        conf   last status
1   Adobe                      $54.99 monthly     0.96    17d active
2   Planet Fitness             $24.99 monthly     0.99   153d active
3   Netflix                    $15.99 monthly     0.99    19d active
```

## Install

macOS, Python 3.12+, Apple Mail with mail downloaded locally. Grant **Full Disk
Access** to Terminal (or iTerm) so the Envelope Index can be read.

```bash
git clone https://github.com/ogprotege/subscripz-buster.git
cd subscripz-buster

# locked environment (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
```

Or a plain venv:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`uv sync` is the path that matches `uv.lock`. Do not `pip install -U mcp` over
it — newer `mcp` breaks `server.py`.

## Hunt

```bash
python -m subscripz scan --days 365
```

Useful flags:

| Flag | What it does |
|---|---|
| `--days 90` | Shorter window |
| `--dry-run` | Count keyword hits, do not cluster |
| `--output-json hunt.json` | Write the full result |
| `--quiet` | No stdout (pair with `--output-json`) |
| `--format json` | JSON on stdout |
| `--mail-db PATH` | Explicit Envelope Index (or `SUBSCRIPZ_MAIL_DB`) |
| `--source messages --messages file.json` | Hunt a fixture instead of Apple Mail |
| `--min-confidence 0.28` | Drop weak series (default 0.28) |

Exit codes: `0` ok, `1` runtime error, `2` missing source / bad usage.

JSON interchange for fixtures and agents:

```json
[
  {
    "subject": "Your Netflix subscription has been renewed — $15.99/month",
    "sender": "noreply@netflix.com",
    "recipient": "me@example.com",
    "date_received": "2026-08-01T00:00:00"
  }
]
```

```bash
python -m subscripz scan --source messages --messages charges.json --format json
```

## How it decides

```
Apple Mail (or a JSON fixture)
        ↓
identify merchant → extract amount / status
        ↓
cluster by merchant, infer interval from charge dates
        ↓
ledger + ranked actions
```

Cadence is inferred from the **gaps between charges** (weekly, monthly, annual,
…). A one-off “your order has shipped” is dropped. A single “annual plan $120”
with subscription language can still land on the ledger, at lower confidence.

| Action | Fired when |
|---|---|
| `cancel_unused` | Last charge older than ~1.6 billing cycles, not cancelled |
| `consolidate` | Same merchant on two or more real recipient accounts |
| `review_price_hike` | Latest amount ≥ 20% over the earlier median |
| `review_trial` | Trial language, no paid cadence yet |
| `keep` | Recent, consistent, one account |

Apple Mail’s Envelope Index is subjects, senders, dates, and sometimes a
snippet. Amounts have to appear in that text. Message bodies (`.emlx`) are not
parsed yet.

## MCP

`server.py` is a stdio FastMCP server. Prefer the in-process tools:

- `hunt_recurring_charges`
- `subscription_action_plan`

Claude Desktop example (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "subscripz-buster": {
      "command": "/ABS/PATH/TO/subscripz-buster/.venv/bin/python",
      "args": ["/ABS/PATH/TO/subscripz-buster/server.py"]
    }
  }
}
```

Older tools (`scan_all_subscriptions`, `comprehensive_scan`, …) still shell out
to the legacy scripts.

## Privacy

- Read-only SQLite against `~/Library/Mail/V*/MailData/Envelope Index`
- No network calls in the hunt path
- No analytics
- Reports you ask for are written where you point `--output-json`

## Tests

```bash
uv run pytest tests/
```

The suite does not need Apple Mail. It uses JSON fixtures and a synthetic
Envelope Index via `--mail-db`.

## If the hunt is empty

1. Apple Mail has actually downloaded the messages (not headers-only).
2. Terminal has Full Disk Access.
3. Widen the window: `--days 730`.
4. Preview the raw hit count: `--dry-run`.
5. Confirm the DB path: `--mail-db "$HOME/Library/Mail/V10/MailData/Envelope Index"`.

## Legacy scanners

The original 17-option menu (`scan_subscriptions_now.py`) and scripts such as
`working_scanner.py` are still in the tree. They grep subject lines. Use them
only if you are debugging an old workflow. The product is `python -m subscripz`.

## License

MIT. See [LICENSE](LICENSE).
