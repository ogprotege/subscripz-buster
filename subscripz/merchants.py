"""Turn a sender + subject into a stable merchant identity."""

from __future__ import annotations

import re
from typing import Optional, Tuple

# Longer phrases first so "youtube tv" wins over "youtube".
KNOWN_PHRASES: Tuple[Tuple[str, str], ...] = (
    ("amazon prime", "Amazon Prime"),
    ("apple music", "Apple Music"),
    ("apple tv+", "Apple TV"),
    ("apple tv", "Apple TV"),
    ("apple one", "Apple"),
    ("youtube tv", "YouTube TV"),
    ("youtube premium", "YouTube Premium"),
    ("hbo max", "Max"),
    ("disney plus", "Disney+"),
    ("disney+", "Disney+"),
    ("paramount plus", "Paramount+"),
    ("paramount+", "Paramount+"),
    ("microsoft 365", "Microsoft 365"),
    ("office 365", "Microsoft 365"),
    ("github copilot", "GitHub Copilot"),
    ("adobe creative", "Adobe"),
    ("creative cloud", "Adobe"),
    ("google one", "Google One"),
    ("google workspace", "Google Workspace"),
    ("icloud+", "iCloud"),
    ("new york times", "New York Times"),
    ("ny times", "New York Times"),
    ("wall street journal", "WSJ"),
    ("washington post", "Washington Post"),
)

KNOWN_DOMAINS = {
    "netflix.com": "Netflix",
    "spotify.com": "Spotify",
    "apple.com": "Apple",
    "icloud.com": "iCloud",
    "amazon.com": "Amazon",
    "amazon.co.uk": "Amazon",
    "amazon.ca": "Amazon",
    "primevideo.com": "Amazon Prime",
    "hulu.com": "Hulu",
    "disney.com": "Disney+",
    "disneyplus.com": "Disney+",
    "hbo.com": "Max",
    "hbomax.com": "Max",
    "max.com": "Max",
    "paramount.com": "Paramount+",
    "paramountplus.com": "Paramount+",
    "peacocktv.com": "Peacock",
    "youtube.com": "YouTube",
    "youtubetv.com": "YouTube TV",
    "google.com": "Google",
    "adobe.com": "Adobe",
    "microsoft.com": "Microsoft",
    "office.com": "Microsoft 365",
    "github.com": "GitHub",
    "gitlab.com": "GitLab",
    "dropbox.com": "Dropbox",
    "evernote.com": "Evernote",
    "notion.so": "Notion",
    "notion.com": "Notion",
    "slack.com": "Slack",
    "zoom.us": "Zoom",
    "linkedin.com": "LinkedIn",
    "medium.com": "Medium",
    "substack.com": "Substack",
    "patreon.com": "Patreon",
    "onlyfans.com": "OnlyFans",
    "nytimes.com": "New York Times",
    "wsj.com": "WSJ",
    "washingtonpost.com": "Washington Post",
    "economist.com": "The Economist",
    "spotify.net": "Spotify",
    "netflix.net": "Netflix",
    "audible.com": "Audible",
    "kindle.com": "Kindle",
    "openai.com": "OpenAI",
    "anthropic.com": "Anthropic",
    "cursor.com": "Cursor",
    "cursor.sh": "Cursor",
    "figma.com": "Figma",
    "canva.com": "Canva",
    "grammarly.com": "Grammarly",
    "1password.com": "1Password",
    "lastpass.com": "LastPass",
    "nordvpn.com": "NordVPN",
    "expressvpn.com": "ExpressVPN",
    "doordash.com": "DoorDash",
    "uber.com": "Uber",
    "lyft.com": "Lyft",
    "airbnb.com": "Airbnb",
    "paypal.com": "PayPal",
    "venmo.com": "Venmo",
    "stripe.com": "Stripe",
    "shopify.com": "Shopify",
    "cloudflare.com": "Cloudflare",
    "digitalocean.com": "DigitalOcean",
    "heroku.com": "Heroku",
    "vercel.com": "Vercel",
    "planetfitness.com": "Planet Fitness",
    "peloton.com": "Peloton",
    "headspace.com": "Headspace",
    "calm.com": "Calm",
    "duolingo.com": "Duolingo",
    "coursera.org": "Coursera",
    "udemy.com": "Udemy",
    "masterclass.com": "MasterClass",
}

# Hosts that send other people's receipts. Identity comes from the subject.
ESP_DOMAINS = {
    "amazonses.com",
    "sendgrid.net",
    "sendgrid.com",
    "mailgun.org",
    "mailgun.com",
    "mailchimp.com",
    "mandrillapp.com",
    "postmarkapp.com",
    "sparkpostmail.com",
    "exacttarget.com",
    "salesforce.com",
    "sendinblue.com",
    "brevo.com",
    "constantcontact.com",
    "mailjet.com",
}

CONSUMER_INBOXES = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "ymail.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "msn.com",
    "icloud.com",
    "me.com",
    "mac.com",
    "aol.com",
    "proton.me",
    "protonmail.com",
    "icloud.com",
}

MAILISH_LABELS = {
    "mail",
    "email",
    "e",
    "em",
    "info",
    "noreply",
    "no-reply",
    "donotreply",
    "do-not-reply",
    "notifications",
    "notification",
    "notify",
    "billing",
    "receipts",
    "receipt",
    "invoices",
    "invoice",
    "updates",
    "update",
    "news",
    "newsletter",
    "support",
    "hello",
    "team",
    "go",
    "eml",
    "mg",
    "m",
    "smtp",
    "bounce",
    "bounces",
}

GENERIC_DISPLAY = {
    "mail delivery subsystem",
    "mail delivery system",
    "noreply",
    "no-reply",
    "do not reply",
    "notifications",
    "notification",
    "support",
    "customer support",
    "billing",
    "account",
    "accounts",
    "info",
}

SENDER_RE = re.compile(r"^\s*(?P<name>.*?)\s*<\s*(?P<addr>[^>]+)\s*>\s*$")
DOMAIN_RE = re.compile(r"@([^>\s]+)")


def parse_sender(sender: str) -> Tuple[str, str]:
    """Return (display_name, address)."""
    if not sender:
        return "", ""
    match = SENDER_RE.match(sender)
    if match:
        return match.group("name").strip().strip('"'), match.group("addr").strip().lower()
    if "@" in sender:
        return "", sender.strip().lower()
    return sender.strip(), ""


def _registrable(domain: str) -> str:
    parts = [p for p in domain.lower().strip(".").split(".") if p]
    if len(parts) >= 3 and parts[-2] in {"co", "com", "net", "org", "ac"}:
        return ".".join(parts[-3:])
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return domain.lower()


def _strip_mailish(domain: str) -> str:
    parts = domain.lower().split(".")
    while len(parts) > 2 and parts[0] in MAILISH_LABELS:
        parts = parts[1:]
    return ".".join(parts)


def _from_subject(text: str) -> Optional[str]:
    lowered = text.lower()
    for phrase, name in KNOWN_PHRASES:
        if phrase in lowered:
            return name
    # Whole-word brand tokens from known domains.
    brands = sorted({name for name in KNOWN_DOMAINS.values()}, key=len, reverse=True)
    for name in brands:
        if re.search(rf"\b{re.escape(name.lower())}\b", lowered):
            return name
    return None


def identify_merchant(sender: str, subject: str = "", snippet: str = "") -> Optional[Tuple[str, str]]:
    """
    Return (stable_key, display_name) or None if this is not a merchant.
    """
    display, address = parse_sender(sender)
    text = f"{subject} {snippet} {display}"
    subject_guess = _from_subject(text)

    domain = ""
    match = DOMAIN_RE.search(address or sender)
    if match:
        domain = match.group(1).lower().rstrip(".")

    if domain in ESP_DOMAINS or _registrable(domain) in ESP_DOMAINS:
        if subject_guess:
            return subject_guess.lower(), subject_guess
        return None

    if domain in CONSUMER_INBOXES:
        if subject_guess:
            return subject_guess.lower(), subject_guess
        return None

    if domain:
        cleaned = _strip_mailish(domain)
        registrable = _registrable(cleaned)
        if registrable in KNOWN_DOMAINS:
            name = KNOWN_DOMAINS[registrable]
            return name.lower(), name
        if cleaned in KNOWN_DOMAINS:
            name = KNOWN_DOMAINS[cleaned]
            return name.lower(), name
        # Walk parent domains: email.adobe.com → adobe.com
        parts = cleaned.split(".")
        for i in range(len(parts) - 1):
            candidate = ".".join(parts[i:])
            if candidate in KNOWN_DOMAINS:
                name = KNOWN_DOMAINS[candidate]
                return name.lower(), name

        if subject_guess:
            return subject_guess.lower(), subject_guess

        label = registrable.split(".")[0]
        if label in MAILISH_LABELS or len(label) < 3:
            return None
        return label, label.replace("-", " ").title()

    if subject_guess:
        return subject_guess.lower(), subject_guess

    cleaned_display = display.strip().strip('"')
    if cleaned_display and cleaned_display.lower() not in GENERIC_DISPLAY:
        key = re.sub(r"[^a-z0-9]+", "", cleaned_display.lower())
        if len(key) >= 3:
            return key, cleaned_display
    return None
