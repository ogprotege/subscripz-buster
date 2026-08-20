"""Typed records that flow through the hunt pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Message:
    """One mail event. Body is optional; Envelope Index rarely has it."""

    message_id: str
    subject: str
    sender: str
    recipient: str
    date_received: datetime
    snippet: str = ""
    body: str = ""

    @property
    def text(self) -> str:
        return " ".join(part for part in (self.subject, self.snippet, self.body) if part)


@dataclass
class Charge:
    """A candidate charge extracted from one message."""

    message: Message
    merchant_key: str
    merchant_name: str
    amount: Optional[float]
    currency: Optional[str]
    frequency_hint: Optional[str]
    status_hint: Optional[str]
    reasons: List[str] = field(default_factory=list)


@dataclass
class Series:
    """A merchant's charges clustered into a possible recurring series."""

    merchant_key: str
    merchant_name: str
    charges: List[Charge]
    frequency: Optional[str]
    interval_days: Optional[float]
    amount: Optional[float]
    currency: str
    status: str
    confidence: float
    accounts: List[str]
    first_seen: datetime
    last_seen: datetime
    cadence_consistent: bool
    amount_consistent: bool
    evidence: List[str] = field(default_factory=list)

    @property
    def charge_count(self) -> int:
        return len(self.charges)

    def monthly_equivalent(self) -> float:
        if not self.amount:
            return 0.0
        freq = self.frequency or "monthly"
        divisors = {
            "daily": 1 / 30.4,
            "weekly": 7 / 30.4,
            "biweekly": 14 / 30.4,
            "monthly": 1.0,
            "quarterly": 1 / 3,
            "semiannual": 1 / 6,
            "annual": 1 / 12,
        }
        return round(self.amount * divisors.get(freq, 1.0), 2)


@dataclass
class Action:
    kind: str
    merchant_name: str
    merchant_key: str
    reason: str
    monthly_impact: float
    confidence: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HuntResult:
    now: datetime
    days_back: int
    total_messages: int
    candidate_count: int
    series: List[Series]
    actions: List[Action]
    source: str
    notes: List[str] = field(default_factory=list)

    def financials(self) -> Dict[str, float]:
        active = [
            s
            for s in self.series
            if s.status not in {"cancelled", "dropped"} and s.confidence >= 0.35
        ]
        monthly = sum(s.monthly_equivalent() for s in active)
        recoverable = sum(a.monthly_impact for a in self.actions if a.kind != "keep")
        return {
            "monthly_total": round(monthly, 2),
            "annual_total": round(monthly * 12, 2),
            "recoverable_monthly": round(recoverable, 2),
            "recoverable_annual": round(recoverable * 12, 2),
            "series_count": len(active),
            "action_count": len([a for a in self.actions if a.kind != "keep"]),
        }

    def to_dict(self) -> Dict[str, Any]:
        money = self.financials()
        return {
            "scan_date": self.now.isoformat(),
            "engine": "subscripz.recurrence",
            "engine_version": "2.4.0",
            "source": self.source,
            "scan_parameters": {"days_back": self.days_back},
            "total_messages": self.total_messages,
            "candidate_count": self.candidate_count,
            "financial_summary": money,
            "notes": self.notes,
            "actions": [
                {
                    "kind": a.kind,
                    "merchant": a.merchant_name,
                    "merchant_key": a.merchant_key,
                    "reason": a.reason,
                    "monthly_impact": a.monthly_impact,
                    "confidence": a.confidence,
                    "details": a.details,
                }
                for a in self.actions
            ],
            "series": [
                {
                    "merchant": s.merchant_name,
                    "merchant_key": s.merchant_key,
                    "status": s.status,
                    "frequency": s.frequency,
                    "interval_days": s.interval_days,
                    "amount": s.amount,
                    "currency": s.currency,
                    "monthly_equivalent": s.monthly_equivalent(),
                    "confidence": s.confidence,
                    "accounts": s.accounts,
                    "charge_count": s.charge_count,
                    "first_seen": s.first_seen.isoformat(),
                    "last_seen": s.last_seen.isoformat(),
                    "days_since_last": (self.now - s.last_seen).days,
                    "cadence_consistent": s.cadence_consistent,
                    "amount_consistent": s.amount_consistent,
                    "evidence": s.evidence,
                    "recent_subject": s.charges[-1].message.subject if s.charges else None,
                }
                for s in self.series
            ],
        }
