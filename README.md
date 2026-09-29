# MemoryMeet

> Don't just remember what was said. Know what changed.

A meeting-prep agent that stores meetings in **Hindsight** memory, then detects priority shifts, contradictions, slipped commitments and expectation gaps before your next meeting.

## Project layout

```
memorymeet/
├── app.py            Streamlit UI (3 tabs)
├── pipeline.py       Write path: transcript -> extract -> retain
├── extractor.py      LLM turns transcript into structured facts
├── memory.py         ALL Hindsight code (retain / recall / reflect)
├── analyzer.py       Read path: recall -> detect changes -> briefing
├── llm.py            Groq wrapper (retries, fallback model, JSON parsing)
├── config.py         Reads keys from .env
├── seed.py           Loads demo data from the terminal
└── data/meetings.json  5 sample meetings (Northwind Logistics)
```

## Setup (about 15 minutes)

### 1. Install Python
Use Python 3.10 or newer. Check with `python --version`.

### 2. Create a virtual environment and install packages
```bash
cd memorymeet
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac / Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Get your keys
**Groq (the LLM)**
1. Go to https://console.groq.com and sign up.
2. API Keys -> Create API Key -> copy it.

**Hindsight Cloud (the memory)**
1. Go to https://ui.hindsight.vectorize.io and sign up, verify your email, create an organization.
2. Billing section -> enter promo code `MEMHACK99` for $50 credits.
3. Click **Connect** in the top bar -> **Create API Key** -> copy it immediately (it is shown only once).

### 4. Create your `.env` file
```bash
# Windows:   copy .env.example .env
# Mac/Linux: cp .env.example .env
```
Open `.env` and paste your two keys.

### 5. Load demo data, then run
```bash
python seed.py
streamlit run app.py
```
`seed.py` reads 5 meetings, extracts facts with the LLM, and stores them in Hindsight. It takes 1 to 3 minutes. (You can also click **Load demo data** in the app sidebar.)

## Demo script (60 seconds)

1. Open tab **2. Prep briefing**, keep the defaults, click **Generate briefing**.
2. Left column: generic briefing without memory. Right column: MemoryMeet catches these planted issues:
   - CRM integration quietly moved to Q1 (internal decision, client never told, client still expects it this year)
   - CRM sandbox demo promised for Aug 25, never delivered
   - Data residency concern raised twice, never answered
   - Pricing conflict: 44,000 offered to client, finance floor is 46,000
3. Open tab **3. Ask memory** and ask: "What does the client expect from us that we may not deliver?"
4. Show the "Learning curve": in tab **1. Add meeting**, paste a new transcript, then regenerate the briefing and show it updating.

## How Hindsight is used (for your submission write-up)

| Step | Hindsight call | File |
|---|---|---|
| One memory bank per client with a mission | `create_bank(mission=...)` | memory.py |
| Store every meeting with its real date | `retain(timestamp=..., document_id=...)` | memory.py |
| Fetch history before a meeting | `recall(query=..., budget="mid")` x5 topic queries | memory.py / analyzer.py |
| Free-form questions over memory | `reflect(query=...)` | memory.py |

Hindsight also consolidates related facts into "observations" in the background and keeps history when new evidence contradicts old, so recall can return `world`, `experience` and `observation` results.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Missing in .env` shown in the app | Check `.env` is in the same folder as `app.py` and has no quotes or spaces around `=` |
| 401 / unauthorized from Hindsight | Key wrong or expired; create a new one under Connect |
| Groq JSON or function errors | Handled by retry and fallback. If it keeps failing, set `PRIMARY_MODEL=qwen/qwen3-32b` in `.env` |
| Groq rate limit (429) | Wait 30 seconds and retry; the free tier has per-minute limits |
| Briefing says "No memories found" | Run `python seed.py` first, and make sure the client name in the sidebar matches |
| Briefing misses some changes | Newly stored facts may take a short while to consolidate in Hindsight. Wait a minute and regenerate |
| `AttributeError` on a Hindsight call | The SDK changed. Run `pip install -U hindsight-client` and check https://hindsight.vectorize.io/sdks/python |

## Ideas to improve after it works

- Add a timeline chart of each party's priorities over time
- Add a small evaluation script: list the 4 planted changes and check the agent finds them (great for the Technical Implementation score)
- Add Google Calendar or Zoom transcript import
- Add a feedback button (useful / not useful) and retain it, so the agent learns your briefing preferences
