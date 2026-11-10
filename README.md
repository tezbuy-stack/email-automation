# Email Automation

Send personalised emails to a list of recipients from Python — with a safe demo mode that previews everything before anything is sent.

## Features

- **Safe demo mode (default):** previews every email on screen and sends nothing.
- **Personalised messages:** reads recipients from a CSV file and fills in each person's name from a template (`{name}` placeholder).
- **Real sending with `--send`:** sends via any SMTP server (Gmail, Outlook, or your own provider).
- **Credentials only via environment variables:** no password is ever written in the code.
- **Input validation:** skips rows with a missing name/email or a badly formed address, and warns you about them.
- **Graceful error handling:** a failed send for one recipient does not stop the rest, and connection problems are reported clearly.
- **Standard library only:** no packages to install.

## Requirements

- Python 3.8 or newer (tested on Python 3.12)
- No external packages — everything used is in the Python standard library (`smtplib`, `email`, `csv`, `os`)

## Installation

```bash
git clone https://github.com/<your-username>/email-automation.git
cd email-automation
```

That's it — there is nothing to install. (Replace `<your-username>` with your own GitHub username.)

## Usage

### Demo mode (default — sends nothing)

```bash
python3 email_automation.py
```

or explicitly:

```bash
python3 email_automation.py --dry-run
```

Sample output:

```
============================================================
DEMO MODE — no emails will be sent.
============================================================
Recipients found: 3
Subject: Hello {name} — a quick update from our team

------------------------------------------------------------
To: alice@example.com  (name: Alice)
Subject: Hello Alice — a quick update from our team

Hi Alice,

This is a sample email sent with the Email Automation project.
...
------------------------------------------------------------
Done. 3 email(s) previewed, 0 sent.
To send for real, run:  python3 email_automation.py --send
```

### Sending for real

1. Set your SMTP credentials as environment variables (see [SMTP configuration](#smtp-configuration) below).
2. Run:

```bash
python3 email_automation.py --send
```

The script prints a clear warning, asks you to type `YES` to confirm, and only then sends the emails.

### Customising the recipients and message

- Edit `recipients.csv` — one row per person, columns `name,email`.
- Edit `email_template.txt` — the first line must be `Subject: ...`, the rest is the body. Use `{name}` anywhere you want the recipient's name to appear.

## SMTP configuration

You need an SMTP server to send real emails. Any provider works; Gmail is the most common example.

### Step 1 — Get your SMTP details

**Gmail:**
- Host: `smtp.gmail.com`, Port: `587`
- You cannot use your normal Google password. Create an **App Password**: Google Account → Security → 2-Step Verification (turn it on) → App passwords → generate one for "Mail". Use that 16-character password as `SMTP_PASS`.

**Other providers:** use the SMTP host and port from your provider's help pages (for example Outlook uses `smtp.office365.com`, port `587`).

### Step 2 — Set the environment variables

```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=you@example.com
export SMTP_PASS=your-app-password
export FROM_EMAIL=you@example.com
```

| Variable | What it is |
|---|---|
| `SMTP_HOST` | Your provider's SMTP server address |
| `SMTP_PORT` | SMTP port — usually `587` (TLS) |
| `SMTP_USER` | The username you log in with (usually your email) |
| `SMTP_PASS` | Your password or app password |
| `FROM_EMAIL` | The address shown as the sender |

### Step 3 — Send

```bash
python3 email_automation.py --send
```

## Safety notes

- **Demo mode is the default.** Running the script with no flags never sends anything.
- **Credentials only via environment variables.** Never put a password in the code, and never commit a `.env` file — this project's `.gitignore` already excludes `.env`.
- **Test with your own address first.** Before mailing a real list, put only your own email in `recipients.csv` and send a test.
- **Respect the recipients.** Only email people who expect mail from you, and follow anti-spam rules in your country.

## Project structure

```
email-automation/
├── email_automation.py   # the script (standard library only)
├── recipients.csv        # sample recipients (name, email)
├── email_template.txt    # sample message (Subject line + {name} placeholder)
├── requirements.txt      # no external dependencies
├── .gitignore            # keeps .env, caches and virtualenvs out of git
└── README.md             # this file
```

## License

MIT — see the [LICENSE](LICENSE) file. (If you publish this repository, add a standard MIT LICENSE file with your name and the year.)
