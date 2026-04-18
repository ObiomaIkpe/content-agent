# Content Agent — Codebase Reference

## What This Does

Watches your developer activity (code commits, Claude Code sessions, VSCode file edits) and automatically generates social media posts for LinkedIn, Twitter, Reddit, Facebook, and Instagram. You review and approve each post via Telegram before anything gets published.

---

## High-Level Flow

```
Every 3 hours (daemon)
  └─ Collect activity snapshots
       ├─ Claude Code session logs
       ├─ GitHub commits & PRs
       ├─ ActivityWatch (VSCode files, app usage)
       └─ Git diffs (stat + full diff for small commits)
       └─ Save to snapshots/snapshot_YYYYMMDD_HHMMSS.json

On demand (/run in Telegram or python agents/crew.py)
  └─ Run 5-step pipeline
       ├─ Step 1: Aggregator   → work report
       ├─ Step 2: Strategist   → content angles
       ├─ Step 3: 5 Writers    → platform drafts
       ├─ Step 4: Reviewer     → quality check
       └─ Step 5: Merge        → send to Telegram

In Telegram
  └─ Review each draft
       ├─ ✅ Approve
       └─ ❌ Reject
```

---

## Directory Structure

```
content-agent/
├── agents/                   # CrewAI pipeline
│   ├── crew.py               # Orchestrator — runs the full 5-step pipeline
│   ├── aggregator_agent.py   # Step 1: merges snapshots into a work report
│   ├── strategist_agent.py   # Step 2: picks highlights and content angles
│   ├── reviewer.py           # Step 4: quality checks all drafts
│   └── writers/
│       ├── linkedin.py       # Step 3: LinkedIn post writer
│       ├── twitter.py        # Step 3: X/Twitter post writer
│       ├── reddit.py         # Step 3: Reddit post writer
│       ├── facebook.py       # Step 3: Facebook post writer
│       └── instagram.py      # Step 3: Instagram caption writer
├── local_agent/              # Activity collection
│   ├── aggregator.py         # Orchestrates all collectors, saves snapshot JSON
│   ├── claude_logs.py        # Reads Claude Code session logs (~/.claude/projects/)
│   ├── github_collector.py   # Fetches commits & PRs via GitHub API
│   ├── activitywatch_collector.py  # Pulls VSCode file activity from ActivityWatch API
│   ├── git_diff_collector.py # Reads local git diffs (stat + code for small commits)
│   └── scheduler.py          # APScheduler daemon — runs collection every 3 hours
├── bot/
│   └── telegram_bot.py       # Telegram bot for review, approval, and pipeline control
├── config/
│   ├── brand_voice.yaml      # Your tone, style, personality, platform limits
│   └── loader.py             # Read/write brand_voice.yaml
├── snapshots/                # Collected activity data (JSON files)
├── .env                      # API keys and config
└── CODEBASE.md               # This file
```

---

## File-by-File Breakdown

### `agents/crew.py` — Pipeline Orchestrator

The main entry point for content generation. Runs 5 sequential steps and sends the results to Telegram.

```
run_pipeline()
  ├─ load_todays_snapshots()          load all snapshot JSON files
  ├─ Crew([agg_agent])                Step 1 → work_report dict
  ├─ Crew([strat_agent])              Step 2 → strategy dict with highlights[]
  ├─ Crew([linkedin, twitter, ...])   Step 3 → drafts dict per platform
  ├─ Crew([reviewer])                 Step 4 → reviews dict per platform
  └─ merge drafts + reviews           Step 5 → final_posts dict
```

**`extract_json(text)`** — strips JSON from Claude's response text (Claude sometimes wraps JSON in prose).

**`final_posts` structure:**
```json
{
  "linkedin": {
    "draft": "...",
    "status": "approved | needs_revision",
    "feedback": "...",
    "final": "..."
  }
}
```

---

### `agents/aggregator_agent.py` — Work Report Builder

**Role:** Work Analyst  
**Input:** List of raw activity snapshots  
**Output:** Structured JSON work report

The task prompt instructs the agent to read all four data sources in each snapshot:
- `claude_sessions` — what you asked Claude to do
- `github` — commit and PR messages
- `activitywatch` — which files you edited and for how long
- `git_diffs` — actual code changes (stat always; full diff for commits ≤50 lines changed)

**Output shape:**
```json
{
  "summary": "2-4 sentence summary of the day",
  "projects": ["content-agent", "..."],
  "technologies": ["Python", "CrewAI", "..."],
  "problems_solved": ["fixed JSON parsing bug", "..."],
  "effort_level": "low | medium | high",
  "raw_highlights": ["notable thing worth posting about", "..."]
}
```

---

### `agents/strategist_agent.py` — Content Angle Generator

**Role:** Content Strategist  
**Input:** Work report + content history (to avoid repeating recent topics)  
**Output:** List of highlights with two angles each

Two angles per highlight:
- **hiring_angle** — frames the work to impress companies looking to hire
- **freelance_angle** — frames the work to attract businesses that need custom software

**Output shape:**
```json
{
  "highlights": [
    {
      "topic": "built Telegram approval flow for content pipeline",
      "hiring_angle": "...",
      "freelance_angle": "...",
      "suggested_platforms": ["linkedin", "twitter"]
    }
  ]
}
```

The pipeline uses only `highlights[0]` — the top pick — for writing.

---

### `agents/reviewer.py` — Quality Gate

**Role:** Content Quality Reviewer  
**Input:** All 5 platform drafts + brand voice config  
**Output:** Approval status, feedback, and revised post per platform

Checks each draft for:
1. Platform tone fit (LinkedIn ≠ Reddit ≠ Twitter)
2. Brand voice alignment (no banned words, correct style)
3. Sensitive company/client info that should be removed
4. Publish-readiness

**Output shape:**
```json
{
  "reviews": {
    "linkedin": {
      "status": "approved | needs_revision",
      "feedback": "...",
      "revised_post": "... or null"
    }
  }
}
```

---

### `agents/writers/` — Platform Writers

Each writer is a CrewAI `Agent` + `Task` pair. All receive the same `highlight` and `brand_voice` inputs. Each has a distinct persona and platform-specific rules.

| File | Role | Key constraints |
|------|------|-----------------|
| `linkedin.py` | LinkedIn Copywriter | 150–300 words, strong hook, 3–5 hashtags, no buzzwords |
| `twitter.py` | X (Twitter) Copywriter | ≤280 chars single tweet or 5-tweet thread, max 2 hashtags |
| `reddit.py` | Reddit Copywriter | Title + Body format, suggest subreddit, no self-promotion tone |
| `facebook.py` | Facebook Copywriter | 100–200 words, explain tech in plain language, warm tone |
| `instagram.py` | Instagram Copywriter | 80–150 words, hook before "more" cutoff, 10–15 hashtags |

---

### `local_agent/aggregator.py` — Snapshot Orchestrator

Calls all four collectors in sequence and saves the result as a timestamped JSON file.

```python
collect_snapshot(hours=3)
  ├─ collect_claude_logs(hours)
  ├─ collect_github(hours)
  ├─ collect_activitywatch(hours)
  └─ collect_git_diffs(hours, claude_sessions, activitywatch)
```

Passes `claude_sessions` and `activitywatch` results directly into `collect_git_diffs` so repo discovery is free — no extra API calls.

Saves to: `snapshots/snapshot_YYYYMMDD_HHMMSS.json`

---

### `local_agent/claude_logs.py` — Claude Session Reader

Reads `~/.claude/projects/*/` JSONL files. Each file is a Claude Code conversation session.

**What it extracts:**
- Your user messages (questions/instructions to Claude)
- Git branch name
- Working directory (`cwd`)
- Session start/end timestamps

**Filtering:**
- Skips messages under 15 chars (noise)
- Skips `<command-name>`, `<local-command-stdout>`, `source ...` lines
- Caps at 10 messages per session

**Anonymization:** If a project name matches `ANONYMIZED_PROJECTS` in `.env`, the project name, branch, and cwd are redacted before saving to the snapshot.

---

### `local_agent/github_collector.py` — GitHub Activity

Uses the GitHub API to fetch recent activity.

- **Commits:** Scans all your repos for commits authored by you in the last N hours
- **PRs:** Uses GitHub search API for PRs you authored updated in the last N hours

Only captures metadata (message, repo, timestamp, URL) — not code content.

Requires: `GITHUB_TOKEN`, `GITHUB_USERNAME` in `.env`

---

### `local_agent/activitywatch_collector.py` — VSCode & App Activity

Polls the local ActivityWatch API (`http://localhost:5600/api/0`) for events from the last N hours.

**Requires ActivityWatch to be running locally with the VSCode extension installed.**

Collects from four bucket types:
| Bucket type | What's captured |
|-------------|----------------|
| `window` | App name + time spent (e.g. VSCode: 3600s) |
| `vscode` | File name + language + time spent per file |
| `afk` | Total active (non-AFK) seconds |
| `web` | Browser tab URLs and titles |

Returns file names and durations — no file contents.

---

### `local_agent/git_diff_collector.py` — Code Change Reader

Auto-discovers git repos from activity data already collected (no manual config needed).

**Repo discovery:**
1. Takes `cwd` from each Claude Code session
2. Takes file paths from ActivityWatch VSCode events (strips the ` (language)` suffix)
3. Walks up each path to find the `.git` root

**Per repo, per commit:**
- Always includes: commit hash, message, author, timestamp, stat summary (files changed + line counts)
- Includes full diff only when total changed lines ≤ 50 (focused, meaningful commits)
- Caps at 10 most recent commits per repo

**Why the threshold matters:** Small commits (bug fixes, specific features) are the most content-worthy and their code is readable. Large commits (refactors, initial commit) would flood the context with noise.

---

### `local_agent/scheduler.py` — Collection Daemon

Runs `collect_snapshot()` every 3 hours using APScheduler. Timezone: `Africa/Lagos`.

```bash
python local_agent/scheduler.py
# Runs forever until Ctrl+C
```

---

### `bot/telegram_bot.py` — Review Interface

A Telegram bot (polling mode) that serves as the human-in-the-loop gate.

**Commands:**
| Command | What it does |
|---------|-------------|
| `/start` | Shows available commands |
| `/status` | Shows how many snapshots have been collected today |
| `/run` | Triggers the full pipeline (takes a few minutes) |
| `/setvoice` | View or update brand voice config (tone, style, personality) |

**Draft review flow:**
1. Pipeline calls `send_all_drafts()` which sends one message per platform
2. Each message has ✅ Approve / ❌ Reject inline buttons
3. Approvals/rejections are stored in `pending_posts` dict (in-memory)
4. When all 5 platforms are reviewed, bot sends a summary

**Note:** Approved posts are flagged but not auto-published yet — publishing is a stub.

---

### `config/brand_voice.yaml` — Voice Configuration

Controls how all writers and the reviewer behave. Editable via `/setvoice` in Telegram or directly in the file.

```yaml
tone: "casual but technical"
style: "storytelling"
personality_notes: "Nigerian developer, keeps it real, no corporate fluff..."
words_to_avoid: [synergy, guru, excited to share, ...]
words_to_use: [built, shipped, solved, figured out, ...]
audiences:
  hiring:   { emphasis: "technical depth", tone_adjustment: "slightly more professional" }
  freelance: { emphasis: "results, speed", tone_adjustment: "warmer, conversational" }
platforms:
  linkedin: { max_words: 300, hashtags: 5 }
  twitter:  { max_chars: 280, hashtags: 2 }
  reddit:   { max_words: 400, hashtags: 0 }
  facebook: { max_words: 200, hashtags: 3 }
  instagram: { max_words: 150, hashtags: 15 }
```

---

### `config/loader.py` — Config I/O

Two functions:
- `load_brand_voice()` → returns the YAML as a dict
- `update_brand_voice(updates)` → merges updates and writes back to the file

---

## Environment Variables (`.env`)

| Variable | Used by | Purpose |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | `crew.py` | Claude API (all agents) |
| `GITHUB_TOKEN` | `github_collector.py` | GitHub API auth |
| `GITHUB_USERNAME` | `github_collector.py` | Whose commits to fetch |
| `TELEGRAM_BOT_TOKEN` | `telegram_bot.py` | Bot identity |
| `TELEGRAM_CHAT_ID` | `telegram_bot.py` | Your chat ID (where drafts are sent) |
| `CLAUDE_LOGS_DIR` | `claude_logs.py` | Path to `~/.claude/projects` |
| `ANONYMIZED_PROJECTS` | `claude_logs.py`, `git_diff_collector.py` | Comma-separated project names to redact |

---

## How to Run

**1. Start the collection daemon** (runs every 3 hours, keep it alive in a terminal or systemd):
```bash
python local_agent/scheduler.py
```

**2. Start the Telegram bot** (separate terminal):
```bash
python bot/telegram_bot.py
```

**3. Trigger content generation** — either:
- Send `/run` in Telegram
- Or run directly: `python agents/crew.py`

**4. Test individual collectors:**
```bash
python local_agent/aggregator.py          # collect + save one snapshot now
python local_agent/github_collector.py    # GitHub only
python local_agent/claude_logs.py         # Claude logs only
python local_agent/git_diff_collector.py  # Git diffs only (uses cwd as test repo)
```

---

## Known Gaps

| Gap | Location | Notes |
|-----|----------|-------|
| Publishing not implemented | `telegram_bot.py:168` | Posts are approved but not sent to platforms |
| Bitbucket collector is empty | `local_agent/bitbucket_collector.py` | Stub file, not wired in |
| `pending_posts` is in-memory | `telegram_bot.py:22` | Restaring the bot clears pending reviews |
| Content history not persisted | `crew.py:46` | Always passes `[]`, so strategist can't avoid repeating topics yet |
| No publishing integrations | — | Twitter/LinkedIn/Reddit APIs not connected |
