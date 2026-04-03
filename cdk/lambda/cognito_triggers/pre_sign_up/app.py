import json
import os


def handler(event, context):
    allowed_domains_str = os.environ.get("ALLOWED_SIGN_UP_EMAIL_DOMAINS_STR", "[]")
    allowed_domains = json.loads(allowed_domains_str)

    if not allowed_domains:
        return event

    email = event["request"]["userAttributes"].get("email", "")

    if not email or "@" not in email:
        raise Exception("Invalid email address")

    domain = email.split("@")[1].lower()

    if domain not in allowed_domains:
        raise Exception(f"Sign up not allowed with email domain: {domain}")

    return event
