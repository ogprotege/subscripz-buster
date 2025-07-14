"""
Common data structures and utilities for subscripz-buster scanners.
This module defines the standard JSON output format used by all scanners.
"""

from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import json


@dataclass
class SubscriptionEmail:
    """Represents a single subscription-related email"""
    message_id: int
    subject: str
    sender: str
    recipient: str
    date_received: datetime
    amount: Optional[float] = None
    currency: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['date_received'] = self.date_received.isoformat() if self.date_received else None
        return data


@dataclass
class Subscription:
    """Represents a unique subscription with all its details"""
    company: str
    emails: List[SubscriptionEmail]
    accounts: Set[str]
    amounts: List[float]
    currencies: Set[str]
    first_seen: datetime
    last_seen: datetime
    status: str  # active, cancelled, trial, failed, inactive
    email_count: int
    avg_amount: Optional[float] = None
    frequency: Optional[str] = None  # monthly, annual, quarterly
    billing_period_details: Optional[str] = None  # Raw text that determined frequency
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'company': self.company,
            'email_count': self.email_count,
            'accounts': list(self.accounts),
            'amounts': self.amounts,
            'currencies': list(self.currencies),
            'avg_amount': self.avg_amount,
            'frequency': self.frequency,
            'billing_period_details': self.billing_period_details,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'status': self.status,
            'days_since_last': (datetime.now() - self.last_seen).days if self.last_seen else None,
            'recent_subject': self.emails[-1].subject if self.emails else None,
            'metadata': self.metadata
        }


@dataclass
class DuplicateSubscription:
    """Represents a subscription found on multiple accounts"""
    company: str
    accounts: List[str]
    monthly_waste: float
    total_emails: int
    
    def to_dict(self):
        return asdict(self)


@dataclass
class ScanResults:
    """Standard output structure for all scanners"""
    scan_date: datetime
    scan_parameters: Dict[str, Any]  # days_back, keywords_used, etc.
    total_emails_scanned: int
    subscription_emails_found: int
    unique_subscriptions: List[Subscription]
    duplicate_subscriptions: List[DuplicateSubscription]
    financial_summary: Dict[str, float]
    scan_metadata: Dict[str, Any]  # scanner version, database type, etc.
    
    def to_dict(self):
        """Convert entire results to dictionary for JSON serialization"""
        return {
            'scan_date': self.scan_date.isoformat(),
            'scan_parameters': self.scan_parameters,
            'total_emails_scanned': self.total_emails_scanned,
            'subscription_emails_found': self.subscription_emails_found,
            'unique_subscriptions': [sub.to_dict() for sub in self.unique_subscriptions],
            'duplicate_subscriptions': [dup.to_dict() for dup in self.duplicate_subscriptions],
            'financial_summary': self.financial_summary,
            'scan_metadata': self.scan_metadata
        }
    
    def to_json(self, filepath: Optional[str] = None, pretty: bool = True) -> str:
        """Convert to JSON string and optionally save to file"""
        json_str = json.dumps(
            self.to_dict(),
            indent=2 if pretty else None,
            sort_keys=True
        )
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
        
        return json_str
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for quick display"""
        active_subs = [s for s in self.unique_subscriptions if s.status == 'active']
        inactive_subs = [s for s in self.unique_subscriptions if s.status == 'inactive']
        
        return {
            'total_subscriptions': len(self.unique_subscriptions),
            'active_subscriptions': len(active_subs),
            'inactive_subscriptions': len(inactive_subs),
            'duplicate_count': len(self.duplicate_subscriptions),
            'monthly_total': self.financial_summary.get('monthly_total', 0),
            'annual_total': self.financial_summary.get('annual_total', 0),
            'duplicate_monthly_waste': self.financial_summary.get('duplicate_monthly_waste', 0),
            'accounts_involved': len(set(
                acc for sub in self.unique_subscriptions 
                for acc in sub.accounts
            ))
        }


def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format amount with currency symbol"""
    symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'CAD': 'C$',
        'AUD': 'A$',
        'JPY': '¥'
    }
    symbol = symbols.get(currency, currency + ' ')
    return f"{symbol}{amount:,.2f}"


def calculate_financial_summary(subscriptions: List[Subscription], 
                              duplicates: List[DuplicateSubscription]) -> Dict[str, float]:
    """Calculate financial totals from subscription data"""
    monthly_total = 0
    annual_total = 0
    unknown_high_value_count = 0
    unknown_high_value_total = 0
    
    for sub in subscriptions:
        if sub.avg_amount and sub.status == 'active':
            if sub.frequency == 'monthly':
                monthly_total += sub.avg_amount
                annual_total += sub.avg_amount * 12
            elif sub.frequency == 'annual':
                monthly_total += sub.avg_amount / 12
                annual_total += sub.avg_amount
            elif sub.frequency == 'quarterly':
                monthly_total += sub.avg_amount / 3
                annual_total += sub.avg_amount * 4
            elif sub.frequency == 'semiannual':
                monthly_total += sub.avg_amount / 6
                annual_total += sub.avg_amount * 2
            else:
                # Be cautious with unknown frequencies
                if sub.avg_amount > 200:
                    # Don't assume high amounts are monthly - track separately
                    unknown_high_value_count += 1
                    unknown_high_value_total += sub.avg_amount
                else:
                    # For small amounts, assume monthly
                    monthly_total += sub.avg_amount
                    annual_total += sub.avg_amount * 12
    
    duplicate_waste = sum(dup.monthly_waste for dup in duplicates)
    
    return {
        'monthly_total': round(monthly_total, 2),
        'annual_total': round(annual_total, 2),
        'duplicate_monthly_waste': round(duplicate_waste, 2),
        'duplicate_annual_waste': round(duplicate_waste * 12, 2),
        'potential_monthly_savings': round(duplicate_waste, 2),
        'potential_annual_savings': round(duplicate_waste * 12, 2),
        'unknown_high_value_count': unknown_high_value_count,
        'unknown_high_value_total': round(unknown_high_value_total, 2)
    }
