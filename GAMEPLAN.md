# ALFRED — Your AI Chief of Staff
## Game Plan v3: Managed Agents + Prompt Caching + Native Web Search

---

## THE BIG PICTURE

You're building **ALFRED** — a personal AI Chief of Staff that lives in Slack, reads your groups, researches links, generates daily briefings, builds tech for you, and helps you and your partner run your fertilizer/startup research operation.

**No n8n. No Zapier. No Brave Search API. No new platforms to learn.**
You pay for Anthropic API + Cursor + Claude Code. That's your stack.

**The system**: Python orchestrator + Claude Managed Agents + Prompt Caching + Slack Bot + Cron Jobs
**Runs on**: Railway ($5/month, auto-deploys from GitHub, auto-restarts)
**Dev environment**: Your Mac + Cursor

---

## ARCHITECTURE OVERVIEW

```
YOU (WhatsApp/Slack)
        |
        v
[SLACK WORKSPACE] <-- Central Hub (free tier)
   |         |
   v         v
[Message     [Scheduled
 Listener]    Cron Jobs]
   |              |
   v              v
[ALFRED BRAIN - Python Orchestrator]
   |
   |--- TIER 1: Regular API (messages.create + prompt caching)
   |      |-- Haiku 4.5 (classification — $0.001/call)
   |      |-- Sonnet 4.6 (chat, scoring, link summaries)
   |      |-- Native web_search tool (replaces Brave Search)
   |      |-- Prompt caching (90% savings on repeated system prompts)
   |
   |--- TIER 2: Claude Managed Agents (autonomous sessions)
   |      |-- Deep research (multi-step search + fetch + synthesis)
   |      |-- Morning briefings (topic scan + news gathering)
   |      |-- Building tasks (Phase 5)
   |      |-- Built-in: web_search, web_fetch, bash, read/write/edit
   |      |-- MCP server support (GitHub, Notion, etc.)
   |      |-- Custom tools (Slack posting, database queries)
   |
   |--- Media Processing (Phase 2):
   |      |-- OpenAI Whisper (voice note transcription)
   |      |-- PDF parsing (research documents)
   |
   |--- Builder Layer (Phase 5):
   |      |-- Claude Code SDK (build apps programmatically)
   |      |-- Cursor (you supervise, it codes)
   |
   |--- Market Intelligence (Phase 6):
   |      |-- Alpaca API (stocks, commodities)
   |      |-- Claude web_search (sector news)
   |
   |--- Research Engine:
          |-- Fertilizer/Agriculture feeds
          |-- Tech/Science/Politics news
          |-- Startup idea generation
          |-- Trading strategy research
```

---

## PROJECT STRUCTURE (Current — What's Actually Built)

```
fatima/
├── alfred/                       # Main application package
│   ├── __init__.py
│   ├── main.py                   # Entry point — validates config, starts everything
│   ├── config.py                 # All settings from .env
│   ├── setup_agent.py            # One-time CLI to create Managed Agent + Environment
│   │
│   ├── brain/                    # All Claude API interaction
│   │   ├── __init__.py
│   │   ├── api.py                # Regular API calls with prompt caching
│   │   ├── agent.py              # Managed Agent (create, sessions, streaming)
│   │   └── prompts.py            # All system prompts in one place
│   │
│   ├── slack/                    # Slack bot layer
│   │   ├── __init__.py
│   │   ├── bot.py                # Event handlers (classify → route → respond)
│   │   └── senders.py            # Post to channels/DMs by name
│   │
│   ├── intelligence/             # Message processing pipeline
│   │   ├── __init__.py
│   │   ├── classifier.py         # Haiku classification with hash cache
│   │   └── link_processor.py     # URL fetch + summarize + web_search fallback
│   │
│   ├── research/                 # Research capabilities
│   │   ├── __init__.py
│   │   └── engine.py             # Deep research (agent) + quick research (API)
│   │
│   ├── briefing/                 # Daily briefing system
│   │   ├── __init__.py
│   │   └── generator.py          # Morning briefing via Managed Agent session
│   │
│   ├── memory/                   # Persistent memory
│   │   ├── __init__.py
│   │   └── store.py              # JSON store with dedup, research history, ideas
│   │
│   ├── scheduler/                # Cron jobs
│   │   ├── __init__.py
│   │   ├── jobs.py               # Job definitions (briefing, token reset, health)
│   │   └── runner.py             # APScheduler setup
│   │
│   └── utils/                    # Shared utilities
│       ├── __init__.py
│       ├── errors.py             # safe_handler decorators
│       └── logging.py            # Structured logging
│
├── data/                         # Local data (gitignored)
│   ├── memory.json               # Persistent memory
│   ├── research/                 # Saved research reports
│   ├── builds/                   # Generated specs & plans
│   └── cache/                    # URL & response cache
│
├── deploy/                       # Deployment configs
│   ├── railway.toml              # Railway deployment config
│   └── Procfile                  # Process runner
│
├── .env.example                  # Template for API keys
├── .env                          # Actual API keys (NEVER committed)
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── GAMEPLAN.md                   # This file — architecture & roadmap
├── ALFRED.md                     # Complete knowledge base & API reference
├── SETUP.md                      # Quick-start setup guide
└── README.md                     # (to be created)
```

---

## WHY SLACK IS YOUR HUB (not WhatsApp directly)

1. **WhatsApp Business API costs money and is locked down.** Meta requires business verification.
2. **Slack has a FREE tier** with full bot API access. Claude can read AND write messages.
3. **The bridge**: You forward important stuff from WhatsApp to Slack, or set up an auto-bridge later.
4. **Your partner joins the same Slack workspace** for free. Both get ALFRED.
5. Slack supports channels, threads, file uploads, slash commands — perfect for a chief of staff.

### The WhatsApp-to-Slack Flow (3 options):

**Option A — Manual Forward (Simplest, Zero Setup) — START HERE**
- You see something interesting in WhatsApp group
- Forward/copy-paste into `#incoming` Slack channel
- ALFRED picks it up automatically, researches it, responds in thread

**Option B — WhatsApp Web Bridge (Free, Phase 7)**
- Uses `whatsapp-web.js` or Baileys (open source Node.js libraries)
- Auto-forwards messages from specific groups to Slack channels
- Risk: WhatsApp CAN temp-ban accounts using unofficial APIs

**Option C — Slack as Primary (Cleanest)**
- Move your research conversations to Slack entirely
- WhatsApp stays for casual chat
- ALFRED lives fully in Slack, no bridge risk

**RECOMMENDATION: Start with Option A. Get ALFRED working. Add bridge in Phase 7 only if you actually need it.**

---

## VOICE NOTE HANDLING (Phase 2 — Whisper Integration)

### How It Works:
1. **Voice note arrives in Slack** (either uploaded manually or forwarded by bridge)
2. ALFRED detects audio file attachment (`.ogg`, `.m4a`, `.mp3`, `.wav`)
3. **Whisper API** transcribes it to text (OpenAI Whisper — $0.006/minute via API)
4. ALFRED processes the transcript same as any text message (classify, research, respond)
5. Posts: "Voice note from [person]: [transcript]" + ALFRED's analysis in thread

### Two Whisper Options:

| Option | Cost | Speed | Setup |
|--------|------|-------|-------|
| **Whisper API (OpenAI)** | $0.006/min | Fast (2-3 sec) | Just an API key |
| **Whisper Local (open source)** | Free | Slower (10-30 sec) | Needs GPU or decent CPU |

**RECOMMENDATION**: Start with Whisper API (costs pennies). Switch to local later if volume is high.

---

## WHAT ALFRED DOES (Feature Breakdown)

### 1. MESSAGE INTELLIGENCE (reads your groups, filters noise)

Not every message matters. ALFRED classifies every message it sees:

| Category | What It Is | What ALFRED Does |
|----------|-----------|-----------------|
| **URGENT** | Time-sensitive, needs your action | Responds immediately with urgency |
| **RESEARCH** | Contains a link or topic worth digging into | Fetches the link, summarizes, or runs deep research |
| **IDEA** | A startup/business idea mentioned | Scores it on 5 criteria, saves to idea bank |
| **TASK** | Something that needs to be done | Acknowledges, clarifies, asks permission before acting |
| **CHAT** | Casual conversation, greetings | Ignores (unless @ALFRED mentioned) |

**How it picks**: Claude Haiku classifies every message. Costs ~$0.001 per classification. Haiku is used because classification is simple — no need for Sonnet/Opus.

**Link handling**: When someone drops a link in the group:
1. ALFRED detects URL(s) in the message
2. Fetches content using httpx + BeautifulSoup (fast, direct)
3. If the fetch fails (paywall, JS-heavy), falls back to Claude's native web_search
4. Claude Sonnet summarizes: what is it, why it matters, what Batman should do about it
5. Posts summary in a thread under the original message

### 2. DAILY MORNING BRIEFING ("Good Morning Batman")

Every day at **10:00 AM** (configured wake time — can be changed), ALFRED posts to your `#daily-briefing` channel:

```
Good morning Batman. Here's your day:

━━━ TODAY'S PRIORITIES ━━━
1. Review the fertilizer supply chain report your partner shared yesterday
   → Summary attached in thread, key finding: urea prices dropping 8% in Q3
2. Follow up on the AgriTech pitch deck (draft ready for review in #builds)
3. Market update: Potash prices moved +3.2% overnight

━━━ NEW THINGS YOU SHOULD KNOW ━━━
• [Agriculture] India announced new fertilizer subsidy policy — impacts your supply chain
  → Full research report: thread below
• [Tech] New Claude model dropped — implications for ALFRED's own capabilities
• [Science] Phosphate extraction breakthrough published in Nature
  → Potential disruption to current market. Deep dive available.

━━━ IDEAS & OPPORTUNITIES ━━━
• AI-powered soil testing marketplace — viability score: 7.2/10
• WhatsApp-based farmer advisory for South Asia — viability score: 8.1/10

━━━ UNPROCESSED ━━━
• 3 links in #incoming still need your review

Reply with a number to deep-dive, or "skip" to move on.
```

**How it works**:
- APScheduler triggers at wake time (or Claude Code Routine in Phase 7)
- A **Managed Agent session** fires: searches all tracked topics via web_search, gathers news, checks memory for recent activity
- The agent synthesizes everything into a briefing and posts to `#daily-briefing`

### 3. DEEP RESEARCH ENGINE

When you say "research this" or ALFRED finds something worth digging into:

1. **A Managed Agent session fires** on Anthropic's cloud
2. The agent autonomously runs multiple web searches from different angles
3. Fetches and reads the most promising pages via web_fetch
4. Cross-references findings across sources
5. Claude synthesizes all sources into a structured research report
6. Posts the report to the relevant Slack channel
7. Saves key findings to memory so it doesn't re-research the same topic

**Research domains (auto-monitored via morning briefing)**:
- Fertilizers & chemicals (your main space)
- Agriculture & AgriTech
- Tech & AI (for your projects)
- Science breakthroughs
- Politics (policy that affects your sectors)
- Startup ecosystem news

**Deep research on demand**:
```
Batman: "@ALFRED research phosphate recycling technologies"
ALFRED: "On it, Batman. Running research..."
[Agent session: runs 8 searches, reads 5 articles, synthesizes]
ALFRED: Posts structured report with:
  - Executive summary
  - Key findings (numbered)
  - Market implications
  - Startup opportunities
  - Sources (all real URLs)
  - Recommended next steps
```

### 4. BUILDER MODE — Phase 5 (Tech Ideas → Working Products)

When you describe a tech idea, ALFRED:

1. **Clarifies**: Asks 2-3 questions to understand scope
2. **Specs it out**: Writes a one-page spec document
3. **Estimates cost**: Token/time estimate
4. **ASKS PERMISSION**: Always. Never builds without your "yes"
5. **Builds it** using Claude Code SDK (programmatic Claude Code)

**Permission model**:
```
ALFRED: "I'd like to build the fertilizer price dashboard you described.
         Spec: [link to spec in #builds]
         Cost: ~$0.15 in tokens
         Tool: Claude Code SDK
         Output: React dashboard + Python API
         Approve? (yes/no/modify)"

Batman: "yes"
ALFRED: [starts building via Claude Code SDK]
```

ALFRED NEVER spends tokens on building without this approval step.

### 5. DOCUMENT GENERATION

On command, ALFRED creates:

| Document | How |
|----------|-----|
| **Pitch Deck** | Structured markdown (10-12 slides) → paste into Canva/Google Slides |
| **One-Pager** | Executive summary of any idea, research, or plan |
| **Research Report** | Full deep-dive with sources, data, analysis, recommendations |
| **Business Plan** | Lean canvas or full business plan |
| **Competitive Analysis** | Market landscape, competitors, positioning |

### 6. TRADING & MARKET INTELLIGENCE (Phase 6)

Using Alpaca API + Claude web_search:
- Monitor your watchlist (fertilizer companies, tech stocks, commodities)
- Daily market summary baked into morning briefing
- Alert you on big moves (>3% change) via Slack DM
- Generate trading strategy reports on demand

### 7. WEB DASHBOARD (Phase 4)

Because Slack is great for real-time but terrible for searching past research:
- Browse research history and idea bank
- Settings panel (wake time, topics, model preferences)
- Token usage dashboard
- Agent session viewer

### 8. MULTI-USER (Your Partner)

Your partner joins the Slack workspace. They get:
- Access to shared channels (`#fertilizer-research`, `#ideas`, `#market-data`)
- Their own DM with ALFRED for personal tasks
- Shared research benefits (one person's research is available to both)
- Collaborative idea development (both can comment on idea threads)
- ALFRED tracks who asked for what — no crossed wires

---

## COST BREAKDOWN

| Tool | Cost | You Already Pay? |
|------|------|-----------------|
| **Anthropic API** (Claude brain) | ~$8-12/month (with prompt caching) | **NEED TO SET UP** |
| **Cursor** | $20/month | Yes |
| **Claude Code** | Included with Claude sub | Yes |
| **Slack** | Free tier | Free |
| **Railway** | $5/month | New |
| **OpenAI Whisper API** | $0.006/min (~$1-2/month) | New (Phase 2) |
| **Python + all libraries** | Free (open source) | Free |
| **Alpaca API** | Free (paper trading) | Free (Phase 6) |

**Total new cost: ~$13-17/month** on top of Cursor you already pay for.

**Cost savings from prompt caching:**
- System prompt cached at 10% of base input cost
- 100+ API calls/day × cached system prompt = ~40-60% savings on input tokens
- Haiku for 80% of calls ($0.001 each)
- Managed Agent only for heavy tasks (~2-3 sessions/day)

---

## BUILD ORDER (Phase by Phase)

### PHASE 1: Foundation ✅ DONE — "ALFRED Talks + Researches"

**What's built:**
- Python project with full directory structure
- Slack Bolt bot (Socket Mode) — listens in all channels
- Message classification with Haiku (URGENT/RESEARCH/IDEA/TASK/CHAT)
- Link fetching + summarization (httpx + BS4 + Sonnet)
- Web search fallback (Claude native web_search, no Brave)
- @ALFRED direct conversation
- Idea scoring
- Deep research via Managed Agent sessions
- Morning briefing via Managed Agent sessions
- Prompt caching on all API calls (90% savings on system prompt)
- Daily token budget tracking + midnight reset
- Health checks every 30 minutes
- JSON memory store with dedup
- Railway deployment config

**End of Phase 1**: Batman talks to ALFRED in Slack, it classifies, researches, summarizes, briefs.

---

### PHASE 2: Intelligence — "Make It Smart"
**Goal**: Voice notes, PDFs, smarter memory.

1. **Voice note processor**: Detect audio → Whisper transcription → classify → respond
2. **PDF processor**: Parse research documents into text → summarize
3. **Memory upgrade**: Mem0 integration (auto-learns from conversations)
4. **Lifestyle learning**: Track when Batman responds → adjust briefing time
5. **Interactive briefing**: "Tell me more about 2" → deep dive in thread

**End of Phase 2**: ALFRED handles any media type and learns your patterns.

---

### PHASE 3: Research Engine — "Personal Analyst"
**Goal**: Automated daily research + slash commands.

1. **Auto-research cron**: Daily scans on tracked topics via agent sessions
2. **Slash commands**: `/research [topic]`, `/brief`, `/idea [concept]`
3. **Research history**: Searchable archive of past reports
4. **Startup idea generator**: Scores opportunities from research findings
5. **Shared research**: Collaborative channels for partner

**End of Phase 3**: ALFRED is a research analyst covering your sectors daily.

---

### PHASE 4: Web Dashboard — "Control Center"
**Goal**: Web UI to browse research, manage settings, view history.

1. **Research browser**: Search and filter past reports
2. **Idea bank**: Browse, sort, and filter scored ideas
3. **Settings panel**: Wake time, topics, model preferences
4. **Token dashboard**: Daily/monthly usage and cost tracking
5. **Agent session viewer**: See what ALFRED did in each session

**End of Phase 4**: Full visibility into everything ALFRED does.

---

### PHASE 5: Builder Mode — "Idea to Product"
**Goal**: Describe an idea → ALFRED specs it → asks permission → builds it.

1. **Idea pipeline**: Clarify → Spec → Estimate → Permission → Build
2. **Claude Code SDK**: Programmatic code generation
3. **Document generation**: Pitch decks, one-pagers, reports, business plans
4. **Custom tools on Managed Agent**: Agent posts progress to Slack during builds

**End of Phase 5**: Idea to working prototype + pitch deck in a day.

---

### PHASE 6: Market Intelligence — "Money Moves"
**Goal**: Stock/commodity monitoring, alerts, trading strategies.

1. **Alpaca integration**: Watchlist for fertilizer stocks, tech, commodities
2. **Alert system**: >3% moves → immediate DM
3. **Strategy generator**: Technical + fundamental analysis on demand
4. **Morning briefing integration**: Market summary baked into daily brief

**End of Phase 6**: Market intelligence woven into your daily flow.

---

### PHASE 7: Polish & Expand — "Full Power"
**Goal**: WhatsApp bridge, MCP ecosystem, Claude Code Routines.

1. **WhatsApp bridge** (optional): `whatsapp-web.js` auto-forwards group messages to Slack
2. **MCP servers on Managed Agent**: GitHub, Notion, Linear, Jira — connected natively
3. **Claude Code Routines**: Replace APScheduler with Anthropic-hosted scheduled tasks
4. **Multi-agent orchestration**: Sub-agents (researcher, builder, analyst) coordinated by ALFRED
5. **Fine-tuning** (optional, using Unsloth): Custom model for fertilizer/agriculture classification

**End of Phase 7**: ALFRED is at full power.

---

## ERROR HANDLING & EDGE CASES

| Error | What ALFRED Does |
|-------|-----------------|
| **Slack API down** | Queues messages locally, retries, logs to `data/` |
| **Claude API down** | Posts: "Brain is resting. Queued for when I'm back." |
| **Claude API rate limit** | Exponential backoff. Prioritizes URGENT over RESEARCH |
| **Token budget exceeded** | Daily cap. Warns at 80%. Stops non-essential at 100%. Resets at midnight |
| **Bad URL / dead link** | Falls back to web_search to find the same topic from other sources |
| **Paywalled article** | web_search fallback finds free sources on the same topic |
| **Duplicate messages** | SHA-256 hash dedup in memory store (24-hour TTL) |
| **Spam/noise in group** | CHAT classification = ignored. Adjustable threshold |
| **Agent session fails** | Error logged, user notified, falls back to regular API call |
| **Agent session too long** | Event limit (200 events) prevents runaway sessions |
| **Research finds nothing** | Honest: "Searched 12 sources, nothing new on [topic]" |
| **Railway server crash** | Auto-restarts. State persisted in JSON + filesystem |
| **Multiple links in one message** | Processes each separately, posts summary for each in thread |
| **Message in non-English** | Claude handles multilingual natively |

---

## TOKEN SAVING STRATEGY

### The Three Gates:

1. **Classification Gate**: Haiku classifies every message. If CHAT → stop. Costs $0.001. Saves 60-70% of token spend.

2. **Permission Gate**: ALFRED NEVER does expensive operations without asking:
   - Deep research → asks first
   - Building anything → asks first with cost estimate
   - Document generation → asks first

3. **Cache Gate**: Prompt caching on all API calls:
   - System prompt cached for 5 minutes (auto-refreshed on each hit)
   - Cache reads cost 10% of base input price = **90% savings**
   - Hash-based dedup in memory prevents reprocessing same content

### Tiered Model Routing:

| Tier | Model | Used For | Cost | % of Calls |
|------|-------|---------|------|-----------|
| **1** | Haiku 4.5 | Classification | $1/MTok input | ~80% |
| **1** | Sonnet 4.6 | Chat, scoring, summaries | $3/MTok input | ~15% |
| **1** | Sonnet 4.6 + web_search | Quick research | $3/MTok + search | ~3% |
| **2** | Managed Agent (Sonnet) | Deep research, briefings | Per-session | ~2% |

### Estimated Monthly Spend (with caching):
- 100 classifications/day (Haiku): **~$0.30/month**
- 15 chat/summary tasks/day (Sonnet, cached): **~$3/month**
- 2 agent sessions/day (deep research + briefing): **~$5/month**
- Voice transcription (Whisper, Phase 2): **~$1/month**
- **Total: ~$8-12/month in API costs**

---

## SLACK WORKSPACE SETUP GUIDE

### Step 1: Create the Workspace
1. Go to `slack.com/get-started#/createnew`
2. Enter your email, verify
3. Workspace name: "ALFRED HQ" (or whatever you want)

### Step 2: Create Channels
Create these channels (all public):
- `#incoming` — Drop links, messages, voice notes here for ALFRED to process
- `#daily-briefing` — Morning briefings land here
- `#research` — General research outputs
- `#fertilizer-research` — Fertilizer/chemical specific research (shared with partner)
- `#ideas` — Startup ideas and opportunity scoring
- `#market-data` — Trading/market intelligence
- `#builds` — Tech building requests and outputs
- `#alfred-logs` — ALFRED's internal logs (for debugging)

### Step 3: Create the ALFRED Bot
1. Go to `api.slack.com/apps`
2. Click "Create New App" → "From scratch"
3. App name: "ALFRED", workspace: your workspace
4. Go to **OAuth & Permissions** → Bot Token Scopes, add:
   - `app_mentions:read`, `channels:history`, `channels:read`, `chat:write`
   - `files:read`, `im:history`, `im:read`, `im:write`
   - `reactions:write`, `users:read`
5. Go to **Event Subscriptions** → Enable → Subscribe to:
   - `app_mention`, `message.channels`, `message.im`, `file_shared`
6. Go to **Socket Mode** → Enable → Generate app-level token (`connections:write`) → Copy (`xapp-...`)
7. Install the app to your workspace
8. Copy the **Bot User OAuth Token** (`xoxb-...`)
9. Copy the **Signing Secret** from Basic Information
10. **Invite ALFRED** to each channel: `/invite @ALFRED`

### Step 4: Invite Your Partner
- Send them the Slack workspace invite link
- They join the shared channels
- They can DM ALFRED for personal tasks too

### Step 5: Get Your API Key
1. **Anthropic**: `console.anthropic.com` → Create account → Add $5 credit → Copy API key

That's it. No Brave Search key. No other API keys for Phase 1.

---

## WHAT BATMAN NEEDS TO DO

### Before Coding:
- [x] **Anthropic API key** — `console.anthropic.com`, add $5, copy key
- [x] **Slack workspace created** — follow guide above
- [x] **Slack bot created** — Bot Token + Signing Secret + App Token

### Can Add Later:
- [ ] OpenAI API key (for Whisper voice notes — Phase 2)
- [ ] Alpaca API key (for market data — Phase 6)
- [ ] Partner's Slack username (once they join)
- [ ] Specific fertilizer companies/tickers to track
- [ ] Web dashboard hosting (Phase 4)

### Already Decided:
- ALFRED calls you: **"Batman"**
- Wake time: **10:00 AM** (configurable)
- Runs on: **Railway ($5/month)**
- Dev environment: **Mac + Cursor**
- Search: **Claude native web_search** (no external search API)
- Research: **Claude Managed Agents** (autonomous sessions)
- Caching: **Prompt caching on all API calls**

---

## OPEN SOURCE REPOS USED

| Repo | Purpose |
|------|---------|
| `github.com/anthropics/anthropic-sdk-python` | Python SDK for Claude API + Managed Agents |
| `github.com/anthropics/claude-agent-sdk-python` | Claude Code SDK for builder mode (Phase 5) |
| `github.com/openai/whisper` | Local voice transcription (Phase 2, free alternative to API) |
| `github.com/nicekui/whatsapp-mcp` | WhatsApp bridge (Phase 7, optional) |
| `Slack Bolt for Python` | Official Slack bot framework |
| `APScheduler` | Python cron job scheduling |
| `Mem0` | AI agent memory framework (Phase 2 upgrade) |

---

## THE HONEST TRUTH

**What ALFRED CAN do:**
- Be a genuinely useful AI chief of staff in Slack
- Research, summarize, plan, and brief Batman daily
- Process links with web search fallback for paywalls
- Build tech prototypes when asked (Phase 5)
- Monitor your sectors and surface opportunities
- Track markets and alert on big moves (Phase 6)
- Generate pitch decks, reports, plans
- Work for both Batman and partner
- Learn patterns and get better over time (Phase 2+)
- Search the web natively without any external search API

**What ALFRED CAN'T do:**
- Replace a human chief of staff (no emotional intelligence)
- Auto-trade stocks (always get your approval first)
- Guarantee research accuracy (always verify via source URLs)
- Work natively on WhatsApp without some jank (Slack-first is the way)
- Read your mind (the better you communicate, the better it gets)

---

## NEXT STEP

Phase 1 is built. To get ALFRED running:

```bash
# 1. Set up your .env with API keys (see SETUP.md)
# 2. Install dependencies
pip install -r requirements.txt

# 3. Create the Managed Agent (one-time)
python -m alfred.setup_agent

# 4. Launch ALFRED
python -m alfred.main
```

See `SETUP.md` for the complete step-by-step guide.
See `ALFRED.md` for the full technical knowledge base and API reference.
