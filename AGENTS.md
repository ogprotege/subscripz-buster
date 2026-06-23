# AGENTS.md

## Cursor Cloud specific instructions

subscripz-buster is a Python 3.12 toolkit of scanners that find recurring
subscriptions in a local mail store, plus an MCP server (`server.py`). It is
`uv`-managed (`uv.lock`). User-facing usage is in `README.md` / `QUICK_REFERENCE.md`.

The environment update script runs `uv sync` (creates `.venv`) and also installs
`pytest` (a test-only tool that is not in the lockfile). Run things with
`uv run <script>` or `./.venv/bin/<tool>`.

- **The scanners read Apple Mail's local `Envelope Index` SQLite database** at
  `~/Library/Mail/V{10,9,8}/MailData/Envelope Index`. That path only exists on
  macOS, so a *real* scan cannot run on the Linux cloud VM (the scanner raises
  `FileNotFoundError: Could not find Apple Mail's Envelope Index database`). No
  Gmail/Google OAuth is required for these Apple-Mail scanners despite the
  `google-api-*` entries in `pyproject.toml`.
- **To exercise a scanner end-to-end in the cloud, build a synthetic Envelope
  Index** at that path with the normalized schema the scanners expect:
  `subjects(ROWID, subject)`, `addresses(ROWID, address)`, and
  `messages(ROWID, message_id, subject→subjects.ROWID, date_received INT epoch,
  sender→addresses.ROWID)`. Then e.g. `uv run working_scanner.py --days 365`
  (add `--dry-run` to just count, or `--output-json out.json --quiet` to export).
  Subscription detection keys off vendor keywords in the subject line.
- **Tests:** `uv run pytest tests/` (3 tests). The `tests/` and `utils/` scripts
  assume the macOS mail DB or build their own; they are smoke checks, not a full
  suite.
