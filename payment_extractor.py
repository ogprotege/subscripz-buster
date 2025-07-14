#!/usr/bin/env python3
"""
Enhanced payment amount extraction utilities for subscription scanners
"""

import re
from typing import Tuple, Optional, List
from collections import defaultdict

class PaymentExtractor:
    """Advanced payment amount extraction from email text"""
    
    # Comprehensive currency patterns
    CURRENCY_PATTERNS = [
        # Dollar amounts
        (r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
        (r'USD\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
        (r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|US\$|dollars?)', 'USD'),
        (r'(?:amount|total|charge|payment|price|cost|fee|due|billed?)[\s:]+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
        
        # Euro amounts
        (r'€\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'EUR'),
        (r'EUR\s*€?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'EUR'),
        (r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:EUR|euros?)', 'EUR'),
        
        # Pound amounts
        (r'£\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'GBP'),
        (r'GBP\s*£?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'GBP'),
        (r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:GBP|pounds?)', 'GBP'),
        
        # Other currencies
        (r'¥\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'JPY'),
        (r'C\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'CAD'),
        (r'A\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'AUD'),
        (r'₹\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'INR'),
        
        # Subscription-specific patterns
        (r'\$(\d{1,3}(?:\.\d{2})?)\s*/\s*(?:month|mo|mnth)', 'USD'),
        (r'\$(\d{1,3}(?:\.\d{2})?)\s*/\s*(?:year|yr|annual)', 'USD'),
        (r'\$(\d{1,3}(?:\.\d{2})?)\s*/\s*(?:week|wk)', 'USD'),
        (r'\$(\d{1,3}(?:\.\d{2})?)\s*(?:per|each)\s*(?:month|year|week)', 'USD'),
        
        # Natural language patterns
        (r'(?:charged?|paid|amount|total|cost|price|fee|bill|invoice)[^\d]*?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
        (r'(?:renew|renewal|subscription|membership)[^\d]*?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
        (r'(?:monthly|annual|yearly|weekly)[^\d]*?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
        
        # Specific vendor patterns
        (r'(?:netflix|spotify|amazon|apple|google|microsoft)[^\d]*?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
        
        # Credit card patterns
        (r'(?:visa|mastercard|amex|discover)[^\d]*?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
        (r'card\s+ending[^\d]*?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
        
        # Invoice patterns
        (r'invoice\s+#?\d+[^\d]*?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
        (r'order\s+#?\d+[^\d]*?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
        
        # Payment confirmation patterns
        (r'payment\s+(?:of|for)[^\d]*?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
        (r'(?:successfully|successfully\s+charged)[^\d]*?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
        
        # Range patterns (take the higher amount)
        (r'\$(\d{1,3}(?:\.\d{2})?)\s*-\s*\$(\d{1,3}(?:\.\d{2})?)', 'USD_RANGE'),
    ]
    
    # Frequency indicators to help determine subscription type
    FREQUENCY_INDICATORS = {
        'monthly': ['monthly', 'month', '/mo', 'per month', 'each month', 'every month'],
        'annual': ['annual', 'yearly', 'year', '/yr', 'per year', 'each year', 'every year'],
        'weekly': ['weekly', 'week', '/wk', 'per week', 'each week', 'every week'],
        'quarterly': ['quarterly', 'quarter', '3 months', 'three months', 'every 3 months'],
        'daily': ['daily', 'day', '/day', 'per day', 'each day', 'every day'],
    }
    
    @classmethod
    def extract_amount(cls, text: str) -> Tuple[Optional[float], Optional[str]]:
        """Extract payment amount and currency from text"""
        if not text:
            return None, None
        
        # Normalize text for better matching
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        
        amounts_found = []
        
        for pattern, currency in cls.CURRENCY_PATTERNS:
            if currency == 'USD_RANGE':
                # Special handling for range patterns
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        # Take the higher amount from range
                        amount1 = float(match.group(1).replace(',', ''))
                        amount2 = float(match.group(2).replace(',', ''))
                        amount = max(amount1, amount2)
                        if 0.99 <= amount <= 10000:
                            amounts_found.append((amount, 'USD', match.start()))
                    except:
                        pass
            else:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        amount_str = match.group(1).replace(',', '')
                        amount = float(amount_str)
                        # Sanity check - subscriptions typically between $0.99 and $10,000
                        if 0.99 <= amount <= 10000:
                            amounts_found.append((amount, currency, match.start()))
                    except:
                        pass
        
        if not amounts_found:
            return None, None
        
        # Sort by position in text (prefer amounts that appear earlier)
        amounts_found.sort(key=lambda x: x[2])
        
        # Filter out unlikely amounts
        filtered_amounts = []
        for amount, currency, pos in amounts_found:
            # Skip year numbers (like 2023, 2024)
            if 2000 <= amount <= 2100:
                continue
            # Skip ZIP codes and other 5-digit numbers
            if 10000 <= amount <= 99999:
                continue
            filtered_amounts.append((amount, currency))
        
        if not filtered_amounts:
            return None, None
        
        # Return the first valid amount found
        return filtered_amounts[0]
    
    @classmethod
    def extract_frequency(cls, text: str) -> Optional[str]:
        """Extract subscription frequency from text"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Check each frequency type
        for frequency, indicators in cls.FREQUENCY_INDICATORS.items():
            for indicator in indicators:
                if indicator in text_lower:
                    return frequency
        
        return None
    
    @classmethod
    def extract_all_amounts(cls, text: str) -> List[Tuple[float, str]]:
        """Extract all payment amounts from text (useful for finding multiple charges)"""
        if not text:
            return []
        
        # Normalize text
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text)
        
        all_amounts = []
        seen_positions = set()
        
        for pattern, currency in cls.CURRENCY_PATTERNS:
            if currency == 'USD_RANGE':
                continue  # Skip range patterns for all amounts
                
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Avoid duplicate matches at same position
                    if match.start() in seen_positions:
                        continue
                    seen_positions.add(match.start())
                    
                    amount_str = match.group(1).replace(',', '')
                    amount = float(amount_str)
                    if 0.99 <= amount <= 10000:
                        # Skip year numbers
                        if 2000 <= amount <= 2100:
                            continue
                        all_amounts.append((amount, currency))
                except:
                    pass
        
        # Remove duplicates while preserving order
        seen = set()
        unique_amounts = []
        for amount in all_amounts:
            if amount not in seen:
                seen.add(amount)
                unique_amounts.append(amount)
        
        return unique_amounts
    
    @classmethod
    def extract_payment_context(cls, text: str, amount: float) -> dict:
        """Extract context around a payment amount for better categorization"""
        if not text or not amount:
            return {}
        
        context = {
            'is_refund': False,
            'is_failed': False,
            'is_trial': False,
            'is_discount': False,
            'payment_method': None,
            'invoice_number': None,
        }
        
        text_lower = text.lower()
        
        # Check for refund
        refund_keywords = ['refund', 'credit', 'reversed', 'returned']
        context['is_refund'] = any(keyword in text_lower for keyword in refund_keywords)
        
        # Check for failed payment
        failed_keywords = ['failed', 'declined', 'unsuccessful', 'rejected', 'insufficient']
        context['is_failed'] = any(keyword in text_lower for keyword in failed_keywords)
        
        # Check for trial
        trial_keywords = ['trial', 'free trial', 'trial period', 'trial ends']
        context['is_trial'] = any(keyword in text_lower for keyword in trial_keywords)
        
        # Check for discount
        discount_keywords = ['discount', 'promo', 'promotion', 'save', 'off', '% off']
        context['is_discount'] = any(keyword in text_lower for keyword in discount_keywords)
        
        # Extract payment method
        payment_methods = {
            'visa': r'visa.*\d{4}',
            'mastercard': r'mastercard.*\d{4}',
            'amex': r'(?:amex|american express).*\d{4}',
            'paypal': r'paypal',
            'card': r'card ending.*\d{4}',
        }
        
        for method, pattern in payment_methods.items():
            if re.search(pattern, text_lower):
                context['payment_method'] = method
                break
        
        # Extract invoice number
        invoice_pattern = r'(?:invoice|order|receipt)\s*#?\s*(\d+)'
        invoice_match = re.search(invoice_pattern, text_lower)
        if invoice_match:
            context['invoice_number'] = invoice_match.group(1)
        
        return context


# Test the extractor
if __name__ == "__main__":
    test_subjects = [
        "Your Netflix subscription has been renewed - $15.99/month",
        "Invoice #12345: Total amount due $49.99",
        "Payment successful: USD 29.95 for Premium Plan",
        "Annual membership renewed for £120.00",
        "Your payment of €9.99 was declined",
        "Spotify Premium - charged $9.99 monthly",
        "Amazon Prime membership: $139/year",
        "Trial ending soon - upgrade for $4.99/mo",
        "Payment failed for $19.99 - please update card",
        "Successfully charged 12.50 USD to Visa ending 1234",
    ]
    
    print("Testing Payment Extractor")
    print("=" * 60)
    
    for subject in test_subjects:
        amount, currency = PaymentExtractor.extract_amount(subject)
        frequency = PaymentExtractor.extract_frequency(subject)
        all_amounts = PaymentExtractor.extract_all_amounts(subject)
        context = PaymentExtractor.extract_payment_context(subject, amount)
        
        print(f"\nSubject: {subject}")
        print(f"  Main amount: {amount} {currency}")
        print(f"  Frequency: {frequency}")
        print(f"  All amounts: {all_amounts}")
        print(f"  Context: {context}")
