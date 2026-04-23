# ALFRED - Your AI Chief of Staff
## Full Game Plan v2: Architecture, Build Order, Tools, Error Handling

---

## THE BIG PICTURE

You're building **ALFRED** — a personal AI Chief of Staff that lives in Slack, reads your groups, researches links, generates daily briefings, builds tech for you, and helps you and your friend run your fertilizer/startup research operation.

**No n8n. No Zapier. No new platforms to learn.**
You already pay for Cursor + Claude + Bolt.new + Claude Code. That's your stack.

**The system**: Python orchestrator + Claude API + Open Source MCP servers + Slack Bot + Cron Jobs
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
   |--- Claude API (reasoning, planning, writing)
   |      |-- Haiku 4.5 (classification, triage — cheap)
   |      |-- Sonnet 4.6 (research, briefings — balanced)
   |      |-- Opus 4.6 (deep analysis, strategy — heavy)
   |
   |--- MCP Servers (plugged in as tools):
   |      |-- Slack MCP (read/write messages)
   |      |-- Fetch MCP (grab any URL/page content)
   |      |-- Brave Search MCP (deep web research)
   |      |-- Filesystem MCP (save reports, plans, data)
   |      |-- Memory MCP (knowledge graph — learns your lifestyle)
   |      |-- Git MCP (manage code repos)
   |      |-- Puppeteer MCP (scrape JS-heavy sites, X/Twitter)
   |
   |--- Media Processing:
   |      |-- OpenAI Whisper (voice note transcription)
   |      |-- OpenDataLoader PDF (parse documents/PDFs)
   |
   |--- Builder Layer:
   |      |-- Claude Code (build apps from terminal)
   |      |-- Bolt.new API (quick prototypes)
   |      |-- Cursor (you supervise, it codes)
   |
   |--- Market Intelligence:
   |      |-- Alpaca API (stocks, commodities)
   |      |-- Brave Search (sector news)
   |
   |--- Research Engine:
          |-- Fertilizer/Agriculture feeds
          |-- Tech/Science/Politics news
          |-- Startup idea generation
          |-- Trading strategy research
```

---

## PROJECT STRUCTURE (Production-Ready)

This is what gets built in your `fatima/` folder:

```
fatima/
├── alfred/                       # Main application package
│   ├── __init__.py
│   ├── main.py                   # Entry point, app startup
│   ├── config.py                 # Settings, env vars, model routing
│   │
│   ├── brain/                    # Claude API integration layer
│   │   ├── __init__.py
│   │   ├── client.py             # Anthropic API wrapper, model selector
│   │   ├── prompts.py            # System prompts for each mode
│   │   ├── tools.py              # Tool definitions for Claude
│   │   └── router.py             # Routes tasks to right model tier
│   │
│   ├── slack/                    # Slack bot layer
│   │   ├── __init__.py
│   │   ├── bot.py                # Slack Bolt app, event handlers
│   │   ├── listeners.py          # Message/event listeners per channel
│   │   ├── senders.py            # Message formatting + sending
│   │   └── commands.py           # Slash commands (/research, /brief, /build)
│   │
│   ├── intelligence/             # Message processing pipeline
│   │   ├── __init__.py
│   │   ├── classifier.py         # URGENT/RESEARCH/IDEA/TASK/CHAT classification
│   │   ├── link_processor.py     # URL detection, fetching, summarizing
│   │   ├── media_processor.py    # Voice notes (Whisper), images, PDFs
│   │   └── deduplicator.py       # Message hash dedup, seen-link tracking
│   │
│   ├── research/                 # Research engine
│   │   ├── __init__.py
│   │   ├── engine.py             # Orchestrates multi-source research
│   │   ├── web_search.py         # Brave Search integration
│   │   ├── url_fetcher.py        # Fetch MCP + Puppeteer for JS sites
│   │   ├── pdf_parser.py         # OpenDataLoader PDF integration
│   │   ├── synthesizer.py        # Combines sources into research briefs
│   │   └── topics.py             # Configured research topics + feeds
│   │
│   ├── briefing/                 # Daily briefing system
│   │   ├── __init__.py
│   │   ├── generator.py          # Morning briefing builder
│   │   ├── news_scanner.py       # Overnight news collection
│   │   └── lifestyle.py          # Wake time learning, topic preferences
│   │
│   ├── builder/                  # Tech building coordinator
│   │   ├── __init__.py
│   │   ├── pipeline.py           # Idea -> Spec -> Permission -> Build
│   │   ├── cursor_bridge.py      # Generate plans for Cursor Agent
│   │   ├── claude_code.py        # Claude Code terminal commands
│   │   └── documents.py          # Pitch decks, one-pagers, reports
│   │
│   ├── market/                   # Trading & market intelligence
│   │   ├── __init__.py
│   │   ├── tracker.py            # Watchlist monitoring
│   │   ├── alerts.py             # Price movement alerts
│   │   └── strategy.py           # Trading strategy generation
│   │
│   ├── memory/                   # Persistent memory & learning
│   │   ├── __init__.py
│   │   ├── store.py              # Memory MCP wrapper (knowledge graph)
│   │   ├── user_profile.py       # Per-user preferences, patterns
│   │   └── research_cache.py     # Seen articles, past research, dedup
│   │
│   ├── scheduler/                # Cron jobs & scheduled tasks
│   │   ├── __init__.py
│   │   ├── jobs.py               # Job definitions (briefing, research, alerts)
│   │   ├── runner.py             # APScheduler setup & management
│   │   └── queue.py              # Failed task retry queue
│   │
│   └── utils/                    # Shared utilities
│       ├── __init__.py
│       ├── tokens.py             # Token counting, budget tracking, cost estimates
│       ├── errors.py             # Error handling, circuit breakers
│       ├── cache.py              # URL cache, response cache (TTL-based)
│       └── logging.py            # Structured logging
│
├── mcp_config/                   # MCP server configurations
│   └── servers.json              # MCP server registry & connection settings
│
├── data/                         # Local data (gitignored)
│   ├── research/                 # Saved research reports
│   ├── builds/                   # Generated specs & plans
│   └── cache/                    # URL & response cache
│
├── deploy/                       # Deployment configs
│   ├── railway.toml              # Railway deployment config
│   ├── Procfile                  # Process runner
│   └── Dockerfile                # Container config (optional)
│
├── tests/                        # Tests
│   ├── test_classifier.py
│   ├── test_research.py
│   └── test_briefing.py
│
├── .env.example                  # Template for API keys
├── .env                          # Actual API keys (NEVER committed)
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── GAMEPLAN.md                   # This file
└── README.md
```

---

## WHY SLACK IS YOUR HUB (not WhatsApp directly)

1. **WhatsApp Business API costs money and is locked down.** Meta requires business verification.
2. **Slack has a FREE tier** with full bot API access. Claude can read AND write messages.
3. **The bridge**: You forward important stuff from WhatsApp to Slack, or set up an auto-bridge later.
4. **Your friend joins the same Slack workspace** for free. Both get ALFRED.
5. Slack supports channels, threads, file uploads, slash commands — perfect for a chief of staff.

### The WhatsApp-to-Slack Flow (3 options):

**Option A - Manual Forward (Simplest, Zero Setup) — START HERE**
- You see something interesting in WhatsApp group
- Forward/copy-paste into `#incoming` Slack channel
- ALFRED picks it up automatically, researches it, responds in thread
- Voice notes: record in WhatsApp, save audio file, upload to Slack — ALFRED transcribes via Whisper

**Option B - WhatsApp Web Bridge (Free, Phase 7)**
- Uses `whatsapp-web.js` or Baileys (open source Node.js libraries)
- Connects to your WhatsApp via QR code (like WhatsApp Web)
- Auto-forwards messages from specific groups to Slack channels
- **Voice note handling**: Bridge detects audio messages, downloads `.ogg` file, forwards to Slack, ALFRED auto-transcribes via Whisper
- **Risk**: WhatsApp CAN temp-ban accounts using unofficial APIs. Rare with low volume, but real. Use a secondary number if worried.
- **Mitigation**: Rate-limit forwarding (max 1 message/10 sec), don't send back to WhatsApp, read-only mode

**Option C - Slack as Primary (Cleanest)**
- Move your research conversations to Slack entirely
- WhatsApp stays for casual chat
- ALFRED lives fully in Slack, no bridge risk

**RECOMMENDATION: Start with Option A. Get ALFRED working. Add bridge in Phase 7 only if you actually need it.**

---

## VOICE NOTE HANDLING (Whisper Integration)

This is a real workflow for you — your WhatsApp groups probably have voice notes. Here's how ALFRED handles them:

### How It Works:
1. **Voice note arrives in Slack** (either uploaded manually or forwarded by bridge)
2. ALFRED detects audio file attachment (`.ogg`, `.m4a`, `.mp3`, `.wav`)
3. **Whisper API** transcribes it to text (OpenAI Whisper — free local model OR $0.006/minute via API)
4. ALFRED processes the transcript same as any text message (classify, research, respond)
5. Posts: "Voice note from [person]: [transcript]" + ALFRED's analysis in thread

### Two Whisper Options:

| Option | Cost | Speed | Setup |
|--------|------|-------|-------|
| **Whisper API (OpenAI)** | $0.006/min | Fast (2-3 sec) | Just an API key |
| **Whisper Local (open source)** | Free | Slower (10-30 sec) | Needs GPU or decent CPU |

**RECOMMENDATION**: Start with Whisper API (costs pennies). Switch to local later if volume is high.

### Voice Note Pipeline:
```
Audio file in Slack
  → Download file via Slack API
  → Send to Whisper (API or local)
  → Get transcript text
  → Run through classifier (URGENT/RESEARCH/IDEA/TASK/CHAT)
  → Process like any other message
  → Post transcript + analysis in thread
```

---

## WHAT ALFRED DOES (Feature Breakdown)

### 1. MESSAGE INTELLIGENCE (reads your groups, filters noise)

Not every message matters. ALFRED classifies every message it sees:

| Category | What It Is | What ALFRED Does |
|----------|-----------|-----------------|
| **URGENT** | Time-sensitive, needs your action | Sends you a DM immediately |
| **RESEARCH** | Contains a link or topic worth digging into | Fetches the link, summarizes, adds to research queue |
| **IDEA** | A startup/business idea mentioned | Logs it, does quick viability research, saves to idea bank |
| **TASK** | Something that needs to be done | Creates a task card, asks if you want it planned out |
| **CHAT** | Casual conversation, greetings | Ignores (doesn't waste tokens) |
| **VOICE** | Audio/voice note | Transcribes first via Whisper, then classifies the transcript |

**How it picks**: Claude Haiku reads the message, classifies it using a system prompt. Costs ~$0.001 per classification (basically free). Haiku is used here because classification is a simple task — no need for Sonnet/Opus.

**Link handling**: When someone drops a link in the group:
1. ALFRED detects URL(s) in the message
2. Fetches content using Fetch MCP (or Puppeteer MCP for JS-heavy sites like X/Twitter)
3. If PDF → OpenDataLoader parses it into structured text
4. If paywalled → tries archive.org, then searches for the same topic elsewhere
5. Claude Sonnet summarizes: what is it, why it matters, what you should do about it
6. Posts summary in a thread under the original message
7. If it's a startup opportunity or research finding → queued for daily briefing

### 2. DAILY MORNING BRIEFING ("Good Morning Sir")

Every day at **10:00 AM** (your wake time — ALFRED learns and adjusts over time), ALFRED posts to your `#daily-briefing` channel:

```
Good morning sir. Here's your day:

━━━ TODAY'S PRIORITIES ━━━
1. Review the fertilizer supply chain report your friend shared yesterday
   → Summary attached in thread, key finding: urea prices dropping 8% in Q3
2. Follow up on the AgriTech pitch deck (draft ready for review in #builds)
3. Market update: Potash prices moved +3.2% overnight

━━━ NEW THINGS YOU SHOULD KNOW ━━━
• [Agriculture] India announced new fertilizer subsidy policy — impacts your supply chain
  → Full research report: thread below
• [Tech] New Claude model dropped — implications for ALFRED's own capabilities
• [Science] Phosphate extraction breakthrough published in Nature
  → Potential disruption to current market. Deep dive available.

━━━ IDEAS FROM YESTERDAY'S RESEARCH ━━━
• Idea: AI-powered soil testing marketplace — viability score: 7.2/10
• Idea: WhatsApp-based farmer advisory for South Asia — viability score: 8.1/10

━━━ UNPROCESSED FROM YESTERDAY ━━━
• 3 links in #incoming still need your review
• 1 voice note from [friend] — transcript ready

Reply with a number to deep-dive, or "skip" to move on.
```

**How it works**:
- APScheduler triggers at 10:00 AM (or learned wake time)
- ALFRED collects: unprocessed messages from yesterday, overnight Brave Search results, market data, task list
- Claude Sonnet synthesizes into briefing format
- Posts to `#daily-briefing`
- Waits for your reply to go deeper on anything
- Interactive: "tell me more about 2" → deep dive in thread

**Lifestyle learning**:
- Tracks when you first respond each morning → adjusts briefing time
- Tracks which items you engage with → promotes those topics
- Tracks which items you skip → deprioritizes those topics
- All stored in Memory MCP knowledge graph

### 3. DEEP RESEARCH ENGINE

When you say "research this" or ALFRED finds something worth digging into:

1. **Web Search**: Brave Search MCP — 10-20 queries across different angles
2. **URL Fetching**: Fetch MCP for standard pages, Puppeteer MCP for JS-heavy sites
3. **PDF Analysis**: OpenDataLoader extracts structured data from research papers/reports
4. **Voice Briefings**: If research came from a voice note, includes the transcript context
5. **Synthesis**: Claude Sonnet (or Opus for deep dives) combines all sources into a research brief
6. **Output**: Posts structured report in the relevant Slack channel
7. **Memory**: Saves key findings to knowledge graph so it doesn't re-research the same topic

**Research domains (auto-monitored daily via morning cron)**:
- Fertilizers & chemicals (your main space)
- Agriculture & AgriTech
- Tech & AI (for your projects)
- Science breakthroughs
- Politics (policy that affects your sectors)
- Startup ecosystem news

**Deep research on demand**:
```
You: "deep research on phosphate recycling technologies"
ALFRED: "Starting deep research. Estimated: 15-20 sources, ~$0.12 in tokens. Proceed?"
You: "yes"
ALFRED: [runs 15 searches, reads 8 articles, 2 PDFs, synthesizes]
ALFRED: Posts structured report with:
  - Executive summary
  - Key findings (numbered)
  - Market implications
  - Startup opportunities
  - Sources (all real URLs, verified)
  - Recommended next steps
```

### 4. BUILDER MODE (Tech Ideas → Working Products)

When you describe a tech idea, ALFRED:

1. **Clarifies**: Asks 2-3 questions to understand scope
2. **Specs it out**: Writes a one-page spec document
3. **Estimates cost**: "This will use ~50K tokens (~$0.15). Build with Cursor. Time: ~30 min"
4. **ASKS PERMISSION**: Always. Never builds without your "yes"
5. **Builds it** using:

| Tool | When ALFRED Uses It | How |
|------|-------------------|-----|
| **Cursor** | Complex apps, you want to supervise | Creates plan file → you open in Cursor → Agent executes |
| **Claude Code** | Backend APIs, scripts, automation | Runs Claude Code commands from terminal on Railway |
| **Bolt.new** | Quick prototypes, landing pages | Sends spec to your Bolt.new account |

**Permission model (token saver)**:
```
ALFRED: "I'd like to build the fertilizer price dashboard you described.
         Spec: [link to spec in #builds]
         Cost: ~$0.15 in tokens
         Tool: Cursor (you'll supervise)
         Output: React dashboard + Python API
         Approve? (yes/no/modify)"

You: "yes"
ALFRED: [starts building]
```

ALFRED NEVER spends tokens on building without this approval step.

### 5. DOCUMENT GENERATION

On command, ALFRED creates:

| Document | How |
|----------|-----|
| **Pitch Deck** | Structured markdown (10-12 slides) → you paste into Canva/Google Slides |
| **One-Pager** | Executive summary of any idea, research, or plan |
| **Research Report** | Full deep-dive with sources, data, analysis, recommendations |
| **Business Plan** | Lean canvas or full business plan |
| **Trading Strategy** | Technical + fundamental analysis with entry/exit points |
| **Marketing Plan** | Target audience, channels, messaging, budget |
| **Competitive Analysis** | Market landscape, competitors, positioning |

### 6. TRADING & MARKET INTELLIGENCE

Using Alpaca API + Brave Search:
- Monitor your watchlist (fertilizer companies, tech stocks, commodities)
- Daily market summary baked into morning briefing
- Alert you on big moves (>3% change) via Slack DM
- Generate trading strategy reports on demand
- Backtest ideas using historical data

### 7. MULTI-USER (Your Friend)

Your friend joins the Slack workspace. They get:
- Access to shared channels (`#fertilizer-research`, `#ideas`, `#market-data`)
- Their own DM with ALFRED for personal tasks
- Shared research benefits (one person's research is available to both)
- Collaborative idea development (both can comment on idea threads)
- ALFRED tracks who asked for what — no crossed wires

---

## MCP SERVERS (Correct Package Names)

All MCP servers are open source from `github.com/modelcontextprotocol/servers`:

```json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": { "SLACK_BOT_TOKEN": "xoxb-...", "SLACK_TEAM_ID": "T..." }
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": { "BRAVE_API_KEY": "..." }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/data"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"]
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    }
  }
}
```

**Note**: In production (Railway), ALFRED doesn't use MCP servers as separate processes. Instead, it calls the same APIs directly from Python. MCPs are for local dev and Claude Desktop. The Python code wraps the same functionality (Brave Search API, Slack API, etc.) natively.

---

## COST BREAKDOWN

| Tool | Cost | You Already Pay? |
|------|------|-----------------|
| **Anthropic API** (Claude brain) | ~$10-15/month (usage-based, $5 min top-up) | **NEED TO SET UP** |
| **Cursor** | $20/month | Yes |
| **Claude Code** | Included with Claude sub | Yes |
| **Bolt.new** | Your existing plan | Yes |
| **Slack** | Free tier | Free |
| **Railway** | $5/month | New |
| **Brave Search API** | Free (2,000 queries/month) | Free |
| **OpenAI Whisper API** | $0.006/min (~$1-2/month) | New (or use free local model) |
| **Python + all MCP servers** | Free (open source) | Free |
| **Alpaca API** | Free (paper trading) | Free |

**Total new cost: ~$15-20/month** on top of Cursor + Bolt.new you already pay for.

The $5 Anthropic top-up gets you started. You won't burn through it fast because:
- 80% of calls go to Haiku (dirt cheap)
- Permission gate blocks expensive operations
- Caching prevents duplicate work

---

## BUILD ORDER (Phase by Phase)

### PHASE 1: Foundation (Week 1) — "Get ALFRED Talking"
**Goal**: Claude bot in Slack that can read messages and respond.

**Steps**:
1. **You**: Go to `console.anthropic.com`, create account, add $5 credit
2. **You**: Create Slack workspace (I'll walk you through it — guide below)
3. **You**: Create Slack bot app at `api.slack.com` (guide below)
4. **I build**: Python project scaffolded with the full directory structure above
5. **I build**: Slack Bolt bot that listens to messages in all channels
6. **I build**: Basic Claude integration — messages go to Haiku, responses come back
7. **I build**: ALFRED responds in threads, knows its name, knows you're "sir"
8. **Test**: You paste a message in `#incoming`, ALFRED responds intelligently

**End of Phase 1**: You talk to ALFRED in Slack, it responds.

---

### PHASE 2: Intelligence (Week 2) — "Make It Smart"
**Goal**: ALFRED classifies messages, processes links, remembers things.

1. **Message classifier**: Haiku-powered URGENT/RESEARCH/IDEA/TASK/CHAT/VOICE routing
2. **Link processor**: Detects URLs → Fetch MCP → Claude Sonnet summary → thread reply
3. **Voice note processor**: Detect audio → Whisper transcription → classify transcript → respond
4. **PDF processor**: OpenDataLoader integration for research documents
5. **Memory system**: Memory MCP knowledge graph — remembers what you care about
6. **Deduplication**: Same link won't be processed twice

**End of Phase 2**: ALFRED is genuinely useful — processes links, transcribes voice notes, filters noise.

---

### PHASE 3: Daily Briefing (Week 3) — "Good Morning Sir"
**Goal**: Personalized morning briefing at 10 AM every day.

1. **APScheduler**: Cron job triggers at 10:00 AM
2. **News scanner**: Brave Search checks your configured topics overnight
3. **Briefing generator**: Claude Sonnet synthesizes everything into morning briefing
4. **Interactive follow-up**: Reply with a number → deep dive in thread
5. **Lifestyle learning**: Track your response patterns, adjust timing and topics

**End of Phase 3**: You wake up to a personalized briefing daily.

---

### PHASE 4: Research Engine (Week 4) — "Your Personal Analyst"
**Goal**: Deep research on demand + auto-research on your sectors.

1. **Auto-research cron**: Daily scans on fertilizers, agriculture, tech, science, politics
2. **Deep research command**: `/research phosphate recycling` → full report
3. **Startup idea generator**: Scores opportunities from research findings
4. **Shared research**: `#fertilizer-research` for you + friend
5. **Research memory**: Never researches the same thing twice

**End of Phase 4**: ALFRED is a research analyst covering your sectors daily.

---

### PHASE 5: Builder Mode (Weeks 5-6) — "Idea to Product"
**Goal**: Describe an idea → ALFRED specs it → asks permission → builds it.

1. **Idea pipeline**: Clarify → Spec → Estimate → Permission → Build
2. **Cursor bridge**: ALFRED writes plans for Cursor Agent to execute
3. **Claude Code integration**: Direct terminal builds for scripts/APIs
4. **Document generation**: Pitch decks, one-pagers, research reports, business plans

**End of Phase 5**: Idea to working prototype + pitch deck in a day.

---

### PHASE 6: Market Intelligence (Weeks 6-7) — "Money Moves"
**Goal**: Stock/commodity monitoring, alerts, trading strategies.

1. **Alpaca integration**: Watchlist for fertilizer stocks, tech, commodities
2. **Alert system**: >3% moves → immediate DM
3. **Strategy generator**: Technical + fundamental analysis on demand
4. **Morning briefing integration**: Market summary baked into daily brief

**End of Phase 6**: Market intelligence woven into your daily flow.

---

### PHASE 7: Polish & Expand (Weeks 7-8) — "Full Power"
**Goal**: WhatsApp bridge, token optimization, fine-tuning.

1. **WhatsApp bridge** (optional): `whatsapp-web.js` auto-forwards group messages to Slack
2. **Token optimization**: Response caching, smarter model routing
3. **Fine-tuning** (optional, using Unsloth): Custom model for fertilizer/agriculture classification
4. **Slash commands**: `/brief`, `/research [topic]`, `/build [idea]`, `/market [ticker]`

**End of Phase 7**: ALFRED is at full power.

---

## ERROR HANDLING & EDGE CASES

| Error | What ALFRED Does |
|-------|-----------------|
| **Slack API down** | Queues messages locally in SQLite, retries every 5 min, logs to `data/` |
| **Claude API down** | Posts: "Brain is resting. Queued for when I'm back." Processes queue on recovery |
| **Claude API rate limit** | Exponential backoff (1s → 2s → 4s → 8s). Prioritizes URGENT over RESEARCH |
| **Token budget exceeded** | Daily budget cap (configurable). Warns at 80%. Stops non-essential at 100%. Resets at midnight |
| **Bad URL / dead link** | Tries archive.org fallback. If still dead: "Link broken. Searched for the topic instead: [results]" |
| **Paywalled article** | Fetches what it can, searches for same topic from free sources |
| **PDF can't be parsed** | OCR fallback attempt. If still fails: "Couldn't parse. File saved for manual review" |
| **Voice note too long (>10 min)** | Chunks into segments, transcribes each, combines. Warns about higher cost before processing |
| **Voice note bad quality** | Whisper still works (it's robust). If truly garbled: "Transcript uncertain, here's my best attempt: [text]" |
| **WhatsApp bridge disconnects** | Sends "WhatsApp disconnected — re-scan QR code" to Slack. Auto-reconnect for 1 hour |
| **Duplicate messages** | SHA-256 hash dedup. Same message/link won't be processed twice within 24 hours |
| **Spam/noise in group** | CHAT classification = ignored. Adjustable threshold in config |
| **Friend sends conflicting instruction** | ALFRED asks for clarification, tags both users: "I got different requests from you two — who should I prioritize?" |
| **Research finds nothing new** | Honest: "Searched 12 sources, nothing new today on [topic]. Last significant update was [date]" |
| **Build fails midway** | Saves progress to `data/builds/`, reports error with stack trace, asks: "Retry, modify approach, or abandon?" |
| **Railway server crash** | Auto-restarts via Railway. State persisted in SQLite + filesystem. Picks up where it left off |
| **Memory storage full** | Memory MCP prunes old low-relevance entries. Critical memories are never pruned |
| **X/Twitter link (JS-heavy)** | Puppeteer MCP renders the page, extracts text. Falls back to Brave Search for the tweet content |
| **Multiple links in one message** | Processes each link separately, posts summary for each in the same thread |
| **Message in non-English** | Claude handles multilingual natively. Responds in the language you message in, or English if you prefer |

---

## TOKEN SAVING STRATEGY

### The Three Gates:

1. **Classification Gate**: Haiku classifies every message. If it's CHAT → stop. Costs $0.001. This alone saves 60-70% of would-be token spend.

2. **Permission Gate**: ALFRED NEVER does expensive operations without asking:
   - Deep research (>5 searches) → asks first
   - Building anything → asks first with cost estimate
   - Document generation → asks first
   - Voice note >5 min → warns about cost

3. **Cache Gate**: Before researching, checks cache:
   - URL content cached 24 hours
   - Research results cached 7 days
   - Brave Search results cached 12 hours
   - Classification results cached per message hash

### Tiered Model Routing:

| Model | Used For | Cost | % of Calls |
|-------|---------|------|-----------|
| **Haiku 4.5** | Classification, simple Q&A, acknowledgments | $0.25/1M input | ~80% |
| **Sonnet 4.6** | Research summaries, briefings, planning, link analysis | $3/1M input | ~18% |
| **Opus 4.6** | Deep analysis, complex strategy, important documents | $15/1M input | ~2% |

### Estimated Monthly Spend:
- 100 classifications/day (Haiku): **~$0.30/month**
- 5 research tasks/day (Sonnet): **~$5/month**
- 1 deep task/day (Opus): **~$3/month**
- Morning briefing (Sonnet): **~$2/month**
- Voice transcription (Whisper): **~$1/month**
- **Total: ~$11-15/month in API costs**

---

## SLACK WORKSPACE SETUP GUIDE

Here's exactly what to do:

### Step 1: Create the Workspace
1. Go to `slack.com/get-started#/createnew`
2. Enter your email, verify
3. Workspace name: "ALFRED HQ" (or whatever you want)
4. Skip the onboarding tour

### Step 2: Create Channels
Create these channels (all public):
- `#incoming` — Drop links, messages, voice notes here for ALFRED to process
- `#daily-briefing` — Morning briefings land here
- `#research` — General research outputs
- `#fertilizer-research` — Fertilizer/chemical specific research (shared with friend)
- `#ideas` — Startup ideas and opportunity scoring
- `#market-data` — Trading/market intelligence
- `#builds` — Tech building requests and outputs
- `#alfred-logs` — ALFRED's internal logs (for debugging)

### Step 3: Create the ALFRED Bot
1. Go to `api.slack.com/apps`
2. Click "Create New App" → "From scratch"
3. App name: "ALFRED", workspace: your workspace
4. Go to **OAuth & Permissions** → Bot Token Scopes, add:
   - `channels:history` (read messages)
   - `channels:read` (list channels)
   - `chat:write` (send messages)
   - `files:read` (read uploaded files/voice notes)
   - `im:history` (read DMs)
   - `im:write` (send DMs)
   - `reactions:write` (react to messages)
   - `users:read` (identify who sent what)
5. Go to **Event Subscriptions** → Enable → Subscribe to:
   - `message.channels` (messages in channels)
   - `message.im` (DMs to ALFRED)
   - `file_shared` (file uploads including voice notes)
6. Install the app to your workspace
7. Copy the **Bot User OAuth Token** (starts with `xoxb-`)
8. Copy the **Signing Secret** from Basic Information

### Step 4: Invite Your Friend
- Send them the Slack workspace invite link
- They join the shared channels
- They can DM ALFRED for personal tasks too

### Step 5: Get Your API Keys
1. **Anthropic**: `console.anthropic.com` → Create account → Add $5 credit → Copy API key
2. **Brave Search**: `brave.com/search/api/` → Free tier → Copy API key
3. **OpenAI** (for Whisper): `platform.openai.com` → API keys → Create key (or we use free local Whisper)

---

## WHAT I NEED FROM YOU (Updated Checklist)

### Before I Start Coding:
- [ ] **Anthropic API key** — go to `console.anthropic.com`, add $5, copy key
- [ ] **Slack workspace created** — follow guide above, send me the Bot Token + Signing Secret
- [ ] **Brave Search API key** — free at `brave.com/search/api/`

### Can Add Later:
- [ ] OpenAI API key (for Whisper voice notes) — or we use free local Whisper
- [ ] Alpaca API key (for market data) — free at `alpaca.markets`
- [ ] Your friend's Slack username (once they join)
- [ ] Specific fertilizer companies/tickers to track
- [ ] Bolt.new API access (for builder mode)

### Already Decided:
- ALFRED calls you: **"sir"**
- Wake time: **10:00 AM**
- Runs on: **Railway ($5/month)**
- Dev environment: **Mac + Cursor**

---

## OPEN SOURCE REPOS USED

| Repo | Purpose |
|------|---------|
| `github.com/modelcontextprotocol/servers` | Official MCP servers (Slack, Fetch, Memory, Filesystem, Git, Brave Search, Puppeteer) |
| `github.com/anthropics/anthropic-sdk-python` | Python SDK for Claude API |
| `github.com/opendataloader-project/opendataloader-pdf` | PDF parsing for research documents |
| `github.com/unslothai/unsloth` | Fine-tune custom models (Phase 7 - optional) |
| `github.com/openai/whisper` | Local voice transcription (free alternative to Whisper API) |
| `github.com/nicekui/whatsapp-mcp` | WhatsApp bridge (Phase 7 - optional) |
| `github.com/punkpeye/awesome-mcp-servers` | Directory of community MCP servers for future expansion |
| `Slack Bolt for Python` | Official Slack bot framework |
| `APScheduler` | Python cron job scheduling |

---

## THE HONEST TRUTH

**What ALFRED CAN do:**
- Be a genuinely useful AI chief of staff in Slack
- Research, summarize, plan, and brief you daily
- Transcribe voice notes and process them like text
- Build tech prototypes when you ask
- Monitor your sectors and surface opportunities
- Track markets and alert on big moves
- Generate pitch decks, reports, plans
- Work for both you and your friend
- Learn your patterns and get better over time

**What ALFRED CAN'T do:**
- Replace a human chief of staff (no emotional intelligence, no relationship building)
- Auto-trade stocks (always get your approval first — legal + practical reasons)
- Guarantee research accuracy (always verify important findings via source URLs)
- Work natively on WhatsApp without some jank (Slack-first is the way)
- Read your mind (the better you communicate with it, the better it gets)

**What could go wrong:**
- WhatsApp unofficial bridge could get temp-banned (rare, mitigated by rate limiting)
- Claude API costs could spike on a heavy research day (budget caps prevent this)
- Research could cite hallucinated sources (we always include and verify real URLs)
- Whisper could mis-transcribe heavily accented speech (confidence scores help flag this)

---

## NEXT STEP

Get me those 3 keys and I start building Phase 1 immediately:

1. **Anthropic API key** → `console.anthropic.com`
2. **Slack Bot Token** → follow the Slack setup guide above
3. **Brave Search API key** → `brave.com/search/api/`

Once I have those, I scaffold the entire project and have ALFRED talking in Slack within one session.
