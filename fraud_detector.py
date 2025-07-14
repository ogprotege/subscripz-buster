#!/usr/bin/env python3
"""
Enhanced fraud detection and filtering for subscription emails
Combines multiple strategies to identify and filter fraudulent subscription emails
"""

import re
from typing import Tuple, Dict, List, Optional
from datetime import datetime
import socket

class FraudDetector:
    """
    Comprehensive fraud detection system for subscription emails.
    
    This class implements multiple layers of protection:
    1. Domain reputation checking
    2. Payment amount validation
    3. Known service whitelisting
    4. Enhanced spam pattern detection
    """
    
    # Known legitimate subscription services (can be expanded)
    LEGITIMATE_SERVICES = {
        # Streaming Services
        'netflix', 'hulu', 'disney', 'disneyplus', 'hbo', 'hbomax', 'peacock',
        'paramount', 'paramountplus', 'appletv', 'amazonprime', 'youtube',
        'spotify', 'applemusic', 'pandora', 'tidal', 'deezer', 'soundcloud',
        
        # Software & Productivity
        'microsoft', 'office365', 'adobe', 'creativeloud', 'zoom', 'slack',
        'notion', 'evernote', 'dropbox', 'googledrive', 'icloud', 'onedrive',
        'lastpass', '1password', 'dashlane', 'nordvpn', 'expressvpn',
        
        # News & Publications
        'nytimes', 'wsj', 'washingtonpost', 'economist', 'bloomberg',
        'reuters', 'apnews', 'cnn', 'foxnews', 'bbc', 'theguardian',
        
        # Shopping & Services
        'amazon', 'walmart', 'target', 'costco', 'samsclub', 'instacart',
        'doordash', 'ubereats', 'grubhub', 'lyft', 'uber', 'airbnb',
        
        # Gaming & Entertainment
        'steam', 'epicgames', 'playstation', 'xbox', 'nintendo',
        'twitch', 'discord', 'patreon', 'onlyfans', 'substack',
        
        # Fitness & Health
        'peloton', 'fitbit', 'strava', 'myfitnesspal', 'headspace', 'calm',
        
        # Financial Services
        'paypal', 'venmo', 'cashapp', 'zelle', 'stripe', 'square',
        
        # Social Media
        'facebook', 'instagram', 'twitter', 'linkedin', 'tiktok', 'snapchat',
        
        # Developer Tools
        'github', 'gitlab', 'bitbucket', 'atlassian', 'jira', 'confluence',
        'heroku', 'digitalocean', 'aws', 'googlecloud', 'azure',
        
        # Education
        'coursera', 'udemy', 'udacity', 'edx', 'masterclass', 'skillshare',
        'duolingo', 'babbel', 'rosettastone'
    }
    
    # Suspicious domain patterns that indicate potential fraud
    SUSPICIOUS_PATTERNS = [
        # Generic names that fraudsters often use
        r'^(email|mail|secure|account|notification|alert|update|verify|confirm)',
        r'^(payment|billing|invoice|order|receipt|transaction)',
        r'^(service|support|customer|help|info|contact)',
        r'^(urgent|important|action|required|immediate)',
        
        # Typosquatting patterns (common misspellings of legitimate services)
        r'netfl[i1]x', r'amaz[o0]n', r'g[o0][o0]gle', r'micr[o0]s[o0]ft',
        r'app[l1]e', r'payp[a@]l', r'ebay\d', r'bankof',
        
        # Excessive numbers or random characters
        r'\d{3,}', r'[a-z0-9]{15,}',
        
        # Multiple hyphens or underscores (often used in phishing)
        r'[-_]{2,}', r'[a-z]+-[a-z]+-[a-z]+-[a-z]+',
    ]
    
    # Known phishing/spam domains (this would be much larger in production)
    BLACKLISTED_DOMAINS = {
        # Common spam domains
        'emailinfo', 'mailserver', 'notification-center', 'account-update',
        'secure-payment', 'billing-department', 'customer-service',
        
        # Temporary email services
        'guerrillamail', 'mailinator', '10minutemail', 'throwawaymail',
        'tempmail', 'fakeinbox', 'trashmail', 'maildrop',
        
        # Known phishing domains (examples)
        'phishing-example', 'scam-domain', 'fake-service'
    }
    
    # Suspicious TLDs often used in fraud
    SUSPICIOUS_TLDS = {
        '.tk', '.ml', '.ga', '.cf',  # Free domains often used for scams
        '.click', '.download', '.review', '.top',  # Generic TLDs favored by scammers
        '.loan', '.work', '.date', '.men'  # Often associated with spam
    }
    
    @classmethod
    def validate_payment_amount(cls, amount: float, frequency: str = None) -> Tuple[bool, str]:
        """
        Validates if a payment amount is reasonable for a subscription.
        
        Returns (is_valid, reason)
        """
        # Convert to monthly equivalent for comparison
        if frequency == 'annual':
            monthly_amount = amount / 12
        elif frequency == 'daily':
            monthly_amount = amount * 30
        elif frequency == 'weekly':
            monthly_amount = amount * 4.33
        else:
            monthly_amount = amount
        
        # Check for unreasonable amounts
        if monthly_amount > 500:
            return False, f"Suspiciously high amount: ${monthly_amount:.2f}/month"
        
        if monthly_amount < 0.50 and monthly_amount > 0:
            return False, f"Suspiciously low amount: ${monthly_amount:.2f}/month"
        
        # Check for common scam amounts
        scam_amounts = [9999, 999, 499, 399, 299, 199]
        if int(amount) in scam_amounts:
            return False, f"Common scam amount: ${amount}"
        
        # Check for amounts that are too precise (like $123.456)
        if '.' in str(amount) and len(str(amount).split('.')[1]) > 2:
            return False, f"Suspicious precision: ${amount}"
        
        return True, "Amount appears reasonable"
    
    @classmethod
    def check_domain_reputation(cls, email: str) -> Tuple[bool, str]:
        """
        Checks if an email domain appears legitimate.
        
        Returns (is_legitimate, reason)
        """
        if not email or '@' not in email:
            return False, "Invalid email format"
        
        domain = email.split('@')[1].lower()
        domain_parts = domain.split('.')
        
        # Check if it's a known legitimate service
        for part in domain_parts:
            if part in cls.LEGITIMATE_SERVICES:
                return True, f"Known legitimate service: {part}"
        
        # Check blacklist
        for blacklisted in cls.BLACKLISTED_DOMAINS:
            if blacklisted in domain:
                return False, f"Blacklisted domain: {blacklisted}"
        
        # Check suspicious TLDs
        for tld in cls.SUSPICIOUS_TLDS:
            if domain.endswith(tld):
                return False, f"Suspicious TLD: {tld}"
        
        # Check suspicious patterns
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if re.match(pattern, domain_parts[0], re.IGNORECASE):
                return False, f"Suspicious domain pattern: {pattern}"
        
        # Check if domain has valid DNS (catches completely fake domains)
        try:
            socket.gethostbyname(domain)
        except socket.gaierror:
            return False, "Domain does not resolve (no DNS)"
        
        # If we get here, domain passes basic checks
        return True, "Domain passes basic validation"
    
    @classmethod
    def extract_legitimate_company_name(cls, sender: str, subject: str = None) -> Optional[str]:
        """
        Extracts company name only if it appears legitimate.
        
        Returns None if the sender appears fraudulent.
        """
        is_legit, reason = cls.check_domain_reputation(sender)
        if not is_legit:
            return None
        
        # Extract domain part
        if '@' in sender:
            domain = sender.split('@')[1].lower()
            company = domain.split('.')[0]
            
            # Skip generic names
            generic_names = {'email', 'mail', 'notification', 'alert', 'info', 
                           'support', 'service', 'account', 'billing', 'payment'}
            if company in generic_names:
                return None
            
            # Check if it's a known service
            if company in cls.LEGITIMATE_SERVICES:
                # Return properly capitalized name
                service_map = {
                    'netflix': 'Netflix',
                    'spotify': 'Spotify',
                    'amazon': 'Amazon',
                    'microsoft': 'Microsoft',
                    'google': 'Google',
                    'apple': 'Apple',
                    'hbo': 'HBO',
                    'disneyplus': 'Disney+',
                    'nytimes': 'New York Times',
                    'wsj': 'Wall Street Journal'
                }
                return service_map.get(company, company.title())
            
            # If not generic and passes domain checks, might be legitimate
            if len(company) > 3:  # Skip very short names
                return company.title()
        
        return None
    
    @classmethod
    def is_likely_fraud(cls, sender: str, subject: str, amount: float = None, 
                       frequency: str = None) -> Tuple[bool, List[str]]:
        """
        Comprehensive fraud check combining all detection methods.
        
        Returns (is_fraud, reasons)
        """
        reasons = []
        
        # Check domain reputation
        domain_ok, domain_reason = cls.check_domain_reputation(sender)
        if not domain_ok:
            reasons.append(f"Domain issue: {domain_reason}")
        
        # Check payment amount if provided
        if amount is not None:
            amount_ok, amount_reason = cls.validate_payment_amount(amount, frequency)
            if not amount_ok:
                reasons.append(f"Payment issue: {amount_reason}")
        
        # Check subject line for scam indicators
        if subject:
            subject_lower = subject.lower()
            
            # Common scam phrases
            scam_phrases = [
                'verify your account', 'confirm your payment', 'urgent action required',
                'suspended account', 'click here immediately', 'limited time offer',
                'congratulations you won', 'claim your prize', 'act now',
                'verify payment method', 'update billing information',
                'your account will be closed', 'security alert'
            ]
            
            for phrase in scam_phrases:
                if phrase in subject_lower:
                    reasons.append(f"Scam phrase detected: '{phrase}'")
                    break
            
            # Check for ALL CAPS (common in scams)
            if subject.isupper() and len(subject) > 10:
                reasons.append("Excessive capitalization (ALL CAPS)")
            
            # Check for excessive punctuation
            if subject.count('!') > 2 or subject.count('$') > 2:
                reasons.append("Excessive punctuation/symbols")
        
        # If we found multiple red flags, it's likely fraud
        is_fraud = len(reasons) >= 2
        
        # Single critical red flag can also indicate fraud
        if not is_fraud and reasons:
            critical_flags = ['Blacklisted domain', 'Domain does not resolve', 
                            'Suspiciously high amount', 'Common scam amount']
            for reason in reasons:
                if any(flag in reason for flag in critical_flags):
                    is_fraud = True
                    break
        
        return is_fraud, reasons
    
    @classmethod
    def clean_email_data(cls, emails: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Filters a list of emails, separating legitimate from fraudulent.
        
        Returns (legitimate_emails, fraudulent_emails)
        """
        legitimate = []
        fraudulent = []
        
        for email in emails:
            sender = email.get('sender', '')
            subject = email.get('subject', '')
            amount = email.get('amount')
            frequency = email.get('frequency')
            
            is_fraud, reasons = cls.is_likely_fraud(sender, subject, amount, frequency)
            
            if is_fraud:
                email['fraud_reasons'] = reasons
                fraudulent.append(email)
            else:
                # Extract legitimate company name
                company = cls.extract_legitimate_company_name(sender, subject)
                if company:
                    email['clean_company'] = company
                    legitimate.append(email)
                else:
                    # Can't identify company, might be fraud
                    email['fraud_reasons'] = ['Cannot identify legitimate company']
                    fraudulent.append(email)
        
        return legitimate, fraudulent


# Example usage and testing
if __name__ == "__main__":
    print("Testing Fraud Detection System")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        ("netflix@email.netflix.com", "Your Netflix subscription", 15.99, "monthly"),
        ("email@phishing-site.tk", "URGENT: Verify your payment!!!", 999.00, "daily"),
        ("noreply@spotify.com", "Your Spotify Premium receipt", 9.99, "monthly"),
        ("secure@notification-update.click", "Account suspended - Act now!", 199.99, None),
        ("billing@microsoft.com", "Office 365 renewal", 99.99, "annual"),
        ("email@secure-payment.ga", "Payment of $168.08 required", 168.08, "daily"),
    ]
    
    for sender, subject, amount, frequency in test_cases:
        is_fraud, reasons = FraudDetector.is_likely_fraud(sender, subject, amount, frequency)
        print(f"\nEmail: {sender}")
        print(f"Subject: {subject}")
        print(f"Amount: ${amount} ({frequency or 'one-time'})")
        print(f"Verdict: {'FRAUD' if is_fraud else 'LEGITIMATE'}")
        if reasons:
            print(f"Reasons: {', '.join(reasons)}")
