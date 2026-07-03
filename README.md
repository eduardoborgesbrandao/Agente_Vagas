 Job Hunter Agent
An automated AI-powered job monitoring agent that scrapes job listings daily, scores them against your profile using Google Gemini, and delivers only the best matches directly to your Telegram — so you never miss a relevant opportunity.
 - The Problem
Searching for internships and junior positions manually is time-consuming and inconsistent. Job boards surface hundreds of irrelevant listings, and good opportunities disappear within hours. Most candidates either check too infrequently and miss openings, or waste time reviewing jobs that don't fit their profile.
 - The Solution
A fully automated agent that runs every night, filters every new job against your profile using AI, and sends you a curated shortlist with fit scores and reasoning — before you even wake up.
 - How It Works
Gupy API (job board)
        ↓
   Filter: posted in last 30h
        ↓
   Deduplicate (SQLite)
        ↓
   Gemini AI scores each job (0–100)
   against your profile + preferences
        ↓
   Jobs above threshold → queue
        ↓
   Telegram notification with:
   • Job title & company
   • Match score
   • Tech core flag (is it a tech company?)
   • AI reasoning for the score
   • Direct application link

 - Key Features
AI-Powered Scoring — Google Gemini 2.5 Flash evaluates each job against your skills, location preferences, and career goals. Returns a structured JSON score with explanation.
Intelligent Deduplication — SQLite database tracks every job ever seen. No duplicate alerts across multiple runs.
Priority Queue — Jobs are ranked by tech-core companies first, then by match score. You see the best opportunities first.
Daily Rate Limiting — Configurable cap on daily notifications (default: 7) to prevent alert fatigue.
Fully Automated CI/CD — GitHub Actions runs the agent every night at 01:00 UTC with zero manual intervention. Also supports manual trigger via workflow_dispatch.
Graceful Error Handling — Retry logic on Gemini API calls, fallback modes for missing credentials, structured execution summary logs.

 - Tech Stack
Python 3.11AI / Google Gemini 2.5 Flash (via google-genai)/Gupy Public API/ SQLite/ Telegram Bot API/ GitHub Actions/ .env + GitHub Secrets/ HTTP requests


- Project Structure
job-hunter-agent/
├── .github/
│   └── workflows/
│       └── run_agente.yml      # GitHub Actions workflow
├── config/
│   └── configuracoes.py        # Environment config & constants
├── src/
│   ├── scraper.py              # Gupy API integration & date filtering
│   ├── analise.py              # Gemini AI scoring engine
│   ├── database.py             # SQLite persistence layer
│   └── notificador.py          # Telegram notification sender
├── data/
│   └── jobs.db                 # SQLite database (auto-created)
├── perfil.txt                  # Candidate profile (skills, goals, preferences)
├── main.py                     # Orchestration & execution summary
└── requirements.txt


AI Scoring Logic
The Gemini model acts as a senior technical recruiter. For each job, it receives:
Job title and full description
Candidate profile (education, stack, career goals, location preferences)
It returns a structured JSON with three fields:

json{
  "match_score": 82,
  "tech_core": true,
  "motivo": "Strong alignment with Flutter and Python stack."
}

Hard elimination rules are encoded in the system prompt — administrative roles, wrong field requirements, or location mismatches automatically score below 50 regardless of other factors.
