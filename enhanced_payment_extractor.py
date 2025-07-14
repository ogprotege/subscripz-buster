#!/usr/bin/env python3
"""
Enhanced payment extraction with improved frequency detection and validation
"""

import re
from typing import Tuple, Optional, List, Dict
from datetime import datetime

class EnhancedPaymentExtractor:
    """
    Advanced payment extraction that properly identifies frequencies and amounts
    """
    
    # Comprehensive currency patterns with better context awareness
    CURRENCY_PATTERNS = [
        # Dollar amounts with context
        (r'\$\s*(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD)?', 'USD'),
        (r'USD\s*\$?\s*(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
        (r'(?:amount|total|charge|payment|price|cost|fee|due|billed?)[\s:]+\$\s*(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
        
        # With frequency indicators
        (r'\$(\d{1,4}(?:\.\d{2})?)\s*/\s*(?:month|mo|mnth)', 'USD', 'monthly'),
        (r'\$(\d{1,4}(?:\.\d{2})?)\s*/\s*(?:year|yr|annual)', 'USD', 'annual'),
        (r'\$(\d{1,4}(?:\.\d{2})?)\s*/\s*(?:week|wk)', 'USD', 'weekly'),
        (r'\$(\d{1,4}(?:\.\d{2})?)\s*/\s*(?:day)', 'USD', 'daily'),
        (r'\$(\d{1,4}(?:\.\d{2})?)\s*(?:per|each)\s*(?:month|year|week|day)', 'USD', None),
        
        # Annual amounts (commonly in the hundreds)
        (r'(?:annual|yearly|per year).*?\$(\d{2,4}(?:\.\d{2})?)', 'USD', 'annual'),
        (r'\$(\d{2,4}(?:\.\d{2})?)\s*(?:annual|yearly|per year|\/year|\/yr)', 'USD', 'annual'),
        
        # Monthly amounts (commonly under 100)
        (r'(?:monthly|per month).*?\$(\d{1,3}(?:\.\d{2})?)', 'USD', 'monthly'),
        (r'\$(\d{1,3}(?:\.\d{2})?)\s*(?:monthly|per month|\/month|\/mo)', 'USD', 'monthly'),
        
        # Subscription-specific patterns
        (r'(?:subscription|membership|plan|service).*?\$(\d{1,4}(?:\.\d{2})?)', 'USD'),
        (r'(?:renew|renewal|recurring).*?\$(\d{1,4}(?:\.\d{2})?)', 'USD'),
        
        # Euro amounts
        (r'€\s*(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)', 'EUR'),
        (r'EUR\s*€?\s*(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)', 'EUR'),
        (r'(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)\s*(?:EUR|euros?)', 'EUR'),
        
        # Pound amounts
        (r'£\s*(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)', 'GBP'),
        (r'GBP\s*£?\s*(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)', 'GBP'),
        
        # Other currencies
        (r'C\$\s*(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)', 'CAD'),
        (r'A\$\s*(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)', 'AUD'),
        (r'₹\s*(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)', 'INR'),
        (r'¥\s*(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)', 'JPY'),
        
        # Natural language patterns
        (r'(?:charged?|paid|billed?|debited?).*?\$(\d{1,4}(?:\.\d{2})?)', 'USD'),
        (r'(?:payment|invoice|receipt) (?:of|for).*?\$(\d{1,4}(?:\.\d{2})?)', 'USD'),
        
        # Credit card statement patterns
        (r'(?:ending in|card) \d{4}.*?\$(\d{1,4}(?:\.\d{2})?)', 'USD'),
        (r'(?:visa|mastercard|amex|discover).*?\$(\d{1,4}(?:\.\d{2})?)', 'USD'),
    ]
    
    # Enhanced frequency detection patterns
    FREQUENCY_PATTERNS = [
        # Annual patterns (highest priority to catch these first)
        (r'annual(?:ly)?|yearly|every year|per year|once (?:a|per) year|/yr\b|/year\b', 'annual'),
        (r'(?:paid|billed|charged) (?:annually|yearly)', 'annual'),
        (r'12[- ]months?|twelve months?', 'annual'),
        (r'expires? (?:in )?(?:one|1) year', 'annual'),
        (r'valid (?:for|until) (?:one|1) year', 'annual'),
        
        # Semi-annual
        (r'semi[- ]?annual(?:ly)?|every (?:six|6) months?|twice (?:a|per) year', 'semiannual'),
        (r'6[- ]months?|six months?', 'semiannual'),
        
        # Quarterly
        (r'quarter(?:ly)?|every (?:three|3) months?|4 times (?:a|per) year', 'quarterly'),
        (r'(?:paid|billed|charged) quarterly', 'quarterly'),
        (r'3[- ]months?|three months?', 'quarterly'),
        
        # Monthly (most common)
        (r'month(?:ly)?|every month|per month|once (?:a|per) month|/mo\b|/month\b', 'monthly'),
        (r'(?:paid|billed|charged) monthly', 'monthly'),
        (r'(?:on the) \d{1,2}(?:st|nd|rd|th) (?:of each|every) month', 'monthly'),
        (r'expires? (?:in )?(?:one|1) month', 'monthly'),
        (r'30[- ]days?|thirty days?', 'monthly'),
        
        # Bi-weekly
        (r'bi[- ]?weekly|every (?:two|2) weeks?|fortnightly', 'biweekly'),
        (r'(?:paid|billed|charged) (?:bi-weekly|biweekly|every two weeks)', 'biweekly'),
        (r'14[- ]days?|fourteen days?', 'biweekly'),
        
        # Weekly
        (r'week(?:ly)?|every week|per week|once (?:a|per) week|/wk\b|/week\b', 'weekly'),
        (r'(?:paid|billed|charged) weekly', 'weekly'),
        (r'7[- ]days?|seven days?', 'weekly'),
        
        # Daily
        (r'dai(?:ly)?|every day|per day|once (?:a|per) day|/day\b', 'daily'),
        (r'(?:paid|billed|charged) daily', 'daily'),
        
        # One-time
        (r'one[- ]time|single payment|non[- ]recurring|not recurring', 'onetime'),
    ]
    
    # Context clues for frequency inference
    FREQUENCY_CONTEXT_CLUES = {
        'annual': {
            'amount_range': (50, 2000),  # Typical annual amounts
            'keywords': ['subscription', 'membership', 'license', 'premium', 'pro'],
            'services': ['microsoft', 'adobe', 'amazon prime', 'costco', 'sams club']
        },
        'monthly': {
            'amount_range': (1, 200),  # Typical monthly amounts
            'keywords': ['streaming', 'music', 'storage', 'hosting'],
            'services': ['netflix', 'spotify', 'hulu', 'dropbox', 'icloud']
        }
    }
    
    @classmethod
    def extract_amount_and_frequency(cls, text: str) -> Tuple[Optional[float], Optional[str], Optional[str]]:
        """
        Extract payment amount, currency, and frequency from text
        Returns (amount, currency, frequency)
        """
        if not text:
            return None, None, None
        
        # Normalize text
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text)
        
        # First, try to extract frequency explicitly
        detected_frequency = cls._detect_frequency(text)
        
        # Then extract amounts with their context
        amount, currency = cls._extract_amount_with_context(text, detected_frequency)
        
        # If no explicit frequency found, try to infer from amount and context
        if not detected_frequency and amount:
            detected_frequency = cls._infer_frequency(text, amount)
        
        return amount, currency, detected_frequency
    
    @classmethod
    def _detect_frequency(cls, text: str) -> Optional[str]:
        """
        Detect subscription frequency from text using enhanced patterns
        """
        text_lower = text.lower()
        
        # Check each frequency pattern (ordered by priority)
        for pattern, frequency in cls.FREQUENCY_PATTERNS:
            if re.search(pattern, text_lower):
                return frequency
        
        return None
    
    @classmethod
    def _extract_amount_with_context(cls, text: str, known_frequency: str = None) -> Tuple[Optional[float], Optional[str]]:
        """
        Extract amount considering context and frequency
        """
        amounts_found = []
        
        for pattern_info in cls.CURRENCY_PATTERNS:
            pattern = pattern_info[0]
            currency = pattern_info[1]
            pattern_frequency = pattern_info[2] if len(pattern_info) > 2 else None
            
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount = float(amount_str)
                    
                    # Skip unlikely amounts
                    if amount < 0.01 or amount > 50000:
                        continue
                    
                    # Skip years (2020-2030)
                    if 2020 <= amount <= 2030:
                        continue
                    
                    # Skip ZIP codes
                    if 10000 <= amount <= 99999:
                        continue
                    
                    # Calculate priority based on context
                    priority = match.start()  # Earlier in text = higher priority
                    
                    # Boost priority if pattern frequency matches known frequency
                    if pattern_frequency and known_frequency and pattern_frequency == known_frequency:
                        priority -= 1000
                    
                    amounts_found.append((amount, currency, priority))
                    
                except ValueError:
                    continue
        
        if not amounts_found:
            return None, None
        
        # Sort by priority (lower number = higher priority)
        amounts_found.sort(key=lambda x: x[2])
        
        return amounts_found[0][0], amounts_found[0][1]
    
    @classmethod
    def _infer_frequency(cls, text: str, amount: float) -> Optional[str]:
        """
        Infer frequency based on amount and context clues
        """
        text_lower = text.lower()
        
        # Check for service-specific patterns
        for frequency, clues in cls.FREQUENCY_CONTEXT_CLUES.items():
            # Check amount range
            min_amount, max_amount = clues['amount_range']
            if min_amount <= amount <= max_amount:
                # Check for service names
                for service in clues['services']:
                    if service in text_lower:
                        return frequency
                
                # Check for keywords
                keyword_count = sum(1 for keyword in clues['keywords'] if keyword in text_lower)
                if keyword_count >= 2:
                    return frequency
        
        # Default inference based on amount alone
        if amount >= 100:
            # Large amounts are often annual
            if any(word in text_lower for word in ['subscription', 'membership', 'renewal']):
                return 'annual'
        elif amount <= 20:
            # Small amounts are often monthly
            return 'monthly'
        
        return None
    
    @classmethod
    def extract_payment_context(cls, text: str, amount: float = None) -> Dict[str, any]:
        """
        Extract comprehensive payment context
        """
        context = {
            'is_refund': False,
            'is_failed': False,
            'is_trial': False,
            'is_discount': False,
            'is_cancelled': False,
            'is_upgrade': False,
            'is_downgrade': False,
            'payment_method': None,
            'invoice_number': None,
            'next_billing_date': None,
            'subscription_tier': None
        }
        
        if not text:
            return context
        
        text_lower = text.lower()
        
        # Check for refund
        if re.search(r'refund|credit|reversal|returned|money back', text_lower):
            context['is_refund'] = True
        
        # Check for failed payment
        if re.search(r'failed|declined|unsuccessful|rejected|insufficient|denied', text_lower):
            context['is_failed'] = True
        
        # Check for trial
        if re.search(r'trial|free trial|trial period|trial ends|trial expires', text_lower):
            context['is_trial'] = True
        
        # Check for discount
        if re.search(r'discount|promo|promotion|save|% off|coupon|deal', text_lower):
            context['is_discount'] = True
        
        # Check for cancellation
        if re.search(r'cancel|cancelled|terminated|ended|discontinued', text_lower):
            context['is_cancelled'] = True
        
        # Check for plan changes
        if re.search(r'upgrade|upgraded|premium|pro plan', text_lower):
            context['is_upgrade'] = True
        elif re.search(r'downgrade|downgraded|basic plan|free plan', text_lower):
            context['is_downgrade'] = True
        
        # Extract payment method
        payment_patterns = [
            (r'visa\s*(?:ending in |••••\s*)(\d{4})', 'Visa'),
            (r'mastercard\s*(?:ending in |••••\s*)(\d{4})', 'Mastercard'),
            (r'amex\s*(?:ending in |••••\s*)(\d{4})', 'Amex'),
            (r'discover\s*(?:ending in |••••\s*)(\d{4})', 'Discover'),
            (r'paypal', 'PayPal'),
            (r'apple pay', 'Apple Pay'),
            (r'google pay', 'Google Pay'),
            (r'(?:card|payment method) ending in (\d{4})', 'Card'),
        ]
        
        for pattern, method in payment_patterns:
            match = re.search(pattern, text_lower)
            if match:
                context['payment_method'] = method
                if len(match.groups()) > 0:
                    context['payment_method'] += f" ending {match.group(1)}"
                break
        
        # Extract invoice number
        invoice_patterns = [
            r'invoice\s*#?\s*(\w+)',
            r'order\s*#?\s*(\w+)',
            r'receipt\s*#?\s*(\w+)',
            r'transaction\s*(?:id|#)?\s*(\w+)',
            r'reference\s*(?:number|#)?\s*(\w+)'
        ]
        
        for pattern in invoice_patterns:
            match = re.search(pattern, text_lower)
            if match:
                context['invoice_number'] = match.group(1).upper()
                break
        
        # Extract next billing date
        date_patterns = [
            r'next (?:billing|payment|charge)(?: date)?:?\s*(\w+\s+\d{1,2}(?:,?\s*\d{4})?)',
            r'renews?\s+(?:on\s+)?(\w+\s+\d{1,2}(?:,?\s*\d{4})?)',
            r'(?:billing|payment) cycle:?\s*(\w+\s+\d{1,2}(?:,?\s*\d{4})?)',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text_lower)
            if match:
                context['next_billing_date'] = match.group(1)
                break
        
        # Extract subscription tier
        tier_patterns = [
            (r'premium\s*(?:plan|subscription|membership)', 'Premium'),
            (r'pro\s*(?:plan|subscription|membership)', 'Pro'),
            (r'plus\s*(?:plan|subscription|membership)', 'Plus'),
            (r'basic\s*(?:plan|subscription|membership)', 'Basic'),
            (r'standard\s*(?:plan|subscription|membership)', 'Standard'),
            (r'free\s*(?:plan|subscription|membership)', 'Free'),
            (r'family\s*(?:plan|subscription|membership)', 'Family'),
            (r'business\s*(?:plan|subscription|membership)', 'Business'),
            (r'enterprise\s*(?:plan|subscription|membership)', 'Enterprise'),
        ]
        
        for pattern, tier in tier_patterns:
            if re.search(pattern, text_lower):
                context['subscription_tier'] = tier
                break
        
        return context
    
    @classmethod
    def validate_frequency_amount_combination(cls, amount: float, frequency: str, service_name: str = None) -> bool:
        """
        Validate if amount makes sense for the given frequency
        """
        if not amount or not frequency:
            return True
        
        # Define reasonable ranges for each frequency
        frequency_ranges = {
            'daily': (0.10, 50),      # $0.10 - $50/day
            'weekly': (1, 200),       # $1 - $200/week
            'biweekly': (5, 400),     # $5 - $400/biweekly
            'monthly': (0.99, 500),   # $0.99 - $500/month
            'quarterly': (10, 1500),  # $10 - $1500/quarter
            'semiannual': (20, 3000), # $20 - $3000/semi-annual
            'annual': (10, 5000),     # $10 - $5000/year
        }
        
        if frequency in frequency_ranges:
            min_amount, max_amount = frequency_ranges[frequency]
            return min_amount <= amount <= max_amount
        
        return True
    
    @classmethod
    def standardize_frequency(cls, frequency: str) -> str:
        """
        Standardize frequency terms to consistent values
        """
        if not frequency:
            return None
        
        frequency_map = {
            'yearly': 'annual',
            'per year': 'annual',
            'annually': 'annual',
            '/yr': 'annual',
            '/year': 'annual',
            
            'per month': 'monthly',
            '/mo': 'monthly',
            '/month': 'monthly',
            
            'per week': 'weekly',
            '/wk': 'weekly',
            '/week': 'weekly',
            
            'bi-weekly': 'biweekly',
            'every two weeks': 'biweekly',
            'fortnightly': 'biweekly',
            
            'every 3 months': 'quarterly',
            'per quarter': 'quarterly',
            
            'every 6 months': 'semiannual',
            'twice a year': 'semiannual',
            
            'per day': 'daily',
            '/day': 'daily',
            
            'one-time': 'onetime',
            'single': 'onetime',
            'once': 'onetime'
        }
        
        frequency_lower = frequency.lower().strip()
        return frequency_map.get(frequency_lower, frequency_lower)


# Testing
if __name__ == "__main__":
    print("Testing Enhanced Payment Extractor")
    print("=" * 80)
    
    test_cases = [
        # Annual subscriptions that should be properly detected
        "Your Adobe Creative Cloud annual subscription has been renewed for $599.88",
        "Microsoft 365 yearly subscription - $99.99/year",
        "Amazon Prime membership renewed: $139 per year",
        "Annual Costco membership fee of $120 has been charged",
        
        # Monthly subscriptions
        "Netflix monthly subscription: $15.99",
        "Spotify Premium - $9.99/month",
        "Your Dropbox Plus subscription of $11.99 per month",
        
        # Mixed frequencies
        "Gym membership: $49.99 monthly (billed quarterly at $149.97)",
        "Magazine subscription: $4.99/month or $47.88/year - save 20%!",
        
        # Context clues
        "Thank you for your payment of $119.88",  # Should infer annual for ~$120
        "Subscription renewed - $11.99",  # Should infer monthly for small amount
        
        # Failed/Special cases
        "Payment failed for your $9.99 monthly Hulu subscription",
        "Your free trial ends soon - upgrade for $14.99/month",
        "Cancelled: Disney+ annual plan ($79.99/year)",
    ]
    
    for text in test_cases:
        print(f"\nText: {text}")
        amount, currency, frequency = EnhancedPaymentExtractor.extract_amount_and_frequency(text)
        context = EnhancedPaymentExtractor.extract_payment_context(text, amount)
        
        print(f"  Amount: {amount} {currency}")
        print(f"  Frequency: {frequency}")
        
        if frequency and amount:
            # Show monthly equivalent
            from enhanced_fraud_detector import EnhancedFraudDetector
            monthly = EnhancedFraudDetector.calculate_monthly_equivalent(amount, frequency)
            print(f"  Monthly equivalent: ${monthly:.2f}")
        
        # Show relevant context
        relevant_context = {k: v for k, v in context.items() if v and v is not False}
        if relevant_context:
            print(f"  Context: {relevant_context}")
        
        print("-" * 60)
