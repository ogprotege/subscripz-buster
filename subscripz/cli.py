"""Agent-friendly CLI for the recurring-charge engine."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

from subscripz.engine import hunt
from subscripz.report import render_json, render_text, write_json
from subscripz.sources.apple_mail import AppleMailSource
from subscripz.sources.messages import load_messages


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m subscripz",
        description=(
            "Find recurring charges in local mail and rank what to cancel. "
            "Detects cadence (same merchant, similar amount, regular interval) "
            "instead of grepping subject lines."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m subscripz scan --days 365
  python -m subscripz scan --mail-db "./Envelope Index" --output-json report.json --quiet
  python -m subscripz scan --source messages --messages charges.json --format json
  python -m subscripz scan --dry-run --days 90

Exit codes:
  0  hunt completed
  1  runtime error
  2  missing source / bad usage
""",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Hunt recurring charges and print an action plan")
    scan.add_argument("--days", type=int, default=365, help="Days of history (default: 365)")
    scan.add_argument(
        "--source",
        choices=("apple-mail", "messages"),
        default="apple-mail",
        help="Message source (default: apple-mail)",
    )
    scan.add_argument("--mail-db", help="Path to Envelope Index (or set SUBSCRIPZ_MAIL_DB)")
    scan.add_argument("--messages", help="JSON file of messages (required for --source messages)")
    scan.add_argument("--output-json", help="Write the full hunt result as JSON")
    scan.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Stdout format (default: text)",
    )
    scan.add_argument("--quiet", action="store_true", help="No stdout (use with --output-json)")
    scan.add_argument("--dry-run", action="store_true", help="Count candidates, do not cluster")
    scan.add_argument(
        "--min-confidence",
        type=float,
        default=0.28,
        help="Drop series below this confidence (default: 0.28)",
    )
    return parser


def _load(args) -> tuple:
    if args.source == "messages":
        if not args.messages:
            print(
                "error: --source messages requires --messages PATH",
                file=sys.stderr,
            )
            print("fix: pass a JSON list of {subject,sender,recipient,date_received}", file=sys.stderr)
            return 2, None, None
        path = Path(args.messages)
        if not path.exists():
            print(f"error: messages file not found: {path}", file=sys.stderr)
            return 2, None, None
        return 0, load_messages(path), "messages"

    try:
        source = AppleMailSource(args.mail_db)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2, None, None
    return 0, source, "apple-mail"


def run_scan(args) -> int:
    code, payload, source_name = _load(args)
    if code != 0:
        return code

    if args.dry_run:
        if source_name == "apple-mail":
            stats = payload.count(args.days)
            body = {
                "dry_run": True,
                "source": source_name,
                "days_back": args.days,
                "total_messages": stats["total_messages"],
                "keyword_hits": stats["keyword_hits"],
            }
        else:
            body = {
                "dry_run": True,
                "source": source_name,
                "days_back": args.days,
                "total_messages": len(payload),
                "keyword_hits": len(payload),
            }
        if not args.quiet:
            if args.format == "json":
                print(json.dumps(body, indent=2))
            else:
                print("DRY RUN")
                print(f"   source: {body['source']}")
                print(f"   Total emails in period: {body['total_messages']:,}")
                print(f"   Subscription emails found: {body['keyword_hits']:,}")
        if args.output_json:
            Path(args.output_json).write_text(json.dumps(body, indent=2))
        return 0

    if source_name == "apple-mail":
        messages = payload.load(args.days)
    else:
        messages = payload

    result = hunt(
        messages,
        now=datetime.now(),
        days_back=args.days,
        source=source_name,
        min_confidence=args.min_confidence,
    )

    if args.output_json:
        write_json(result, args.output_json)

    if not args.quiet:
        print(render_json(result) if args.format == "json" else render_text(result))
        if args.output_json and args.format != "json":
            print(f"\nWrote {args.output_json}")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "scan":
            return run_scan(args)
        parser.print_help()
        return 2
    except BrokenPipeError:
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
