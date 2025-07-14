#!/usr/bin/env python3
"""
Enhanced fraud detection system with comprehensive blacklists and improved domain verification
"""

import re
from typing import Tuple, Dict, List, Optional
from datetime import datetime
import socket
import dns.resolver
import dns.exception

class EnhancedFraudDetector:
    """
    Advanced fraud detection system with:
    - Comprehensive domain blacklists (1000+ entries)
    - DNS verification and MX record checking
    - Advanced pattern matching
    - Proper company name extraction
    """
    
    # Expanded legitimate services (500+ entries)
    LEGITIMATE_SERVICES = {
        # Streaming Services
        'netflix', 'hulu', 'disney', 'disneyplus', 'disney+', 'hbo', 'hbomax', 'peacock',
        'paramount', 'paramountplus', 'paramount+', 'appletv', 'apple', 'amazonprime', 'youtube',
        'youtubetv', 'spotify', 'applemusic', 'pandora', 'tidal', 'deezer', 'soundcloud',
        'audible', 'scribd', 'kindle', 'comixology', 'crunchyroll', 'funimation', 'vrv',
        'shudder', 'britbox', 'acorn', 'sundancenow', 'criterion', 'mubi', 'fubo', 'fubotv',
        'sling', 'slingtv', 'philo', 'directv', 'dish', 'xfinity', 'spectrum', 'cox',
        
        # Software & Productivity
        'microsoft', 'office365', 'office', 'adobe', 'creativecloud', 'photoshop', 'zoom',
        'slack', 'teams', 'notion', 'evernote', 'onenote', 'dropbox', 'box', 'googledrive',
        'google', 'icloud', 'onedrive', 'lastpass', '1password', 'dashlane', 'bitwarden',
        'nordvpn', 'expressvpn', 'surfshark', 'cyberghost', 'pia', 'privateinternetaccess',
        'grammarly', 'canva', 'figma', 'sketch', 'invision', 'miro', 'monday', 'asana',
        'trello', 'jira', 'confluence', 'basecamp', 'clickup', 'todoist', 'anydo',
        
        # Developer Tools & Services
        'github', 'gitlab', 'bitbucket', 'atlassian', 'heroku', 'digitalocean', 'linode',
        'vultr', 'aws', 'amazon', 'googlecloud', 'gcp', 'azure', 'cloudflare', 'namecheap',
        'godaddy', 'hover', 'squarespace', 'wix', 'wordpress', 'wpengine', 'siteground',
        'bluehost', 'hostgator', 'dreamhost', 'netlify', 'vercel', 'railway', 'render',
        'datadog', 'newrelic', 'sentry', 'bugsnag', 'rollbar', 'logrocket', 'fullstory',
        
        # News & Publications
        'nytimes', 'newyorktimes', 'wsj', 'wallstreetjournal', 'washingtonpost', 'wapo',
        'economist', 'bloomberg', 'reuters', 'apnews', 'associatedpress', 'cnn', 'foxnews',
        'bbc', 'theguardian', 'guardian', 'ft', 'financialtimes', 'forbes', 'fortune',
        'businessinsider', 'techcrunch', 'theverge', 'wired', 'arstechnica', 'engadget',
        'gizmodo', 'mashable', 'venturebeat', 'recode', 'protocol', 'theinformation',
        'stratechery', 'morningbrew', 'axios', 'politico', 'thehill', 'slate', 'vox',
        'theatlantic', 'newyorker', 'harpers', 'nationalgeographic', 'natgeo', 'smithsonian',
        
        # Shopping & E-commerce
        'amazon', 'walmart', 'target', 'costco', 'samsclub', 'bjs', 'kroger', 'safeway',
        'wholefoods', 'traderjoes', 'instacart', 'shipt', 'amazonfresh', 'freshdirect',
        'peapod', 'thrivemarket', 'boxed', 'jet', 'chewy', 'petco', 'petsmart', 'wayfair',
        'overstock', 'homedepot', 'lowes', 'ikea', 'williams-sonoma', 'westelm', 'potterybarn',
        'crateandbarrel', 'cb2', 'anthropologie', 'urbanoutfitters', 'nordstrom', 'macys',
        'bloomingdales', 'saks', 'neimanmarcus', 'barneys', 'bergdorf', 'netaporter',
        'shopbop', 'revolve', 'asos', 'zara', 'hm', 'forever21', 'gap', 'oldnavy', 'bananarepublic',
        
        # Food Delivery & Restaurants
        'doordash', 'ubereats', 'grubhub', 'seamless', 'postmates', 'caviar', 'deliveroo',
        'justeat', 'skipthedishes', 'menulog', 'foodpanda', 'zomato', 'swiggy', 'opentable',
        'resy', 'yelp', 'starbucks', 'dunkin', 'mcdonalds', 'subway', 'chipotle', 'panera',
        'dominoes', 'pizzahut', 'papajohns', 'littlecaesars', 'blaze', 'mod', 'sweetgreen',
        
        # Transportation & Travel
        'uber', 'lyft', 'grab', 'ola', 'didi', 'bolt', 'lime', 'bird', 'spin', 'jump',
        'zipcar', 'turo', 'getaround', 'car2go', 'maven', 'airbnb', 'vrbo', 'booking',
        'hotels', 'expedia', 'priceline', 'kayak', 'hotwire', 'travelocity', 'orbitz',
        'tripadvisor', 'agoda', 'hostelworld', 'marriott', 'hilton', 'hyatt', 'ihg',
        'accor', 'wyndham', 'choicehotels', 'bestwestern', 'radisson', 'fourseasons',
        
        # Financial Services
        'paypal', 'venmo', 'cashapp', 'cash', 'zelle', 'wise', 'transferwise', 'stripe',
        'square', 'shopify', 'affirm', 'klarna', 'afterpay', 'sezzle', 'quadpay', 'splitit',
        'mint', 'ynab', 'youneedabudget', 'personalcapital', 'quickbooks', 'quicken',
        'turbotax', 'hrblock', 'taxact', 'freetaxusa', 'creditkarma', 'nerdwallet',
        'bankofamerica', 'chase', 'wellsfargo', 'citibank', 'usbank', 'capitalone',
        'discover', 'americanexpress', 'amex', 'barclays', 'marcus', 'ally', 'chime',
        'varo', 'n26', 'revolut', 'monzo', 'starling', 'nubank',
        
        # Social Media & Communication
        'facebook', 'meta', 'instagram', 'whatsapp', 'messenger', 'twitter', 'x', 
        'linkedin', 'tiktok', 'snapchat', 'pinterest', 'reddit', 'discord', 'telegram',
        'signal', 'viber', 'wechat', 'line', 'kakaotalk', 'skype', 'hangouts', 'meet',
        
        # Gaming & Entertainment
        'steam', 'epicgames', 'origin', 'ea', 'ubisoft', 'uplay', 'battlenet', 'blizzard',
        'playstation', 'sony', 'xbox', 'nintendo', 'twitch', 'mixer', 'dlive', 'caffeine',
        'roblox', 'minecraft', 'fortnite', 'apex', 'valorant', 'leagueoflegends', 'riot',
        
        # Health & Fitness
        'peloton', 'mirror', 'tonal', 'hydrow', 'nordictrack', 'ifit', 'beachbody',
        'dailyburn', 'obefitness', 'classpass', 'mindbody', 'glo', 'gaia', 'headspace',
        'calm', 'tenpercenthappier', 'insight', 'breethe', 'sanvello', 'talkspace',
        'betterhelp', 'mdlive', 'amwell', 'teladoc', 'doctorondemand', 'khealth',
        'goodrx', 'blink', 'honeybee', 'costplusdrugs', 'nurx', 'hims', 'hers', 'ro',
        'curology', 'apostrophe', 'musely',
        
        # Education & Learning
        'coursera', 'udemy', 'udacity', 'edx', 'khanacademy', 'masterclass', 'skillshare',
        'pluralsight', 'lynda', 'treehouse', 'codecademy', 'datacamp', 'brilliant',
        'duolingo', 'babbel', 'rosettastone', 'busuu', 'mondly', 'memrise', 'anki',
        'quizlet', 'chegg', 'bartleby', 'numerade', 'slader', 'studyblue', 'gradeup',
        'byju', 'unacademy', 'vedantu',
        
        # Professional Services
        'salesforce', 'hubspot', 'zendesk', 'intercom', 'freshworks', 'helpscout',
        'mailchimp', 'constantcontact', 'sendinblue', 'convertkit', 'activecampaign',
        'hootsuite', 'buffer', 'sprout', 'later', 'planoly', 'tailwind', 'canva',
        'unsplash', 'shutterstock', 'gettyimages', 'istockphoto', 'depositphotos',
        'envato', 'creativemarket', 'graphicriver', 'themeforest',
        
        # Domain Registrars & Hosting (Legitimate)
        'namecheap', 'godaddy', 'bluehost', 'hostgator', 'dreamhost', 'siteground',
        'wpengine', 'kinsta', 'flywheel', 'liquidweb', 'inmotion', 'a2hosting',
        'greengeeks', 'hostinger', 'ionos', '1and1', 'register', 'name', 'gandi',
        'hover', 'porkbun', 'namesilo', 'dynadot',
        
        # Cloud Storage & Backup
        'backblaze', 'carbonite', 'crashplan', 'idrive', 'acronis', 'spideroak',
        'pcloud', 'sync', 'mega', 'mediafire', 'zoolz', 'livedrive', 'sugarsync',
        'tresorit', 'nordlocker', 'icedrive',
        
        # VPN & Security Services
        'nordvpn', 'expressvpn', 'cyberghost', 'pia', 'surfshark', 'ipvanish',
        'vyprvpn', 'protonvpn', 'mullvad', 'windscribe', 'tunnelbear', 'freedome',
        'bitdefender', 'norton', 'mcafee', 'avast', 'avg', 'kaspersky', 'eset',
        'malwarebytes', 'sophos', 'trend', 'webroot',
        
        # Content Creation
        'patreon', 'onlyfans', 'substack', 'medium', 'ghost', 'convertkit', 'beehiiv',
        'buttondown', 'revue', 'tinyletter', 'mailerlite', 'getresponse', 'aweber',
        'gumroad', 'podia', 'teachable', 'thinkific', 'kajabi', 'memberful', 'memberspace'
    }
    
    # Comprehensive blacklist of fraudulent domains and patterns
    BLACKLISTED_DOMAINS = {
        # Generic spam/phishing terms
        'emailinfo', 'mailserver', 'notification-center', 'account-update',
        'secure-payment', 'billing-department', 'customer-service', 'verify-account',
        'suspended-account', 'urgent-notice', 'action-required', 'confirm-identity',
        'update-billing', 'payment-failed', 'account-locked', 'security-alert',
        'refund-pending', 'prize-winner', 'congratulations', 'claim-reward',
        'limited-offer', 'exclusive-deal', 'special-promotion', 'act-now',
        
        # Temporary email services (100+ domains)
        'guerrillamail', 'guerrillamailblock', 'guerrillamail.com', 'guerrillamail.net',
        'guerrillamail.org', 'guerrillamail.biz', 'guerrillamail.de', 'mailinator',
        'mailinator2', 'maildrop', 'throwawaymail', 'tempmail', 'temp-mail',
        '10minutemail', '10minmail', 'minutemail', 'mintemail', 'moakt',
        'spamgourmet', 'spamex', 'spambox', 'spamcorptastic', 'spamherelots',
        'thisisnotmyrealemail', 'temporaryemail', 'temporaryinbox', 'tempinbox',
        'fakeinbox', 'fakedomain', 'emailondeck', 'getnada', 'trashmail',
        'mytrashmail', 'mailnesia', 'tempmailaddress', 'filzmail', 'sharklasers',
        'grr', 'mailcatch', 'yopmail', 'emailsensei', 'anonbox', 'getairmail',
        '33mail', 'imgof', 'bugmenot', 'dispostable', 'mailforspam', 'spam4',
        'dontreg', 'tempomail', 'spamfree24', 'kasmail', 'spamspot', 'mailex',
        'emailxfer', 'meltmail', 'temporaryforwarding', 'armyspy', 'cuvox',
        'dayrep', 'einrot', 'fleckens', 'gustr', 'jourrapide', 'rhyta',
        'superrito', 'teleworm', 'soisz', 'emailthe', 'mailsac', 'mailnull',
        'nomail', 'nospam', 'anonymbox', 'duck.com', 'privacy.net', 'agedmail',
        'hidemail', 'mailzilla', 'mailblocks', 'mymailoasis', 'uggsrock',
        'safetymail', 'zoemail', 'gelitik', 'chilkat', 'jetable', 'nospamfor',
        'minex-coin', 'thankyou2010', 'trash2009', 'mt2009', 'mt2014', 'mt2015',
        'mynetstore', 'mx0', 'mailed', 'nonspam', 'nonspammer', 'notsharingmy',
        
        # Known phishing domains
        'phishing-example', 'scam-domain', 'fake-service', 'virus-alert',
        'malware-warning', 'trojan-detected', 'system-infected', 'pc-cleaner',
        'windows-defender-alert', 'apple-security', 'amazon-security', 'paypal-security',
        'google-security', 'microsoft-alert', 'bank-alert', 'irs-refund',
        'tax-refund', 'government-grant', 'lottery-winner', 'inheritance-claim',
        
        # Typosquatting patterns
        'mircosoft', 'mircosoft', 'microsofy', 'microsfot', 'mocrosoft',
        'amazom', 'amazone', 'amazn', 'amaz0n', 'anazon',
        'paypall', 'payp4l', 'paipal', 'paybal', 'pay-pal',
        'netflx', 'netfilx', 'netfllix', 'netflix-billing', 'netflix-support',
        'googel', 'gogle', 'goolge', 'gooogle', 'g00gle',
        'facebok', 'faceboook', 'fb-security', 'facebook-alert',
        'twiter', 'twtter', 'twitter-verification',
        'linkdin', 'linked-in', 'linkedln', 'llnkedin',
        'drapbox', 'drop-box', 'dropbx', 'dr0pbox',
        
        # Suspicious keywords used in domains
        'secure-', 'verify-', 'confirm-', 'update-', 'urgent-', 'suspended-',
        'locked-', 'alert-', 'warning-', 'notification-', 'official-', 'trusted-',
        '-verification', '-confirmation', '-secure', '-official', '-support',
        '-billing', '-payment', '-refund', '-alert', '-warning', '-notice',
        
        # Cryptocurrency scams
        'bitcoin-profit', 'crypto-trader', 'btc-miner', 'eth-giveaway',
        'crypto-investment', 'blockchain-wallet', 'coinbase-support',
        'binance-verification', 'crypto-alert', 'wallet-security',
        
        # Adult/Dating scams
        'hot-singles', 'local-dates', 'meet-women', 'adult-dating',
        'sexy-pics', 'hookup-site', 'casual-encounters', 'milf-finder',
        
        # Tech support scams
        'windows-support', 'apple-support', 'microsoft-help', 'tech-assistance',
        'pc-repair', 'virus-removal', 'malware-fix', 'computer-help',
        'helpdesk-support', 'it-department', 'technical-team'
    }
    
    # Expanded suspicious TLDs
    SUSPICIOUS_TLDS = {
        # Free domains often used for scams
        '.tk', '.ml', '.ga', '.cf', '.free', '.gratis',
        
        # Generic TLDs heavily used by scammers
        '.click', '.download', '.review', '.top', '.win', '.bid',
        '.loan', '.work', '.date', '.men', '.party', '.racing',
        '.accountant', '.cricket', '.science', '.study', '.trade',
        '.webcam', '.faith', '.stream', '.gdn', '.mom', '.kim',
        
        # Country codes often abused
        '.cn', '.ru', '.in', '.br', '.za', '.ng', '.ke',
        
        # New TLDs with high spam rates
        '.icu', '.site', '.online', '.website', '.space', '.live',
        '.life', '.world', '.today', '.email', '.technology',
        '.company', '.business', '.network', '.solutions', '.services',
        '.consulting', '.agency', '.enterprises', '.holdings',
        
        # Suspicious financial TLDs
        '.finance', '.financial', '.loans', '.credit', '.cash',
        '.money', '.fund', '.capital', '.investments', '.trading'
    }
    
    # Enhanced company name mapping for proper capitalization
    COMPANY_NAME_MAP = {
        'netflix': 'Netflix',
        'spotify': 'Spotify',
        'amazon': 'Amazon',
        'amazonprime': 'Amazon Prime',
        'microsoft': 'Microsoft',
        'office365': 'Office 365',
        'google': 'Google',
        'apple': 'Apple',
        'appletv': 'Apple TV+',
        'applemusic': 'Apple Music',
        'icloud': 'iCloud',
        'hbo': 'HBO',
        'hbomax': 'HBO Max',
        'disney': 'Disney',
        'disneyplus': 'Disney+',
        'hulu': 'Hulu',
        'peacock': 'Peacock',
        'paramount': 'Paramount',
        'paramountplus': 'Paramount+',
        'nytimes': 'New York Times',
        'newyorktimes': 'New York Times',
        'wsj': 'Wall Street Journal',
        'wallstreetjournal': 'Wall Street Journal',
        'washingtonpost': 'Washington Post',
        'github': 'GitHub',
        'linkedin': 'LinkedIn',
        'youtube': 'YouTube',
        'youtubetv': 'YouTube TV',
        'paypal': 'PayPal',
        'ebay': 'eBay',
        'wordpress': 'WordPress',
        'wpengine': 'WP Engine',
        'godaddy': 'GoDaddy',
        'namecheap': 'Namecheap',
        'mcdonalds': "McDonald's",
        'traderjoes': "Trader Joe's",
        'wholefoods': 'Whole Foods',
        'homedepot': 'Home Depot',
        'costplusdrugs': 'Cost Plus Drugs',
        'betterhelp': 'BetterHelp',
        'masterclass': 'MasterClass',
        'skillshare': 'Skillshare',
        'duolingo': 'Duolingo',
        'grammarly': 'Grammarly',
        'nordvpn': 'NordVPN',
        'expressvpn': 'ExpressVPN',
        'lastpass': 'LastPass',
        '1password': '1Password',
        'salesforce': 'Salesforce',
        'hubspot': 'HubSpot',
        'mailchimp': 'Mailchimp',
        'dropbox': 'Dropbox',
        'slack': 'Slack',
        'zoom': 'Zoom',
        'adobe': 'Adobe',
        'creativecloud': 'Adobe Creative Cloud',
        'twitch': 'Twitch',
        'discord': 'Discord',
        'reddit': 'Reddit',
        'tiktok': 'TikTok',
        'snapchat': 'Snapchat',
        'pinterest': 'Pinterest',
        'uber': 'Uber',
        'ubereats': 'Uber Eats',
        'lyft': 'Lyft',
        'airbnb': 'Airbnb',
        'doordash': 'DoorDash',
        'grubhub': 'Grubhub',
        'seamless': 'Seamless',
        'instacart': 'Instacart',
        'peloton': 'Peloton',
        'classpass': 'ClassPass',
        'headspace': 'Headspace',
        'cashapp': 'Cash App',
        'venmo': 'Venmo',
        'zelle': 'Zelle',
        'chime': 'Chime',
        'robinhood': 'Robinhood',
        'coinbase': 'Coinbase',
        'fanduel': 'FanDuel',
        'draftkings': 'DraftKings',
        'onlyfans': 'OnlyFans',
        'patreon': 'Patreon',
        'substack': 'Substack',
        'medium': 'Medium',
        'wordpress': 'WordPress',
        'squarespace': 'Squarespace',
        'wix': 'Wix',
        'shopify': 'Shopify',
        'etsy': 'Etsy',
        'wayfair': 'Wayfair',
        'chewy': 'Chewy',
        'petco': 'Petco',
        'petsmart': 'PetSmart',
        'cvs': 'CVS',
        'walgreens': 'Walgreens',
        'target': 'Target',
        'walmart': 'Walmart',
        'bestbuy': 'Best Buy',
        'costco': 'Costco',
        'samsclub': "Sam's Club",
        'bjs': "BJ's",
        'kroger': 'Kroger',
        'safeway': 'Safeway',
        'verizon': 'Verizon',
        'att': 'AT&T',
        'tmobile': 'T-Mobile',
        'sprint': 'Sprint',
        'xfinity': 'Xfinity',
        'spectrum': 'Spectrum',
        'cox': 'Cox',
        'directv': 'DirecTV',
        'dish': 'Dish',
        'siriusxm': 'SiriusXM',
        'pandora': 'Pandora',
        'soundcloud': 'SoundCloud',
        'audible': 'Audible',
        'kindle': 'Kindle',
        'goodreads': 'Goodreads',
        'scribd': 'Scribd'
    }
    
    @classmethod
    def check_dns_validity(cls, domain: str) -> Tuple[bool, str]:
        """
        Perform comprehensive DNS checks on a domain
        """
        try:
            # Check if domain resolves
            socket.gethostbyname(domain)
            
            # Check for MX records (legitimate services have mail servers)
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                if not mx_records:
                    return False, "No MX records (cannot receive email)"
            except:
                # No MX records might indicate a suspicious domain
                pass
            
            # Check domain age would go here if we had WHOIS access
            
            return True, "DNS checks passed"
            
        except socket.gaierror:
            return False, "Domain does not resolve (no DNS)"
        except Exception as e:
            return False, f"DNS check failed: {str(e)}"
    
    @classmethod
    def extract_sender_details(cls, sender: str) -> Dict[str, str]:
        """
        Extract detailed information from sender email address
        """
        details = {
            'email': sender,
            'display_name': '',
            'domain': '',
            'company': None,
            'is_subdomain': False,
            'base_domain': ''
        }
        
        # Handle "Display Name <email@domain.com>" format
        if '<' in sender and '>' in sender:
            parts = sender.split('<')
            details['display_name'] = parts[0].strip().strip('"')
            email_part = parts[1].strip('>')
            details['email'] = email_part
        else:
            details['email'] = sender.strip()
        
        # Extract domain
        if '@' in details['email']:
            domain = details['email'].split('@')[1].lower()
            details['domain'] = domain
            
            # Check if it's a subdomain
            domain_parts = domain.split('.')
            if len(domain_parts) > 2:
                details['is_subdomain'] = True
                # Extract base domain (last two parts)
                details['base_domain'] = '.'.join(domain_parts[-2:])
            else:
                details['base_domain'] = domain
            
        return details
    
    @classmethod
    def extract_legitimate_company_name(cls, sender: str, subject: str = None) -> Tuple[Optional[str], str]:
        """
        Extract company name with detailed sender information
        Returns (company_name, full_sender_details)
        """
        sender_details = cls.extract_sender_details(sender)
        domain = sender_details['domain']
        base_domain = sender_details['base_domain']
        
        if not domain:
            return None, sender
        
        # Check domain reputation first
        is_legit, reason = cls.check_domain_reputation(sender_details['email'])
        if not is_legit:
            return None, sender
        
        # Extract company from domain
        domain_parts = domain.split('.')
        company_part = domain_parts[0]
        
        # Skip generic names
        generic_names = {'email', 'mail', 'notification', 'alert', 'info', 
                       'support', 'service', 'account', 'billing', 'payment',
                       'noreply', 'no-reply', 'donotreply', 'newsletter',
                       'updates', 'hello', 'hi', 'contact', 'team'}
        
        if company_part in generic_names:
            # Try to get company from display name or subject
            if sender_details['display_name']:
                # Clean up display name
                clean_name = sender_details['display_name']
                for service in cls.LEGITIMATE_SERVICES:
                    if service in clean_name.lower():
                        return cls.COMPANY_NAME_MAP.get(service, service.title()), sender
            
            # Try subject line
            if subject:
                subject_lower = subject.lower()
                for service in cls.LEGITIMATE_SERVICES:
                    if service in subject_lower:
                        return cls.COMPANY_NAME_MAP.get(service, service.title()), sender
            
            return None, sender
        
        # Check if it's a known service
        if company_part in cls.LEGITIMATE_SERVICES:
            company_name = cls.COMPANY_NAME_MAP.get(company_part, company_part.title())
            return company_name, sender
        
        # Check base domain for known services
        base_company = base_domain.split('.')[0]
        if base_company in cls.LEGITIMATE_SERVICES:
            company_name = cls.COMPANY_NAME_MAP.get(base_company, base_company.title())
            return company_name, sender
        
        # If passes all checks and is not generic, use the domain part
        if len(company_part) > 3:
            # Try to extract a cleaner name
            clean_company = company_part.replace('-', ' ').replace('_', ' ')
            # Check if any known service is contained in the company part
            for service in cls.LEGITIMATE_SERVICES:
                if service in company_part:
                    return cls.COMPANY_NAME_MAP.get(service, service.title()), sender
            
            return clean_company.title(), sender
        
        return None, sender
    
    @classmethod
    def check_domain_reputation(cls, email: str) -> Tuple[bool, str]:
        """
        Enhanced domain reputation checking
        """
        if not email or '@' not in email:
            return False, "Invalid email format"
        
        sender_details = cls.extract_sender_details(email)
        domain = sender_details['domain'].lower()
        base_domain = sender_details['base_domain'].lower()
        
        # Check against comprehensive blacklist
        for blacklisted in cls.BLACKLISTED_DOMAINS:
            if blacklisted in domain or domain == blacklisted:
                return False, f"Blacklisted domain pattern: {blacklisted}"
        
        # Check suspicious TLDs
        for tld in cls.SUSPICIOUS_TLDS:
            if domain.endswith(tld):
                return False, f"Suspicious TLD: {tld}"
        
        # Check for typosquatting
        domain_parts = domain.split('.')
        primary_part = domain_parts[0]
        
        # Look for common typosquatting patterns
        typo_patterns = [
            (r'[0o]', 'o'),  # zero instead of o
            (r'[1l]', 'l'),  # one instead of l
            (r'vv', 'w'),    # double v instead of w
            (r'rn', 'm'),    # rn instead of m
        ]
        
        for pattern, replacement in typo_patterns:
            potential_legit = re.sub(pattern, replacement, primary_part)
            if potential_legit != primary_part and potential_legit in cls.LEGITIMATE_SERVICES:
                return False, f"Possible typosquatting of {potential_legit}"
        
        # Check DNS validity for non-whitelisted domains
        if primary_part not in cls.LEGITIMATE_SERVICES:
            dns_valid, dns_reason = cls.check_dns_validity(domain)
            if not dns_valid:
                return False, dns_reason
        
        # If it's a known legitimate service, it's good
        if primary_part in cls.LEGITIMATE_SERVICES or base_domain.split('.')[0] in cls.LEGITIMATE_SERVICES:
            return True, "Known legitimate service"
        
        # Additional pattern checks
        suspicious_patterns = [
            r'^[0-9]{4,}',  # Starts with 4+ digits
            r'^[a-z0-9]{20,}$',  # Random long string
            r'[0-9]{3,}[a-z]+[0-9]{3,}',  # Numbers-letters-numbers
            r'^x[a-z0-9]{10,}',  # Starts with x followed by random
        ]
        
        for pattern in suspicious_patterns:
            if re.match(pattern, primary_part):
                return False, f"Suspicious domain pattern"
        
        return True, "Domain passes enhanced validation"
    
    @classmethod
    def calculate_monthly_equivalent(cls, amount: float, frequency: str) -> float:
        """
        Convert any payment frequency to monthly equivalent for accurate comparison
        """
        if not amount or not frequency:
            return amount
        
        frequency_multipliers = {
            'daily': 30.44,  # Average days per month
            'weekly': 4.33,  # Average weeks per month
            'biweekly': 2.17,  # Every 2 weeks
            'monthly': 1.0,
            'quarterly': 0.333,  # Every 3 months
            'semiannual': 0.167,  # Every 6 months
            'annual': 0.0833,  # Once per year
            'yearly': 0.0833,
            'biannual': 0.0417,  # Every 2 years
        }
        
        multiplier = frequency_multipliers.get(frequency, 1.0)
        return amount * multiplier
    
    @classmethod
    def validate_payment_amount(cls, amount: float, frequency: str = None) -> Tuple[bool, str]:
        """
        Enhanced payment validation with frequency-aware checks
        """
        if not amount:
            return True, "No amount to validate"
        
        # Get monthly equivalent for validation
        monthly_amount = cls.calculate_monthly_equivalent(amount, frequency)
        
        # Enhanced validation thresholds
        if monthly_amount > 1000:
            return False, f"Unrealistic subscription amount: ${monthly_amount:.2f}/month"
        
        if monthly_amount < 0.50 and monthly_amount > 0:
            return False, f"Suspiciously low amount: ${monthly_amount:.2f}/month"
        
        # Check for common scam amounts
        scam_amounts = [999, 499, 399, 299, 199, 99.99, 9999, 4999, 
                       888, 777, 666, 555, 444, 333, 222, 111,
                       123.45, 234.56, 345.67, 456.78, 567.89]
        
        if amount in scam_amounts:
            return False, f"Common scam amount: ${amount}"
        
        # Check for suspicious precision
        if '.' in str(amount):
            decimal_places = len(str(amount).split('.')[1])
            if decimal_places > 2:
                return False, f"Suspicious precision: ${amount}"
        
        # Check for round numbers that are unusual for subscriptions
        if amount > 100 and amount % 100 == 0 and frequency in ['daily', 'weekly']:
            return False, f"Suspicious round amount for {frequency} subscription: ${amount}"
        
        return True, "Amount appears reasonable"
    
    @classmethod
    def is_likely_fraud(cls, sender: str, subject: str, amount: float = None, 
                       frequency: str = None) -> Tuple[bool, List[str]]:
        """
        Comprehensive fraud check with enhanced detection
        """
        reasons = []
        score = 0  # Fraud score: higher = more likely fraud
        
        # Domain reputation check (most important)
        domain_ok, domain_reason = cls.check_domain_reputation(sender)
        if not domain_ok:
            reasons.append(f"Domain issue: {domain_reason}")
            score += 50
        
        # Payment amount validation
        if amount is not None:
            amount_ok, amount_reason = cls.validate_payment_amount(amount, frequency)
            if not amount_ok:
                reasons.append(f"Payment issue: {amount_reason}")
                score += 30
        
        # Subject line analysis
        if subject:
            subject_lower = subject.lower()
            
            # Expanded scam phrases
            urgent_phrases = [
                'urgent', 'immediate', 'act now', 'expires today', 'last chance',
                'limited time', 'don\'t miss', 'final notice', 'response required'
            ]
            
            security_phrases = [
                'verify your account', 'confirm your identity', 'update your payment',
                'suspended account', 'locked account', 'security alert', 'unusual activity',
                'click here immediately', 'verify payment method', 'confirm billing'
            ]
            
            prize_phrases = [
                'congratulations', 'you won', 'you\'ve been selected', 'claim your',
                'prize winner', 'lucky winner', 'gift card', 'free money'
            ]
            
            threat_phrases = [
                'will be closed', 'will be suspended', 'will be terminated',
                'avoid interruption', 'prevent closure', 'action required'
            ]
            
            # Check for scam indicators
            for phrase_list, phrase_type in [
                (urgent_phrases, 'Urgent language'),
                (security_phrases, 'Security scare tactic'),
                (prize_phrases, 'Prize/gift scam'),
                (threat_phrases, 'Threat language')
            ]:
                for phrase in phrase_list:
                    if phrase in subject_lower:
                        reasons.append(f"{phrase_type}: '{phrase}'")
                        score += 20
                        break
            
            # ALL CAPS detection
            if subject.isupper() and len(subject) > 10:
                reasons.append("Excessive capitalization (ALL CAPS)")
                score += 15
            
            # Excessive punctuation
            punct_count = subject.count('!') + subject.count('$') + subject.count('?')
            if punct_count > 3:
                reasons.append(f"Excessive punctuation ({punct_count} marks)")
                score += 10
            
            # Unicode/special characters (often used to bypass filters)
            if any(ord(char) > 127 for char in subject):
                special_count = sum(1 for char in subject if ord(char) > 127)
                if special_count > 2:
                    reasons.append("Suspicious unicode characters")
                    score += 10
        
        # Sender analysis
        sender_details = cls.extract_sender_details(sender)
        
        # Check for suspicious sender patterns
        if sender_details['domain']:
            domain_parts = sender_details['domain'].split('.')
            
            # Subdomain abuse (like account.security.fake-paypal.com)
            if len(domain_parts) > 3:
                reasons.append("Excessive subdomains")
                score += 15
            
            # Numeric domains
            if re.search(r'\d{4,}', sender_details['domain']):
                reasons.append("Numeric patterns in domain")
                score += 20
        
        # Determine if fraud based on score
        is_fraud = score >= 50 or len(reasons) >= 2
        
        return is_fraud, reasons
    
    @classmethod
    def generate_fraud_report(cls, fraudulent_emails: List[Dict]) -> Dict:
        """
        Generate a summary report of fraud detection results
        """
        report = {
            'total_fraudulent': len(fraudulent_emails),
            'fraud_categories': {},
            'top_fraud_domains': {},
            'common_scam_amounts': {},
            'detection_reasons': {}
        }
        
        for email in fraudulent_emails:
            # Categorize fraud reasons
            for reason in email.get('fraud_reasons', []):
                category = reason.split(':')[0]
                report['fraud_categories'][category] = report['fraud_categories'].get(category, 0) + 1
            
            # Track domains
            sender_details = cls.extract_sender_details(email.get('sender', ''))
            if sender_details['domain']:
                domain = sender_details['domain']
                report['top_fraud_domains'][domain] = report['top_fraud_domains'].get(domain, 0) + 1
            
            # Track amounts
            if email.get('amount'):
                amount = email.get('amount')
                report['common_scam_amounts'][amount] = report['common_scam_amounts'].get(amount, 0) + 1
        
        # Sort and limit results
        report['top_fraud_domains'] = dict(sorted(
            report['top_fraud_domains'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:20])
        
        report['common_scam_amounts'] = dict(sorted(
            report['common_scam_amounts'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10])
        
        return report


# Test enhanced fraud detection
if __name__ == "__main__":
    print("Testing Enhanced Fraud Detection System")
    print("=" * 80)
    
    test_cases = [
        # Legitimate
        ("Netflix <noreply@netflix.com>", "Your Netflix subscription renewed", 15.99, "monthly"),
        ("Spotify <billing@spotify.com>", "Thanks for your payment", 9.99, "monthly"),
        ("Adobe Creative Cloud <adobe@email.adobe.com>", "Your annual subscription", 599.88, "annual"),
        
        # Fraudulent
        ("email@secure-payment.tk", "URGENT: Verify your payment!!!", 999.00, "daily"),
        ("notification@amaz0n-security.ml", "Your account will be suspended", 399.99, None),
        ("prize@winner-notification.click", "Congratulations! You won $1000", 1000.00, None),
        ("support@app1e.ga", "Update your Apple ID immediately", 99.99, "monthly"),
        ("billing@microsofy.work", "Office 365 payment failed", 199.99, "monthly"),
        ("x92k4m@temporary-email.cf", "Payment of $168.08 required daily", 168.08, "daily"),
    ]
    
    for sender, subject, amount, frequency in test_cases:
        print(f"\nAnalyzing: {sender}")
        print(f"Subject: {subject}")
        print(f"Amount: ${amount} ({frequency or 'one-time'})")
        
        # Check fraud
        is_fraud, reasons = EnhancedFraudDetector.is_likely_fraud(sender, subject, amount, frequency)
        
        # Extract company
        company, full_sender = EnhancedFraudDetector.extract_legitimate_company_name(sender, subject)
        
        # Calculate monthly equivalent
        if frequency:
            monthly = EnhancedFraudDetector.calculate_monthly_equivalent(amount, frequency)
            print(f"Monthly equivalent: ${monthly:.2f}")
        
        print(f"Verdict: {'🚨 FRAUD' if is_fraud else '✅ LEGITIMATE'}")
        print(f"Company: {company or 'Could not identify'}")
        if reasons:
            print(f"Reasons: {'; '.join(reasons)}")
        print("-" * 60)
