# AGENTS.md

## Cursor Cloud specific instructions

subscripz-buster is a **Python** subscription / recurring-payment hunter for **Apple
Mail**. It runs as both a CLI scanner suite and a **FastMCP server** (`server.py`,
stdio). See `README.md` / `QUICK_REFERENCE.md` for the full command list.

### Environment (uv-managed — this matters)
- The project is managed with **`uv`** (`pyproject.toml` + `uv.lock`, Python 3.12). The
  startup update script runs `uv sync`, which creates `.venv/` (gitignored) with the
  **locked** dependency versions. Use `.venv/bin/python ...` to run anything.
- **Do not** `pip install` the latest deps over this. The lockfile pins `mcp==1.9.4`;
  newer `mcp` releases break `server.py` at import (`FastMCP.__init__() got an
  unexpected keyword argument 'description'`). Always reproduce the env via `uv sync`.
- `uv` is installed at `~/.local/bin/uv`.

### Running / testing
- MCP server: `.venv/bin/python server.py` (stdio). To smoke-test without a client,
  pipe an `initialize` + `notifications/initialized` + `tools/list` JSON-RPC sequence
  into it. It exposes ~10 tools (`scan_all_subscriptions`, `comprehensive_scan`,
  `find_duplicate_subscriptions`, `financial_summary`, `export_to_excel`, …) and shells
  out to the scanner scripts as subprocesses.
- CLI scanners: e.g. `.venv/bin/python working_scanner.py --days 365`
  (`--dry-run`, `--output-json <path>`, `--quiet`). Interactive launcher:
  `scan_subscriptions_now.py`.

### Non-obvious notes — testing on Linux (no Apple Mail)
- Scanners read the macOS Apple Mail SQLite DB at
  `~/Library/Mail/V10|V9|V8/MailData/Envelope Index` and raise `FileNotFoundError`
  if it's absent. There is no Apple Mail on the Linux cloud VM.
- To exercise the scanners/MCP server end-to-end here, create a **synthetic
  `Envelope Index`** SQLite DB at `~/Library/Mail/V10/MailData/Envelope Index` matching
  the queried schema:
  - `subjects(ROWID INTEGER PK, subject TEXT)`
  - `addresses(ROWID INTEGER PK, address TEXT)`
  - `messages(ROWID INTEGER PK, message_id INTEGER, subject INTEGER→subjects.ROWID,
    sender INTEGER→addresses.ROWID, date_received INTEGER unix-seconds)`
  - optional `recipients(message INTEGER, address INTEGER, type INTEGER)` (`type=0` = "To")
  Put dollar amounts in the subject text so `PaymentExtractor` can pick them up. This
  DB lives outside the repo, so rebuild it if the VM state is fresh.
- Output JSON/CSV/XLSX and `*.log` are gitignored.
