# ALFRED Setup Guide — Get Running in 15 Minutes

## Step 1: Get Your API Keys (5 minutes)

### Anthropic API Key (REQUIRED)
1. Go to https://console.anthropic.com
2. Create an account (email + password)
3. Go to **Billing** → Add $5 credit (minimum)
4. Go to **API Keys** → Create new key
5. Copy the key (starts with `sk-ant-`)

### Slack Bot (REQUIRED)
1. Go to https://slack.com/get-started#/createnew
2. Create workspace: "ALFRED HQ" (or any name)
3. Create these channels: `#incoming`, `#daily-briefing`, `#research`, `#fertilizer-research`, `#ideas`, `#market-data`, `#builds`, `#alfred-logs`
4. Go to https://api.slack.com/apps → "Create New App" → "From scratch"
5. App name: **ALFRED**, select your workspace
6. Go to **OAuth & Permissions** → Add these Bot Token Scopes:
   - `app_mentions:read`
   - `channels:history`
   - `channels:read`
   - `chat:write`
   - `files:read`
   - `im:history`
   - `im:read`
   - `im:write`
   - `reactions:write`
   - `users:read`
7. Go to **Event Subscriptions** → Enable Events → Subscribe to bot events:
   - `app_mention`
   - `message.channels`
   - `message.im`
   - `file_shared`
8. Go to **Socket Mode** → Enable Socket Mode → Generate an app-level token (name it "alfred-socket"), give it `connections:write` scope → Copy the token (starts with `xapp-`)
9. Go to **Install App** → Install to Workspace → Copy the **Bot User OAuth Token** (starts with `xoxb-`)
10. Go to **Basic Information** → Copy the **Signing Secret**
11. **Invite ALFRED to your channels**: In Slack, go to each channel → type `/invite @ALFRED`

### Brave Search API Key (REQUIRED for research)
1. Go to https://brave.com/search/api/
2. Sign up for free plan (2,000 queries/month)
3. Copy the API key

## Step 2: Configure ALFRED (2 minutes)

In your terminal:
```bash
cd /Users/param/Downloads/fatima
cp .env.example .env
```

Open `.env` and paste your keys:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-socket-token
BRAVE_SEARCH_API_KEY=your-brave-key
ALFRED_WAKE_TIME=10:00
ALFRED_TIMEZONE=Asia/Kolkata
```

## Step 3: Install Dependencies (1 minute)

```bash
cd /Users/param/Downloads/fatima
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Step 4: Launch ALFRED (30 seconds)

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
Starting scheduler...
Scheduler started. Briefing at 10:00 Asia/Kolkata
Starting Slack bot (Socket Mode)...
ALFRED is ready. Listening for messages...
```

And in Slack `#alfred-logs`:
```
ALFRED is online.
Wake time: 10:00 Asia/Kolkata
Daily token budget: 500,000 tokens
Research topics: fertilizers, agriculture, agritech, tech startups, AI, science breakthroughs, India agriculture policy
Ready to serve, sir.
```

## Step 5: Test It

1. Go to `#incoming` in Slack
2. Paste a link: `https://en.wikipedia.org/wiki/Fertilizer`
3. ALFRED should reply in a thread with a summary
4. Type `@ALFRED what can you do?` — it should respond
5. Try: `@ALFRED research phosphate recycling latest developments`

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Missing required env vars" | Check your `.env` file has all 4 required keys |
| Slack bot doesn't respond | Make sure Socket Mode is enabled and ALFRED is invited to the channel |
| "Rate limited by Anthropic" | You're sending too many messages. Wait a minute |
| "Daily token budget exceeded" | Wait until midnight (auto-resets) or increase `ALFRED_DAILY_TOKEN_BUDGET` in `.env` |
| Bot crashes immediately | Check the error in terminal — usually a bad API key |

## What's Working in Phase 1

- Message listening in all channels ALFRED is invited to
- Message classification (URGENT/RESEARCH/IDEA/TASK/CHAT)
- Link fetching and summarization
- @ALFRED direct conversation
- Idea scoring
- Morning briefing at 10:00 AM (generates from whatever data is available)
- Token budget tracking and daily reset
- Memory persistence (remembers across restarts)
- Health checks every 30 minutes

## What's Coming Next

- Phase 2: Voice note transcription (Whisper), PDF parsing, enhanced link processing
- Phase 3: Richer morning briefings with interactive follow-up
- Phase 4: Deep research engine with multi-source synthesis
- Phase 5: Builder mode (Cursor/Claude Code/Bolt.new integration)
- Phase 6: Market intelligence (Alpaca)
- Phase 7: WhatsApp bridge, token optimization, fine-tuning
