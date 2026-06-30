---
name: autocloser
description: >
  Autonomous B2B sales pipeline agent. Researches companies, sends personalized
  cold emails, monitors replies, schedules meetings, and sends invoices.
  Trigger this skill when the user asks to run the sales pipeline, manage leads,
  check pipeline status, or change agent settings.
version: 1.0.0
platforms: [windows, linux, macos]
requires_tools: [terminal]
metadata:
  hermes:
    category: sales-automation
    tags: [b2b, email, crm, pipeline, outreach, sales]
---

# AutoCloser — Autonomous B2B Sales Agent

## When to Use

Trigger this skill when the user asks to:
- **Run the sales pipeline** — "run AutoCloser", "start outreach", "process leads"
- **Add or manage leads** — "add a lead", "remove lead", "update lead", "show leads"
- **Check pipeline status** — "pipeline status", "show funnel", "how are my leads doing"
- **Change settings** — "change sender name", "set email tone", "show settings"
- **Manage services** — "list services", "add a service"
- **Schedule recurring runs** — "run AutoCloser every hour"

## Project Location

All commands must be run from the project root: `e:\Programs\Autocloser`

The Python executable should be invoked as `python` on Windows.

## Commands

### Run the Pipeline

Run a single cycle of the sales pipeline (processes all leads based on their status):

```
python scripts/main.py --single-cycle --no-input
```

- `--single-cycle` — runs one cycle and exits (no infinite loop)
- `--no-input` — skips all interactive prompts (auto-confirms meetings and invoices)

For continuous operation (loops based on settings interval):

```
python scripts/main.py --no-input
```

### Manage Leads

**List all leads:**
```
python scripts/cli.py list-leads
```

**Add a new lead:**
```
python scripts/cli.py add-lead --company "CompanyName" --contact "PersonName" --email "person@company.com" --website "company.com" --notes "Optional notes"
```

**Update a lead's field:**
```
python scripts/cli.py update-lead --email "person@company.com" --field status --value meeting_sent
```
Valid fields: `company`, `contact`, `email`, `website`, `notes`, `status`
Valid statuses: `new`, `emailed`, `followup_sent`, `meeting_sent`, `meeting_booked`, `meeting_completed`, `invoiced`, `closed_won`, `not_interested`

**Remove a lead:**
```
python scripts/cli.py remove-lead --email "person@company.com"
```

**Show pipeline funnel:**
```
python scripts/cli.py pipeline-status
```

### Manage Services

**List billable services:**
```
python scripts/cli.py list-services
```

**Add a new service:**
```
python scripts/cli.py add-service --id 5 --name "workshop" --description "Half-day workshop" --amount 75000
```
Note: `--amount` is in cents (75000 = $750.00)

### Manage Settings

**Show all settings:**
```
python scripts/cli.py show-settings
```

**Update a setting:**
```
python scripts/cli.py set --key SETTING_KEY --value NEW_VALUE
```

Available settings:

| Key | Type | Description |
|-----|------|-------------|
| `sender_name` | string | Name in email signatures |
| `company_name` | string | Company name in email copy |
| `calendly_link` | string | Public Calendly booking URL |
| `cycle_interval_minutes` | int | Pipeline loop interval (default 15) |
| `pipeline_mode` | string | `"ai"` (Nemotron) or `"procedural"` (hardcoded) |
| `email_tone` | string | Tone for emails: "conversational", "formal", "friendly", etc. |
| `auto_confirm_meetings` | bool | Auto-confirm meetings (true/false) |
| `auto_create_invoices` | bool | Auto-create invoices (true/false) |
| `default_service_id` | string | Default service ID for auto-invoicing |
| `max_email_words` | int | Max word count for generated emails |
| `notifications_enabled` | bool | Enable/disable status notifications |

**Reset all settings to defaults:**
```
python scripts/cli.py reset-settings
```

## Notifications

The pipeline automatically sends notifications for every status change:

- 📧 **emailed** — Cold email sent
- 📨 **followup_sent** — Follow-up sent
- 📅 **meeting_sent** — Meeting link sent
- ✅ **meeting_booked** — Meeting booked
- 🤝 **meeting_completed** — Meeting completed
- 💰 **invoiced** — Invoice sent
- 🎉 **closed_won** — Payment received, deal done!
- ❌ **not_interested** — Lead declined

Notifications appear in stdout (visible in Hermes gateway), and are also
logged to `data/notifications.log`.

## Lead Status Flow

```
new → emailed → meeting_sent → meeting_booked → meeting_completed → invoiced → closed_won
         ↓
    followup_sent → (re-enters at emailed flow)
         ↓
    not_interested (can recover if they reply later)
```

## Verification

After running a command, verify by checking:
1. **Pipeline output** — Look for `[OK] Agent cycle complete!` and the pipeline summary
2. **CSV status** — Run `python scripts/cli.py list-leads` to see updated statuses
3. **Notifications** — Check for 🔔 NOTIFICATION blocks in the output
4. **Settings** — Run `python scripts/cli.py show-settings` to confirm changes

## Prerequisites

- Python 3.10+ with packages: `openai`, `python-dotenv`, `playwright`, `stripe`, `requests`
- Playwright Chromium: `python -m playwright install chromium`
- `.env` file with API keys (NVIDIA, Gmail SMTP, Stripe, Calendly)
- `data/leads.csv` with at least one lead
