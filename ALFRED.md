# ALFRED — Complete Knowledge Base & Build Guide

## Last Updated: April 24, 2026

This file is the **single source of truth** for ALFRED's architecture, capabilities, API knowledge, and build roadmap. It captures everything researched and decided during the initial build sessions. Any AI agent working on this codebase should read this file first.

---

## WHO IS ALFRED

ALFRED is a personal **AI Chief of Staff** that lives in Slack. Built for Batman (the boss) and his partner.

**Domain focus:** Fertilizers, agriculture, AgriTech, India policy, tech/AI/science, startup ideation.

**Core principle:** No n8n. No Zapier. No new platforms. Just Python + Claude API + Slack.

---

## ARCHITECTURE (Current — v2)

```
Message arrives in Slack
    ↓
[SLIM SLACK LISTENER] — Python + Slack Bolt (Socket Mode)
    ↓
Classify with Haiku ($0.001/call) → CHAT? Ignore.
    ↓
┌─────────────────────────────────────────────────┐
│ TIER 1: Regular API (messages.create)           │
│   - Classification (Haiku, no tools)            │
│   - Chat responses (Sonnet, no tools)           │
│   - Idea scoring (Sonnet, no tools)             │
│   - Link summaries (Sonnet, no tools)           │
│   - Quick research (Sonnet + web_search tool)   │
│   * ALL calls use prompt caching                │
│     (system prompt cached, 90% cost reduction)  │
├─────────────────────────────────────────────────┤
│ TIER 2: Managed Agent Sessions                  │
│   - Deep research (autonomous multi-step)       │
│   - Morning briefings (topic scan + synthesis)  │
│   - Building tasks (Phase 5)                    │
│   * Runs on Anthropic's cloud containers        │
│   * Has: web_search, web_fetch, bash,           │
│     read/write/edit, glob/grep                  │
│   * Supports MCP servers + custom tools         │
└─────────────────────────────────────────────────┘
    ↓
Results posted to Slack channels
```

### Why Two Tiers?

- **Tier 1** is for fast, cheap operations. A classification costs ~$0.001. A chat response costs ~$0.01. Prompt caching means the system prompt is read from cache at 10% cost after the first call.
- **Tier 2** is for tasks that need autonomy — the agent decides what to search, what pages to read, and synthesizes multi-source reports. Each session spins up a container on Anthropic's cloud.

---

## TECH STACK

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | Python 3.11+ | Everything |
| AI API | Anthropic Claude API | All intelligence |
| AI Agent | Claude Managed Agents (beta) | Autonomous research/briefings |
| Bot Framework | Slack Bolt + Socket Mode | Real-time Slack integration |
| Scheduling | APScheduler | Cron jobs (briefing, token reset) |
| URL Fetching | httpx + BeautifulSoup4 | Direct link processing |
| Web Search | Claude native web_search tool | Replaces Brave Search entirely |
| Memory | JSON file (data/memory.json) | Persistence across restarts |
| Config | python-dotenv | Environment variables |
| Deploy | Railway ($5/month) | Always-on worker process |

### What We Removed (vs. v1)

| Removed | Replaced By |
|---------|------------|
| Brave Search API + key | Claude's native `web_search_20260209` tool |
| `aiohttp` | Not needed |
| `PyPDF2` | Deferred to future phase |
| `diskcache` | Memory store handles caching |
| `brain/router.py` | Tiered architecture handles routing |
| `intelligence/deduplicator.py` | Built into memory store |
| `research/web_search.py` | Claude web_search tool |
| `utils/tokens.py` | Less relevant with managed agents |

---

## API CAPABILITIES DISCOVERED (April 2026)

### 1. Claude Managed Agents API

**Endpoint:** `POST /v1/agents` (beta: `managed-agents-2026-04-01`)

Three primitives:
- **Agent** — reusable config: model + system prompt + tools + MCP servers + skills. Created once, referenced by ID.
- **Environment** — container template on Anthropic's cloud (networking, packages).
- **Session** — running instance. Send a message, agent works autonomously, streams events back.

**Built-in agent tools** (`agent_toolset_20260401`):

| Tool | Name | What It Does |
|------|------|-------------|
| Bash | `bash` | Execute shell commands |
| Read | `read` | Read files |
| Write | `write` | Write files |
| Edit | `edit` | String replacement in files |
| Glob | `glob` | File pattern matching |
| Grep | `grep` | Regex text search |
| Web Fetch | `web_fetch` | Fetch URL content |
| Web Search | `web_search` | Search the web |

**Agent lifecycle:**
- Create → returns `id` + `version`
- Update → pass `version` for optimistic concurrency, increments version
- List versions → full history
- Archive → read-only, existing sessions continue

**MCP Connector:**
- Agents can connect to remote MCP servers (up to 20)
- Declared at agent creation: `mcp_servers: [{type: "url", name: "github", url: "..."}]`
- Auth provided at session creation via `vault_ids`
- Vaults store credentials separately from agent config

**Custom Tools:**
- Define tools with JSON schema on the agent
- Agent emits `agent.custom_tool_use` events
- Your code executes and sends results back via `user.custom_tool_result`
- Great for: Slack posting, database queries, external APIs

**Session events:**
- `agent.message` — text output from the agent
- `agent.tool_use` — agent is using a built-in tool
- `agent.custom_tool_use` — agent wants YOUR code to run a custom tool
- `session.status_idle` — agent is done
- `session.error` — something went wrong

### 2. Prompt Caching

**How it works:** Cache the system prompt prefix. Subsequent calls read from cache at 10% of input cost.

**Two modes:**
- **Automatic:** `cache_control={"type": "ephemeral"}` at request level. System places breakpoint on last cacheable block automatically.
- **Explicit:** Place `cache_control` on specific content blocks for fine-grained control.

**Pricing (Sonnet 4.6):**
| Type | Cost |
|------|------|
| Base input | $3/MTok |
| 5min cache write | $3.75/MTok (1.25x) |
| Cache read | $0.30/MTok (0.1x — **90% savings**) |
| 1hr cache write | $6/MTok (2x) |

**Minimum cacheable length:** 2048 tokens for Sonnet 4.6, 4096 for Haiku 4.5.

**Cache lifetime:** 5 minutes default, refreshed on each hit. Optional 1-hour TTL at 2x cost.

**What we cache in ALFRED:** The SYSTEM_PROMPT is sent with every API call. With ~100+ calls/day, caching it saves ~90% on those input tokens.

### 3. Native Web Search Tool

**Tool type:** `web_search_20260209`

```python
tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 5}]
```

- Claude decides when to search autonomously
- Returns cited responses with source URLs
- Supports domain filtering (`allowed_domains`, `blocked_domains`)
- Supports localization (`user_location` for India-specific results)
- Iterative searching — uses results from one query to refine the next
- Dynamic filtering with code execution for result relevance

**Replaces:** Brave Search API, manual httpx fetching, BeautifulSoup parsing for research.
**Kept:** httpx + BS4 for direct link processing (someone pastes a specific URL).

### 4. Claude Code Routines

**What:** Saved Claude Code configs that run on Anthropic's cloud on a schedule, via API, or on GitHub events.

**API trigger:**
```bash
curl -X POST https://api.anthropic.com/v1/claude_code/routines/{trigger_id}/fire \
  -H "Authorization: Bearer {token}" \
  -H "anthropic-beta: experimental-cc-routine-2026-04-01" \
  -d '{"text": "Run morning briefing"}'
```

**Potential use:** Morning briefing, daily research scans, health checks — without APScheduler.
**Status:** Not yet integrated. APScheduler handles scheduling for now.
**Requires:** Claude Pro/Max subscription (included, no extra cost).

### 5. Claude Agent SDK

**Package:** `pip install claude-agent-sdk`

```python
from claude_agent_sdk import query

async for message in query(prompt="Build a dashboard"):
    print(message)
```

**Use case:** ALFRED's builder arm (Phase 5). When someone says "build me X", spawn a Claude Code session via the SDK.
**Status:** Not yet integrated. Planned for Phase 5.

### 6. Memory Frameworks (Researched, Not Yet Integrated)

| Framework | Approach | Best For |
|-----------|----------|----------|
| **Mem0** | Auto-extracts memories, graph backend | Personalization |
| **Letta (MemGPT)** | Agent manages its own memory | Autonomous agents |
| **Zep** | Production-grade sessions + long-term | Multi-user apps |
| **Cognee** | Structured memory with reasoning | Complex domains |

**Recommendation:** Mem0 is the best fit for ALFRED — Python-native, auto-extracts memories, supports knowledge graph backend (FalkorDB).
**Status:** Not yet integrated. Currently using JSON file store. Upgrade planned.

---

## FILE STRUCTURE

```
fatima/
├── alfred/
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
│   ├── slack/                    # Slack I/O
│   │   ├── __init__.py
│   │   ├── bot.py                # Event handlers (classify → route → respond)
│   │   └── senders.py            # Post to channels/DMs by name
│   │
│   ├── intelligence/             # Message processing
│   │   ├── __init__.py
│   │   ├── classifier.py         # Haiku classification with hash cache
│   │   └── link_processor.py     # URL fetch + summarize + web_search fallback
│   │
│   ├── research/                 # Research capabilities
│   │   ├── __init__.py
│   │   └── engine.py             # Deep research (agent) + quick research (API)
│   │
│   ├── briefing/                 # Daily briefing
│   │   ├── __init__.py
│   │   └── generator.py          # Morning briefing via Managed Agent session
│   │
│   ├── memory/                   # Persistence
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
├── data/                         # Runtime data (gitignored)
│   ├── memory.json
│   ├── cache/
│   ├── research/
│   └── builds/
│
├── deploy/
│   ├── Procfile                  # worker: python -m alfred.main
│   └── railway.toml              # Nixpacks, auto-restart
│
├── .env.example                  # Template for API keys
├── .env                          # Actual keys (gitignored)
├── .gitignore
├── requirements.txt              # anthropic, slack-bolt, apscheduler, httpx, bs4, dotenv
├── pyproject.toml
├── GAMEPLAN.md                   # Original vision document (7 phases)
├── ALFRED.md                     # THIS FILE — complete knowledge base
└── SETUP.md                      # Quick-start setup guide
```

---

## PHASES & ROADMAP

### Phase 1: Foundation — "ALFRED Talks" ✅ DONE

**What's built:**
- Slack bot (Socket Mode) listens in all channels
- Message classification (Haiku — URGENT/RESEARCH/IDEA/TASK/CHAT)
- Link fetching + summarization (httpx + BS4 + Sonnet)
- Web search fallback when direct fetch fails
- @ALFRED direct conversation
- Idea scoring
- Morning briefing at configured wake time
- Daily token budget tracking + midnight reset
- Health checks every 30 minutes
- JSON memory store with dedup
- Prompt caching on all API calls
- Managed Agent integration for deep research + briefings
- Deployed on Railway

**What you need:**
- `ANTHROPIC_API_KEY` — required
- `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `SLACK_APP_TOKEN` — required
- `ALFRED_AGENT_ID`, `ALFRED_ENVIRONMENT_ID` — optional (created by `setup_agent.py`)

### Phase 2: Intelligence — "Make It Smart"

**What to build:**
- [ ] Voice note transcription (Whisper API — $0.006/min)
- [ ] PDF parsing for research documents
- [ ] Enhanced memory with Mem0 (auto-learns from conversations)
- [ ] Lifestyle learning (track when Batman responds, adjust briefing time)
- [ ] Interactive briefing follow-up ("tell me more about 2")

**Tech needed:**
- `openai` package for Whisper API (or local Whisper)
- `mem0ai` package for intelligent memory
- PDF extraction library (PyMuPDF or similar)

### Phase 3: Research Engine — "Personal Analyst"

**What to build:**
- [ ] Auto-research cron (daily scans on tracked topics via agent sessions)
- [ ] `/research [topic]` slash command
- [ ] Research history browsing
- [ ] Startup idea generator from research findings
- [ ] Collaborative research channels (shared with partner)

**Tech needed:**
- Slash command handlers in Slack bot
- Enhanced memory for research dedup across days

### Phase 4: Web Dashboard — "Control Center" 🆕

**What to build:**
- [ ] Web UI to browse research history, idea bank, memory
- [ ] Settings panel (wake time, topics, model preferences)
- [ ] Token usage dashboard
- [ ] Research search (find past reports)
- [ ] Agent session viewer (see what ALFRED did)

**Tech needed:**
- Next.js or FastAPI + React frontend
- Auth (simple password or Slack OAuth)
- Reads from `data/memory.json` or future database

### Phase 5: Builder Mode — "Idea to Product"

**What to build:**
- [ ] Describe idea → ALFRED specs it out
- [ ] Permission gate before building
- [ ] Claude Code SDK integration for code generation
- [ ] Document generation (pitch decks, reports, business plans)
- [ ] Custom tools on Managed Agent for Slack posting during builds

**Tech needed:**
- `claude-agent-sdk` package
- Custom tools on the Managed Agent definition
- Build queue/tracking in memory

### Phase 6: Market Intelligence — "Money Moves"

**What to build:**
- [ ] Alpaca API integration (stocks, commodities, fertilizer companies)
- [ ] Watchlist monitoring
- [ ] Alert system (>3% moves → DM)
- [ ] Trading strategy reports
- [ ] Market data in morning briefing

**Tech needed:**
- `alpaca-trade-api` package
- Market data in briefing template

### Phase 7: Polish & Expand — "Full Power"

**What to build:**
- [ ] WhatsApp bridge (optional — `whatsapp-web.js`)
- [ ] MCP servers on Managed Agent (GitHub, Notion, Slack MCP)
- [ ] Claude Code Routines for scheduled tasks (replace APScheduler)
- [ ] Fine-tuning with Unsloth (optional — custom fertilizer model)
- [ ] Multi-agent orchestration (callable_agents on Managed Agent)

**Tech needed:**
- MCP server URLs for third-party integrations
- Vault setup for MCP auth
- Routine setup on claude.ai

---

## COST BREAKDOWN (Current)

| Item | Monthly Cost |
|------|-------------|
| Anthropic API (with caching) | ~$8-12 |
| Railway hosting | $5 |
| Slack | Free |
| **Total** | **~$13-17/month** |

**Cost savings from v2 rebuild:**
- Prompt caching saves ~40-60% on input tokens (system prompt cached at 10% cost)
- No Brave Search API (free tier was limited anyway)
- Haiku for 80% of calls ($0.001 each)
- Managed Agent only for heavy tasks (~2-3 sessions/day)

**Alternative: Claude Max subscription ($100-200/month)**
- Includes Claude Code + Routines (replaces Railway + APScheduler)
- Includes API usage (replaces per-token billing)
- Worth evaluating if daily usage exceeds ~$5/day in API costs

---

## KEY DECISIONS LOG

| Decision | Rationale |
|----------|-----------|
| Python, not Node.js | Batman's team works in Python. Anthropic SDK is Python-first. |
| Slack, not WhatsApp | Free API, full bot support, channels/threads, file uploads. WhatsApp bridge possible in Phase 7. |
| Socket Mode, not webhooks | No public URL needed. Works behind NAT/firewalls. Simpler on Railway. |
| Managed Agents for research | Agent autonomously searches, fetches, reads, synthesizes. No manual pipeline. |
| Regular API for classification | Haiku is dirt cheap. No need for a container just to classify a message. |
| Prompt caching on all calls | System prompt sent 100+ times/day. Caching at 10% cost is an easy win. |
| JSON file for memory | Zero setup. Works on Railway. Good enough for Phase 1-3. Mem0 upgrade planned. |
| httpx + BS4 for links | Direct URL fetching is fast and free. Web search fallback handles failures. |
| Batman, not sir | Because Batman said so. |

---

## ENVIRONMENT VARIABLES

```bash
# REQUIRED
ANTHROPIC_API_KEY=sk-ant-...         # Claude API access
SLACK_BOT_TOKEN=xoxb-...             # Slack bot identity
SLACK_SIGNING_SECRET=...             # Request verification
SLACK_APP_TOKEN=xapp-...             # Socket Mode connection

# MANAGED AGENT (created by setup_agent.py)
ALFRED_AGENT_ID=agent_...            # Managed Agent ID
ALFRED_ENVIRONMENT_ID=env_...        # Container environment ID

# OPTIONAL
OPENAI_API_KEY=sk-...                # Whisper (Phase 2)
ALPACA_API_KEY=...                   # Market data (Phase 6)
ALPACA_SECRET_KEY=...                # Market data (Phase 6)

# BEHAVIOR
ALFRED_WAKE_TIME=10:00               # Morning briefing time
ALFRED_TIMEZONE=Asia/Kolkata         # Timezone for scheduling
ALFRED_DAILY_TOKEN_BUDGET=500000     # Daily token limit
ALFRED_LOG_LEVEL=INFO                # Logging verbosity
```

---

## QUICK COMMANDS

```bash
# Install
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Create Managed Agent (one-time)
python -m alfred.setup_agent

# Run ALFRED
python -m alfred.main

# Deploy to Railway
# Push to GitHub → Railway auto-deploys from deploy/railway.toml
```

---

## FUTURE CONSIDERATIONS

1. **Serverless migration** — Railway runs 24/7 but ALFRED only does work when messages arrive or cron fires. A serverless function for Slack events + Routines for cron could reduce costs to near-zero.

2. **Database migration** — JSON file works now but won't scale past 6 months of daily use. SQLite (local) or Supabase (hosted) are the natural next steps.

3. **Web dashboard** — Slack is great for real-time but searching past research is painful. A simple web UI for browsing history, ideas, and memory is planned for Phase 4.

4. **Multi-agent** — Managed Agents supports `callable_agents` (research preview). ALFRED could have sub-agents: a researcher, a builder, a market analyst — orchestrated by the main ALFRED agent.

5. **MCP ecosystem** — As more services expose MCP endpoints (GitHub, Notion, Linear, Jira), ALFRED can connect to them natively via the MCP connector on Managed Agents. No custom integration code needed.
