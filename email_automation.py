"""
Email Automation — send personalised emails to a list of recipients.

SAFE BY DEFAULT
---------------
Running this script with no arguments starts DEMO MODE: it reads the
recipients and the template, prints exactly what *would* be sent to each
person, and sends NOTHING. This is the default on purpose — you can
preview everything before a single email leaves your computer.

To send for real you must do two things:
    1. Pass the --send flag.
    2. Provide your SMTP credentials as environment variables
       (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL).

Credentials are NEVER written in this file. Never put a password in your
code, and never commit a file that contains one.

Usage:
    python3 email_automation.py            # demo mode (default, sends nothing)
    python3 email_automation.py --dry-run  # same as demo mode, explicit
    python3 email_automation.py --send     # real send (needs env vars set)
    python3 email_automation.py --help     # show this help text

Standard library only — no packages to install.
"""

import argparse
import csv
import os
import re
import smtplib
import sys
from email.message import EmailMessage

# Default file names (looked for in the same folder as this script).
RECIPIENTS_FILE = "recipients.csv"
TEMPLATE_FILE = "email_template.txt"

# A very small sanity check for email addresses. It is not a full
# validator — it just catches obvious typos like a missing "@" or ".".
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def load_recipients(path):
    """Read recipients from a CSV file with columns: name,email.

    Returns a list of dicts, e.g. [{"name": "Alice", "email": "alice@example.com"}].
    Rows with a missing name or email, or a badly formed address, are
    skipped with a warning instead of crashing the whole run.
    """
    recipients = []
    with open(path, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row_number, row in enumerate(reader, start=2):  # line 1 is the header
            name = (row.get("name") or "").strip()
            email = (row.get("email") or "").strip()
            if not name or not email:
                print(f"Warning: row {row_number} is missing a name or email — skipped.")
                continue
            if not EMAIL_PATTERN.match(email):
                print(f"Warning: '{email}' (row {row_number}) is not a valid "
                      f"email address — skipped.")
                continue
            recipients.append({"name": name, "email": email})
    return recipients


def load_template(path):
    """Read the email template.

    The first line must look like:  Subject: Your subject here
    Everything after it is the message body. The body may contain
    {name}, which is replaced with each recipient's name.

    Returns (subject, body) as strings.
    """
    with open(path, encoding="utf-8") as template_file:
        lines = template_file.read().splitlines()

    if not lines or not lines[0].lower().startswith("subject:"):
        raise ValueError(
            f"Template '{path}' must start with a 'Subject: ...' line."
        )

    subject = lines[0][len("Subject:"):].strip()
    # Skip the blank line that usually follows the subject line.
    body_lines = lines[1:]
    if body_lines and body_lines[0] == "":
        body_lines = body_lines[1:]
    body = "\n".join(body_lines)
    return subject, body


def personalise(text, name):
    """Replace the {name} placeholder with the recipient's name."""
    return text.replace("{name}", name)


def build_message(subject, body, recipient, from_email):
    """Build a ready-to-send EmailMessage for one recipient."""
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = recipient["email"]
    message.set_content(body)
    return message


def demo_mode(recipients, subject, body):
    """Print what WOULD be sent to each recipient. Sends nothing."""
    print("=" * 60)
    print("DEMO MODE — no emails will be sent.")
    print("=" * 60)
    print(f"Recipients found: {len(recipients)}")
    print(f"Subject: {subject}")
    print()

    for recipient in recipients:
        personalised_subject = personalise(subject, recipient["name"])
        personalised_body = personalise(body, recipient["name"])
        print("-" * 60)
        print(f"To: {recipient['email']}  (name: {recipient['name']})")
        print(f"Subject: {personalised_subject}")
        print()
        print(personalised_body)
        print()

    print("-" * 60)
    print(f"Done. {len(recipients)} email(s) previewed, 0 sent.")
    print("To send for real, run:  python3 email_automation.py --send")
    print("(You will also need the SMTP_* environment variables set.)")


def get_smtp_settings():
    """Read SMTP settings from environment variables.

    Required: SMTP_HOST, SMTP_USER, SMTP_PASS, FROM_EMAIL.
    Optional: SMTP_PORT (defaults to 587, the standard TLS port).

    Returns a dict, or None (after printing a helpful error) if
    something required is missing.
    """
    settings = {
        "host": os.environ.get("SMTP_HOST", "").strip(),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": os.environ.get("SMTP_USER", "").strip(),
        "password": os.environ.get("SMTP_PASS", ""),
        "from_email": os.environ.get("FROM_EMAIL", "").strip(),
    }
    missing = [key for key in ("host", "user", "password", "from_email")
               if not settings[key]]
    if missing:
        var_names = {"host": "SMTP_HOST", "user": "SMTP_USER",
                     "password": "SMTP_PASS", "from_email": "FROM_EMAIL"}
        print("Error: cannot send — these environment variables are not set:")
        for key in missing:
            print(f"  - {var_names[key]}")
        print()
        print("Set them in your terminal first, for example:")
        print("  export SMTP_HOST=smtp.gmail.com")
        print("  export SMTP_PORT=587")
        print("  export SMTP_USER=you@example.com")
        print("  export SMTP_PASS=your-app-password")
        print("  export FROM_EMAIL=you@example.com")
        print("Then run:  python3 email_automation.py --send")
        return None
    return settings


def send_all(recipients, subject, body, settings):
    """Send the personalised email to every recipient via SMTP.

    Connects once, sends each email, and reports success/failure per
    recipient. A failure for one person does not stop the rest.
    Returns (sent_count, failed_count).
    """
    print("=" * 60)
    print("WARNING: REAL SEND MODE")
    print(f"You are about to send {len(recipients)} email(s) from "
          f"{settings['from_email']}.")
    print("=" * 60)
    answer = input("Type YES to continue, anything else to cancel: ").strip()
    if answer != "YES":
        print("Cancelled. No emails were sent.")
        return 0, 0

    sent = 0
    failed = 0
    try:
        # starttls() upgrades the plain connection to an encrypted one.
        with smtplib.SMTP(settings["host"], settings["port"], timeout=30) as server:
            server.starttls()
            server.login(settings["user"], settings["password"])
            for recipient in recipients:
                personalised_subject = personalise(subject, recipient["name"])
                personalised_body = personalise(body, recipient["name"])
                message = build_message(personalised_subject, personalised_body,
                                        recipient, settings["from_email"])
                try:
                    server.send_message(message)
                    print(f"Sent to {recipient['email']}")
                    sent += 1
                except smtplib.SMTPException as error:
                    print(f"Failed to send to {recipient['email']}: {error}")
                    failed += 1
    except (smtplib.SMTPException, OSError) as error:
        print(f"Error: could not connect to the mail server: {error}")
        print("Check SMTP_HOST / SMTP_PORT and your internet connection.")
        return sent, len(recipients) - sent

    print()
    print(f"Done. Sent: {sent}, failed: {failed}.")
    return sent, failed


def parse_args(argv):
    """Parse command-line flags."""
    parser = argparse.ArgumentParser(
        description="Send personalised emails from a CSV list. "
                    "Demo mode (default) only previews — nothing is sent."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--send", action="store_true",
                       help="actually send the emails (needs SMTP_* env vars)")
    group.add_argument("--dry-run", action="store_true",
                       help="preview only, send nothing (same as the default)")
    return parser.parse_args(argv)


def main(argv=None):
    """Load the data, then preview (default) or send (--send)."""
    args = parse_args(argv)

    # Find the data files next to this script, wherever it is run from.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    recipients_path = os.path.join(base_dir, RECIPIENTS_FILE)
    template_path = os.path.join(base_dir, TEMPLATE_FILE)

    try:
        recipients = load_recipients(recipients_path)
    except FileNotFoundError:
        print(f"Error: could not find '{RECIPIENTS_FILE}'. "
              f"Make sure it is in the same folder as this script.")
        return 1

    if not recipients:
        print(f"No valid recipients found in '{RECIPIENTS_FILE}'. "
              f"Nothing to do.")
        return 1

    try:
        subject, body = load_template(template_path)
    except FileNotFoundError:
        print(f"Error: could not find '{TEMPLATE_FILE}'. "
              f"Make sure it is in the same folder as this script.")
        return 1
    except ValueError as error:
        print(f"Error: {error}")
        return 1

    if args.send:
        settings = get_smtp_settings()
        if settings is None:
            return 1
        send_all(recipients, subject, body, settings)
    else:
        demo_mode(recipients, subject, body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
