# ALFRED Setup Guide — Rebuilt with Claude Managed Agents

## What Changed

ALFRED has been rebuilt to use Claude's latest capabilities:

- **Managed Agents** — deep research and briefings run as autonomous agent sessions on Anthropic's cloud. The agent has web_search, web_fetch, bash, and file tools built in.
- **Native web_search** — replaces Brave Search API entirely. No more Brave API key needed.
- **Web search fallback** — if a direct URL fetch fails (paywall, JS-heavy), Claude searches for the topic automatically.
- **Graceful degradation** — ALFRED works without Managed Agents (falls back to regular API calls with web_search tool). Set up the agent for full power.

## Step 1: Get Your API Keys (5 minutes)

### Anthropic API Key (REQUIRED)
1. Go to https://console.anthropic.com
2. Create an account → **Billing** → Add $5 credit
3. **API Keys** → Create new key → Copy (starts with `sk-ant-`)

### Slack Bot (REQUIRED)
1. Go to https://slack.com/get-started#/createnew
2. Create workspace: "ALFRED HQ"
3. Create channels: `#incoming`, `#daily-briefing`, `#research`, `#fertilizer-research`, `#ideas`, `#market-data`, `#builds`, `#alfred-logs`
4. Go to https://api.slack.com/apps → "Create New App" → "From scratch"
5. App name: **ALFRED**, select your workspace
6. **OAuth & Permissions** → Add Bot Token Scopes:
   - `app_mentions:read`, `channels:history`, `channels:read`, `chat:write`
   - `files:read`, `im:history`, `im:read`, `im:write`
   - `reactions:write`, `users:read`
7. **Event Subscriptions** → Enable → Subscribe to:
   - `app_mention`, `message.channels`, `message.im`, `file_shared`
8. **Socket Mode** → Enable → Generate app-level token (`connections:write` scope) → Copy (`xapp-...`)
9. **Install App** → Install to Workspace → Copy Bot Token (`xoxb-...`)
10. **Basic Information** → Copy Signing Secret
11. In Slack: `/invite @ALFRED` in each channel

## Step 2: Configure ALFRED (2 minutes)

```bash
cd /Users/param/Downloads/fatima
cp .env.example .env
```

Edit `.env` with your keys:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-socket-token
```

**That's it.** No Brave Search key needed anymore.

## Step 3: Install Dependencies (1 minute)

```bash
cd /Users/param/Downloads/fatima
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Step 4: Create the Managed Agent (RECOMMENDED)

This gives ALFRED full autonomous research powers:

```bash
source .venv/bin/activate
python -m alfred.setup_agent
```

This creates the agent + environment on Anthropic's cloud and auto-updates your `.env`.

**If this fails** (e.g., API key doesn't have Managed Agents access), ALFRED still works — it falls back to regular API calls with web_search. You can set up the agent later.

## Step 5: Launch ALFRED

```bash
source .venv/bin/activate
python -m alfred.main
```

You should see:
```
ALFRED — AI Chief of Staff — Starting Up
Initializing brain (Claude API)...
Initializing memory store...
Initializing intelligence layer...
Initializing research engine...
Initializing briefing generator...
Managed Agent configured: agent_01XX...
Starting scheduler...
Starting Slack bot (Socket Mode)...
ALFRED is ready. Listening for messages...
```

## Step 6: Test It

1. Go to `#incoming` → Paste a link → ALFRED summarizes in-thread
2. `@ALFRED what can you do?` → It responds
3. `@ALFRED research phosphate recycling` → Deep research via Managed Agent
4. Share a startup idea → ALFRED scores it

## Architecture Overview

```
Message arrives in Slack
    ↓
Classify with Haiku ($0.001) → CHAT? Ignore.
    ↓
URGENT → Quick response (Sonnet)
RESEARCH → Links: fetch + summarize | No links: Agent session
IDEA → Score (Sonnet)
TASK → Acknowledge + clarify (Sonnet)
    ↓
Deep research / briefings → Managed Agent session
  (web_search + web_fetch + bash on Anthropic's cloud)
    ↓
Results posted to Slack
```

## Two Operating Modes

| Mode | When | How |
|------|------|-----|
| **Full (Managed Agent)** | `ALFRED_AGENT_ID` and `ALFRED_ENVIRONMENT_ID` set | Deep research + briefings use autonomous agent sessions |
| **Lite (API only)** | No agent IDs | Falls back to regular API calls with web_search tool |

## Dependencies Removed (vs. old version)

- ~~Brave Search API key~~ → Replaced by Claude's native web_search
- ~~`aiohttp`~~ → Not needed
- ~~`PyPDF2`~~ → Removed (future phase)
- ~~`diskcache`~~ → Removed (memory store handles caching)

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Missing required env vars" | Check `.env` has all 4 required keys |
| "Managed Agent not configured" | Run `python -m alfred.setup_agent` |
| Slack bot doesn't respond | Socket Mode enabled? ALFRED invited to channel? |
| "Rate limited" | Wait a minute, or increase `ALFRED_DAILY_TOKEN_BUDGET` |
| Agent session takes too long | Normal for deep research (1-2 min). Check `#alfred-logs` |
