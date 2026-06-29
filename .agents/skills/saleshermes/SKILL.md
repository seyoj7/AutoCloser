---
name: AutoCloser
description: >
  AutoCloser is an autonomous B2B sales pipeline agent. Given a CSV of leads,
  it researches each company's website with Playwright, generates hyper-personalized
  cold emails via NVIDIA Nemotron, sends them over Gmail SMTP, monitors the inbox
  for replies, classifies sentiment, dispatches Calendly meeting links to warm leads,
  and creates & delivers Stripe invoices — updating lead status in the CSV at every step.
  Trigger this skill when the user asks to run, fix, extend, or debug any part of
  the AutoCloser outreach pipeline (research, email, scheduling, billing, lead status).
---

# AutoCloser — Autonomous B2B Sales Agent

## Overview

AutoCloser is a standalone Hermes-pattern agent powered by **NVIDIA Nemotron**.
The orchestrator (`scripts/main.py`) feeds Nemotron a system prompt and a set
of tool definitions. Nemotron then **autonomously decides** which tool to call,
reads the result, and picks the next action — looping until every lead has been
processed. No hardcoded branching; the model drives the entire pipeline.

```
main.py starts → Nemotron reasons → picks a tool → executes it → sees result
              → picks next tool → ... → "CYCLE COMPLETE" → sleeps 15 min → repeat
```

Run it with:

```bash
cd <project_root>
python scripts/main.py
```

---

## Project Layout

```
Autocloser/
├── .env                    # Secret env vars (never commit)
├── .env.example            # Template for required env vars
├── requirements.txt        # Python dependencies
├── data/
│   ├── leads.csv           # Lead database (status tracked here)
│   └── services.csv        # Billable services menu (Stripe)
├── scripts/
│   ├── main.py             # Agent loop — Nemotron + tool executor
│   ├── csv_reader.py       # Load leads, update statuses, load services
│   ├── research.py         # Playwright scrape + Nemotron summarization
│   ├── email_agent.py      # Email generation, SMTP send, IMAP reply check
│   ├── scheduler.py        # Lead qualification + Calendly scheduling
│   └── billing.py          # Stripe invoice creation & payment polling
```

---

## Required Environment Variables

Set these in `.env` (copy from `.env.example`):

| Variable            | Purpose                                        |
|---------------------|------------------------------------------------|
| `NVIDIA_API_KEY`    | NVIDIA NIM API key for Nemotron                |
| `NVIDIA_BASE_URL`   | Base URL for NVIDIA NIM API                    |
| `SMTP_USER`         | Gmail address for sending/receiving email      |
| `SMTP_PASSWORD`     | Gmail App Password (not account password)      |
| `STRIPE_SECRET_KEY` | Stripe secret key for invoice creation         |
| `CALENDLY_LINK`     | Public Calendly booking URL                    |
| `CALENDLY_API_KEY`  | Calendly API key                               |
| `SENDER_NAME`       | Your name (used in email signatures)           |
| `COMPANY_NAME`      | Your company name (used in email copy)         |

> **Gmail SMTP Note**: You must enable 2FA on your Google account and generate a
> dedicated **App Password** at https://myaccount.google.com/apppasswords.
> Using your normal password will cause authentication failures.

---

## Dependencies

Install all dependencies with:

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

| Package          | Version    | Purpose                                    |
|------------------|------------|--------------------------------------------|
| `openai`         | >= 1.0.0   | OpenAI-compatible client for Nemotron API  |
| `python-dotenv`  | >= 1.0.0   | Load env vars from `.env`                  |
| `playwright`     | >= 1.40.0  | Headless browser for website research      |
| `stripe`         | >= 7.0.0   | Stripe invoice creation & payment tracking |
| `requests`       | >= 2.31.0  | HTTP requests (Calendly API, etc.)         |

---

## How the Agent Works

### Nemotron as the Brain

**Model:** `nvidia/llama-3.3-nemotron-super-49b-v1`

`main.py` sends Nemotron a system prompt describing the full pipeline workflow
plus a list of tool definitions. It then calls the model with `tool_choice="auto"`,
meaning Nemotron autonomously:

1. Decides which tool to call next
2. Provides the arguments
3. Receives the JSON result
4. Reasons about the next step
5. Repeats until all leads are processed

There is **no hardcoded if/else branching** for the pipeline — Nemotron decides
the order and logic at runtime.

### Tools Exposed to Nemotron

| Tool                  | Description                                                  |
|-----------------------|--------------------------------------------------------------|
| `load_leads`          | Load all leads and their current status from CSV             |
| `research_company`    | Scrape website with Playwright + summarize with Nemotron     |
| `generate_email`      | Write a personalized cold email using research intel         |
| `generate_followup`   | Write a follow-up addressing a lead's specific question      |
| `send_email`          | Send email via Gmail SMTP (auto-threads replies)             |
| `check_replies`       | Poll Gmail IMAP for replies from a specific lead             |
| `analyze_reply`       | Classify reply sentiment with Nemotron                       |
| `qualify_lead`        | Determine if a lead is worth pursuing                        |
| `schedule_meeting`    | Send Calendly booking link to a qualified lead               |
| `confirm_meeting`     | Human-in-the-loop: confirm meeting completion                |
| `create_invoice`      | Present service menu, create & send Stripe invoice           |
| `check_payment_status`| Poll Stripe for invoice payment status                       |
| `mark_lead_status`    | Persist lead stage to CSV                                    |

---

## Lead Status Flow

```
new → emailed → meeting_sent → meeting_booked → meeting_completed → invoiced → closed_won
         ↓
    followup_sent → (same as emailed)
         ↓
    not_interested (dead end, unless they reply again)
```

### Per-Status Behavior

| Status              | What Nemotron Does                                            |
|---------------------|---------------------------------------------------------------|
| `new`               | Research → generate email → send → mark `emailed`            |
| `emailed`           | Check replies → classify → follow-up or schedule meeting      |
| `followup_sent`     | Check replies → classify → qualify → schedule or stop         |
| `meeting_sent`      | Check replies → if confirmed, mark `meeting_booked`           |
| `meeting_booked`    | Ask operator if meeting done → mark `meeting_completed`       |
| `meeting_completed` | Create Stripe invoice → mark `invoiced`                       |
| `invoiced`          | Check Stripe payment → if paid, mark `closed_won`             |
| `closed_won`        | Skip                                                          |
| `not_interested`    | Check for change-of-heart replies                             |

---

## Step-by-Step Usage

### 1. Prepare your leads CSV

`data/leads.csv` must have these columns:

```csv
company,contact,email,website,status,notes
Notion,John,john@notion.so,notion.so,new,
Linear,Sara,sara@linear.app,linear.app,new,Interested in automation
```

### 2. Configure `.env`

```bash
cp .env.example .env
# Fill in all required variables
```

### 3. Run the pipeline

```bash
python scripts/main.py
```

The orchestrator loops every 15 minutes. For a one-shot test, interrupt after the
first cycle with `Ctrl+C`.

### 4. Monitor output

Watch the console for tool calls:

```
  [TOOL] load_leads()
  [TOOL] research_company(lead_email='john@notion.so')
  [TOOL] generate_email(lead_email='john@notion.so', research_summary='Notion is...')
  [TOOL] send_email(to='john@notion.so', subject='Quick question about docs')
  [TOOL] mark_lead_status(lead_email='john@notion.so', new_status='emailed')

[AGENT] CYCLE COMPLETE
```

---

## How to Verify It Worked

1. **Emails sent**: Check your Gmail Sent folder for outgoing emails.
2. **CSV updated**: Open `data/leads.csv` — status should change from `new` → `emailed`.
3. **Reply detection**: Send a test reply from a lead email address; watch console for `[REPLY]`.
4. **Calendly link**: Verify the lead received a meeting email with your Calendly URL.
5. **Stripe invoice**: Log into your Stripe dashboard → Invoices tab.
6. **Final status**: After payment, `data/leads.csv` should show `closed_won`.

For quick smoke testing, use Gmail `+alias` addresses (e.g., `you+test1@gmail.com`).

---

## Common Pitfalls

| Symptom                        | Fix                                                                  |
|--------------------------------|----------------------------------------------------------------------|
| Gmail SMTP auth fails          | Use App Password, not account password. Enable 2FA first.            |
| Playwright returns empty text  | Run `python -m playwright install chromium`.                         |
| Nemotron returns empty email   | Check `NVIDIA_BASE_URL` and model ID.                                |
| IMAP check_replies() empty     | Enable IMAP in Gmail Settings → Forwarding and POP/IMAP.            |
| Stripe `No such customer`      | Email casing must be consistent in CSV.                              |
| Lead status not updating       | `mark_lead_status()` uses email as key — check exact match.         |

---

## Extending the Pipeline

To add a new pipeline stage:

1. Create your function in the relevant script (or a new `scripts/my_stage.py`).
2. Add a tool definition in `main.py`'s `TOOLS` list.
3. Add an `elif name == "your_tool":` branch in `execute_tool()`.
4. Update the system prompt to tell Nemotron when to call it.
5. Call `csv_reader.mark_lead_status()` to advance the status.
