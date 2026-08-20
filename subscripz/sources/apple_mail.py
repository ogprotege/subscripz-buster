"""Read Apple Mail's Envelope Index as a stream of Message objects."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from subscripz.models import Message

# Keep this list tight: it is a recall filter, not the product.
KEYWORD_FILTER = (
    "subscription",
    "subscribe",
    "renewal",
    "renew",
    "recurring",
    "membership",
    "invoice",
    "billing",
    "receipt",
    "charged",
    "payment",
    "trial",
    "premium",
    "auto-renew",
    "plan",
)


def find_envelope_index(explicit: Optional[os.PathLike] = None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(f"Mail database not found: {path}")
        return path

    env = os.environ.get("SUBSCRIPZ_MAIL_DB")
    if env:
        path = Path(env)
        if not path.exists():
            raise FileNotFoundError(f"SUBSCRIPZ_MAIL_DB does not exist: {path}")
        return path

    mail_root = Path.home() / "Library" / "Mail"
    for version in ("V10", "V9", "V8", "V7"):
        candidate = mail_root / version / "MailData" / "Envelope Index"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Could not find Apple Mail's Envelope Index. "
        "On a Mac it lives at ~/Library/Mail/V10/MailData/Envelope Index. "
        "Pass --mail-db PATH or set SUBSCRIPZ_MAIL_DB. "
        "For tests use --source messages --messages file.json."
    )


def write_envelope_index(path: Path, rows: Sequence[dict]) -> Path:
    """Create a synthetic Envelope Index for tests and Linux smoke runs."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE subjects (ROWID INTEGER PRIMARY KEY, subject TEXT);
        CREATE TABLE addresses (ROWID INTEGER PRIMARY KEY, address TEXT);
        CREATE TABLE messages (
            ROWID INTEGER PRIMARY KEY,
            message_id INTEGER,
            subject INTEGER,
            sender INTEGER,
            date_received INTEGER,
            snippet TEXT
        );
        CREATE TABLE recipients (
            message INTEGER,
            address INTEGER,
            type INTEGER
        );
        """
    )

    subject_ids = {}
    address_ids = {}

    def subject_id(text: str) -> int:
        if text not in subject_ids:
            cur.execute("INSERT INTO subjects (subject) VALUES (?)", (text,))
            subject_ids[text] = cur.lastrowid
        return subject_ids[text]

    def address_id(text: str) -> int:
        if text not in address_ids:
            cur.execute("INSERT INTO addresses (address) VALUES (?)", (text,))
            address_ids[text] = cur.lastrowid
        return address_ids[text]

    for i, row in enumerate(rows, start=1):
        subj = subject_id(row.get("subject") or "")
        sender = address_id(row.get("sender") or "unknown@example.com")
        received = row.get("date_received")
        if isinstance(received, datetime):
            ts = int(received.timestamp())
        else:
            ts = int(received)
        snippet = row.get("snippet") or ""
        cur.execute(
            """
            INSERT INTO messages (message_id, subject, sender, date_received, snippet)
            VALUES (?, ?, ?, ?, ?)
            """,
            (i, subj, sender, ts, snippet),
        )
        message_rowid = cur.lastrowid
        recipient = row.get("recipient")
        if recipient:
            cur.execute(
                "INSERT INTO recipients (message, address, type) VALUES (?, ?, 0)",
                (message_rowid, address_id(recipient)),
            )

    conn.commit()
    conn.close()
    return path


class AppleMailSource:
    def __init__(self, db_path: Optional[os.PathLike] = None):
        self.db_path = find_envelope_index(db_path)

    def count(self, days_back: int = 365) -> dict:
        cutoff = int((datetime.now() - timedelta(days=days_back)).timestamp())
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        has_subjects = self._has_table(cur, "subjects")
        subject_expr = "s.subject" if has_subjects else "m.subject"
        join = "JOIN subjects s ON m.subject = s.ROWID" if has_subjects else ""
        likes, params = self._like_clause(subject_expr)
        cur.execute(f"SELECT COUNT(*) FROM messages m WHERE m.date_received > ?", (cutoff,))
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT COUNT(DISTINCT m.ROWID)
            FROM messages m
            {join}
            WHERE ({likes}) AND m.date_received > ?
            """,
            (*params, cutoff),
        )
        candidates = cur.fetchone()[0]
        conn.close()
        return {"total_messages": total, "keyword_hits": candidates, "days_back": days_back}

    def load(self, days_back: int = 365) -> List[Message]:
        cutoff = int((datetime.now() - timedelta(days=days_back)).timestamp())
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        has_subjects = self._has_table(cur, "subjects")
        columns = {row[1] for row in cur.execute("PRAGMA table_info(messages)")}
        has_snippet = "snippet" in columns

        subject_expr = "s.subject" if has_subjects else "m.subject"
        join = "JOIN subjects s ON m.subject = s.ROWID" if has_subjects else ""
        snippet_expr = "m.snippet" if has_snippet else "''"
        likes, params = self._like_clause(subject_expr)
        if has_snippet:
            snippet_likes, snippet_params = self._like_clause("m.snippet")
            likes = f"({likes}) OR ({snippet_likes})"
            params = (*params, *snippet_params)

        cur.execute(
            f"""
            SELECT
                m.ROWID,
                {subject_expr} as subject_text,
                m.date_received,
                sender.address as sender_address,
                {snippet_expr} as snippet_text
            FROM messages m
            {join}
            LEFT JOIN addresses sender ON m.sender = sender.ROWID
            WHERE ({likes})
              AND m.date_received > ?
            ORDER BY m.date_received ASC
            """,
            (*params, cutoff),
        )
        rows = cur.fetchall()
        recipients = self._recipients_map(cur, [r[0] for r in rows])
        conn.close()

        messages = []
        for rowid, subject, date_received, sender, snippet in rows:
            recips = recipients.get(rowid, [])
            recipient = recips[0] if recips else ""
            ts = datetime.fromtimestamp(date_received) if date_received else datetime.now()
            messages.append(
                Message(
                    message_id=str(rowid),
                    subject=subject or "",
                    sender=sender or "",
                    recipient=recipient,
                    date_received=ts,
                    snippet=snippet or "",
                )
            )
        return messages

    @staticmethod
    def _has_table(cur: sqlite3.Cursor, name: str) -> bool:
        cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,))
        return cur.fetchone() is not None

    @staticmethod
    def _like_clause(column: str) -> tuple[str, tuple]:
        parts = [f"{column} LIKE ?" for _ in KEYWORD_FILTER]
        params = tuple(f"%{word}%" for word in KEYWORD_FILTER)
        return " OR ".join(parts), params

    def _recipients_map(self, cur: sqlite3.Cursor, message_rowids: Sequence[int]) -> dict:
        mapping: dict[int, list[str]] = {}
        if not message_rowids:
            return mapping
        if not self._has_table(cur, "recipients") or not self._has_table(cur, "addresses"):
            return mapping

        rec_cols = {row[1]: row[2].upper() for row in cur.execute("PRAGMA table_info(recipients)")}
        addr_cols = {row[1]: row[2].upper() for row in cur.execute("PRAGMA table_info(addresses)")}

        msg_col = next(
            (n for n in ("message", "message_id", "messageID", "message_rowid") if n in rec_cols),
            None,
        )
        addr_col = next(
            (n for n in ("address", "address_id", "addresses_id", "email") if n in rec_cols),
            None,
        )
        email_col = next(
            (n for n in ("address", "email", "email_address") if n in addr_cols),
            None,
        )
        type_col = next((n for n in ("type", "recipient_type", "kind") if n in rec_cols), None)
        if not (msg_col and addr_col and email_col):
            return mapping

        addr_is_fk = rec_cols[addr_col] == "INTEGER"
        batch = 400
        ids = [int(i) for i in message_rowids]
        for start in range(0, len(ids), batch):
            chunk = ids[start : start + batch]
            placeholders = ",".join("?" * len(chunk))
            where_type = f"AND r.{type_col} = 0" if type_col else ""
            if addr_is_fk:
                sql = (
                    f"SELECT r.{msg_col}, a.{email_col} "
                    f"FROM recipients r JOIN addresses a ON r.{addr_col} = a.ROWID "
                    f"WHERE r.{msg_col} IN ({placeholders}) {where_type}"
                )
            else:
                sql = (
                    f"SELECT r.{msg_col}, r.{addr_col} "
                    f"FROM recipients r "
                    f"WHERE r.{msg_col} IN ({placeholders}) {where_type}"
                )
            try:
                for msg_id, address in cur.execute(sql, chunk):
                    if msg_id and address:
                        mapping.setdefault(int(msg_id), []).append(str(address))
            except sqlite3.Error:
                break
        return mapping


def iter_apple_mail(days_back: int = 365, db_path: Optional[os.PathLike] = None) -> Iterable[Message]:
    return AppleMailSource(db_path).load(days_back)
