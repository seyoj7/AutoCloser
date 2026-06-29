# AutoCloser — Autonomous B2B Sales Agent

> **Submission for the Hermes Agent Accelerated Business Hackathon**
> Presented by NVIDIA · Stripe · Nous Research

AutoCloser is an autonomous business agent that turns a CSV of leads into closed deals. Powered by **NVIDIA Nemotron 3 Ultra** as the reasoning brain, it uses **Playwright** for company research, **Gmail** for outreach, **Calendly** for scheduling, and **Stripe** for billing — all without human intervention.

Drop in a CSV. AutoCloser does the rest.

---

## 🤖 How It Works

AutoCloser follows the **Hermes agent pattern**: a system prompt defines the workflow, tool definitions give the model capabilities, and `tool_choice="auto"` lets the model decide every action autonomously.

```
main.py starts
  → Nemotron receives system prompt + 13 tool definitions
  → Nemotron reasons: "I should load leads first"
  → calls load_leads() → sees results
  → "This lead is new, I should research them"
  → calls research_company() → sees summary
  → "Now I'll write an email using this research"
  → calls generate_email() → calls send_email()
  → ... continues until all leads are processed ...
  → "CYCLE COMPLETE"
  → sleeps 15 min → repeat
```

**There is no hardcoded if/else pipeline.** Nemotron decides the order and logic at runtime based on each lead's status.

---

## 🧠 NVIDIA Nemotron Integration

**Model:** `nvidia/llama-3.3-nemotron-super-49b-v1`

| Role | How Nemotron Is Used |
|---|---|
| **Agent reasoning** | Drives the entire pipeline by autonomously choosing and sequencing tool calls |
| **Company research** | Summarizes scraped homepage text into actionable sales intel |
| **Email generation** | Writes hyper-personalized cold emails from research context |
| **Follow-up drafting** | Crafts context-aware replies to leads' questions |
| **Reply classification** | Classifies inbound replies as `interested`, `needs_more_info`, `not_interested`, or `unsubscribe` |

---

## 💳 Stripe Integration

AutoCloser uses Stripe to **close the financial loop autonomously**:

- **Provisions Stripe customers** from lead data (company name, email)
- **Creates itemized invoices** from a configurable `data/services.csv` menu
- **Emails the hosted invoice link** directly to the lead
- **Polls payment status** and advances the lead to `closed_won` upon payment

This makes AutoCloser a true **earn-and-operate** agent — it generates real revenue without human intervention.

---

## 🔁 Agent Pipeline

Each lead progresses through these stages. Nemotron decides the action at every step:

```
new → emailed → meeting_sent → meeting_booked → meeting_completed → invoiced → closed_won
         ↓
    followup_sent (loops back to check replies)
         ↓
    not_interested (dead end, unless they reply again)
```

| Status | What Nemotron Does |
|---|---|
| `new` | Research company → generate email → send → mark `emailed` |
| `emailed` | Check replies → classify → follow-up or schedule meeting |
| `followup_sent` | Check replies → classify → qualify → schedule or stop |
| `meeting_sent` | Check replies → if confirmed, mark `meeting_booked` |
| `meeting_booked` | Ask operator if meeting done → mark `meeting_completed` |
| `meeting_completed` | Create Stripe invoice → mark `invoiced` |
| `invoiced` | Check Stripe payment → if paid, mark `closed_won` |
| `closed_won` | Skip |
| `not_interested` | Check for change-of-heart replies |

---

## 🛠️ Tools Exposed to the Agent

Nemotron has access to 13 tools. It picks which to call and in what order:

| Tool | Description |
|---|---|
| `load_leads` | Load all leads and current status from CSV |
| `research_company` | Scrape website with Playwright + summarize with Nemotron |
| `generate_email` | Write a personalized cold email using research intel |
| `generate_followup` | Write a follow-up addressing a lead's specific question |
| `send_email` | Send email via Gmail SMTP (auto-threads replies) |
| `check_replies` | Poll Gmail IMAP for replies from a specific lead |
| `analyze_reply` | Classify reply sentiment with Nemotron |
| `qualify_lead` | Determine if a lead is worth pursuing |
| `schedule_meeting` | Send Calendly booking link to a qualified lead |
| `confirm_meeting` | Human-in-the-loop: confirm meeting completion |
| `create_invoice` | Present service menu, create & send Stripe invoice |
| `check_payment_status` | Poll Stripe for invoice payment status |
| `mark_lead_status` | Persist lead stage to CSV |

---

## 📁 Project Structure

```
Autocloser/
├── .env                    # Secret credentials (never commit)
├── .env.example            # Template for all required env vars
├── requirements.txt        # Python dependencies
├── data/
│   ├── leads.csv           # Lead database — status tracked here
│   └── services.csv        # Billable services menu (Stripe)
├── scripts/
│   ├── main.py             # Agent loop — Nemotron + tool executor
│   ├── csv_reader.py       # Load leads, update statuses, load services
│   ├── research.py         # Playwright scrape + Nemotron summarization
│   ├── email_agent.py      # Email generation, SMTP send, IMAP reply check
│   ├── scheduler.py        # Lead qualification + Calendly scheduling
│   └── billing.py          # Stripe invoice creation & payment polling
└── .agents/
    └── skills/
        └── saleshermes/
            └── SKILL.md    # Skill documentation
```

---

## 🚀 Setup & Installation

### Prerequisites

- Python 3.9+
- A Gmail account with 2FA enabled (for App Password)
- An NVIDIA NIM API key ([cloud.nvidia.com](https://cloud.nvidia.com))
- A Stripe account (test or live)
- A Calendly account with a public booking link

### 1. Install Dependencies

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
# NVIDIA Nemotron — the agent brain
NVIDIA_API_KEY=nvapi-...
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1

# Gmail SMTP/IMAP — outreach + reply monitoring
SMTP_USER=you@gmail.com
SMTP_PASSWORD=your-16-char-app-password

# Scheduling
CALENDLY_LINK=https://calendly.com/yourname/15min
CALENDLY_API_KEY=your_calendly_api_key

# Billing
STRIPE_SECRET_KEY=sk_test_...

# Identity
SENDER_NAME=Your Name
COMPANY_NAME=Your Company Name
```

> **Gmail App Password**: Enable 2FA at [myaccount.google.com](https://myaccount.google.com), then generate an App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).

### 3. Prepare Leads

Create `data/leads.csv`:

```csv
company,contact,email,website,status,notes
Notion,John,john@notion.so,notion.so,new,
Linear,Sara,sara@linear.app,linear.app,new,Interested in automation
```

### 4. Prepare Services (Stripe billing menu)

Create `data/services.csv`:

```csv
id,name,amount_cents,description
1,Discovery Call,0,Free 15-min intro call
2,Consulting Session,200000,2-hour deep-dive consulting ($2000)
3,Retainer,500000,Monthly retainer ($5000)
```

---

## ▶️ Running the Agent

```bash
python scripts/main.py
```

The agent runs in a **15-minute loop**. Each cycle:
1. Nemotron loads all leads
2. Processes every lead based on its current status
3. Prints `CYCLE COMPLETE`
4. Sleeps 15 minutes, then repeats

**Sample output:**

```
############################################################
  CYCLE 1 — 2026-06-30 00:45:12
############################################################

  [TOOL] load_leads()
  [TOOL] research_company(lead_email='john@notion.so')
  [TOOL] generate_email(lead_email='john@notion.so', research_summary='Notion is...')
  [TOOL] send_email(to='john@notion.so', subject='Quick question about docs')
  [TOOL] mark_lead_status(lead_email='john@notion.so', new_status='emailed')

[AGENT] CYCLE COMPLETE

--- FINAL STATUS ---
  Notion       | emailed
  Linear       | emailed

[LOOP] Next cycle at 01:00:12 (15 min). Press Ctrl+C to stop.
```

Press `Ctrl+C` to stop the loop.

---

## 🏆 Hackathon Fit

AutoCloser was built for the **Hermes Agent Accelerated Business Hackathon**. It demonstrates:

- **Agents that earn**: Nemotron drives outreach → Stripe closes the financial loop with real invoices and real payments
- **Agents that run real operations**: Full B2B sales cycle (research → outreach → qualification → scheduling → billing) runs autonomously
- **Agents at scale**: Drop in 1000 leads and walk away — the stateless CSV pipeline handles everything
- **NVIDIA Nemotron**: Powers all reasoning, research summarization, email generation, and reply classification
- **Stripe Skills**: The agent provisions customers, creates invoices, and tracks payments end-to-end

---

## 🐛 Common Issues

| Symptom | Fix |
|---|---|
| `SMTP auth failed` | Use a Gmail App Password, not your account password. Enable 2FA first. |
| `Playwright returns empty text` | Run `python -m playwright install chromium`. |
| `Nemotron returns empty email` | Check `NVIDIA_BASE_URL` and confirm the model ID. |
| `check_replies() finds nothing` | Enable IMAP in Gmail Settings → Forwarding and POP/IMAP. |
| `Stripe: No such customer` | Email casing must match exactly in CSV. |

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `openai` | ≥ 1.0.0 | OpenAI-compatible client for Nemotron tool-calling API |
| `python-dotenv` | ≥ 1.0.0 | Load credentials from `.env` |
| `playwright` | ≥ 1.40.0 | Headless browser for company website scraping |
| `stripe` | ≥ 7.0.0 | Stripe invoice creation and payment status polling |
| `requests` | ≥ 2.31.0 | HTTP client (Calendly API, etc.) |

---

## License

MIT License
