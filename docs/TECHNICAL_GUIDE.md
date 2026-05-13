# LeadFlow AI - Technical Guide

## Architecture Overview

```
Mac Mini (Always-On Local Server)
├── Ollama (local LLM inference - FREE)
│   └── llama3.1:8b  <- lead classification
├── FastAPI (web server on port 8000)
│   ├── /          <- agent dashboard
│   ├── /api/leads <- CRUD
│   ├── /api/scan  <- triggers scrape+classify pipeline
│   └── /api/stats <- summary counts
├── SQLite (leads.db - local, private)
├── APScheduler (optional cron jobs)
└── Claude API (outreach generation, hot leads only)
```

## Two-Tier LLM Strategy
- Tier 1 (Bulk): Ollama llama3.1:8b runs locally, zero cost, handles all classification
- Tier 2 (Quality): Claude API called only for leads scoring >= 7, keeps costs at $5-15/mo

## Geo Corridor Filter
Uses geopy geodesic distance. A lead is "in corridor" if:
  dist(lead, cityX) + dist(lead, cityY) <= corridor_length + buffer_miles

## Adding New Scrapers
Create a file in scrapers/ that returns a list of dicts with these keys:
  name, address, city, lat, lng, equity, years_owned, source, created_at

Then import and call it in app.py do_scan().

## Data Sources to Add
- County assessor APIs (free public data)
- PropStream API (paid, best data quality)
- ATTOM Data API (paid)
- Zillow FSBO search
- Facebook Marketplace (requires selenium)
- Expired MLS (via MLS API or PropStream)

## Scaling Up
- Replace SQLite with PostgreSQL for >10k leads
- Add Redis queue for background jobs (celery + redis)
- Add email delivery via SendGrid API
- Add Twilio for SMS delivery
- Add Follow Up Boss API for CRM sync

## Config (config.yaml)
```yaml
agent_name: Jane Smith
city_x: San Jose, CA
city_y: San Francisco, CA
radius_miles: 15
claude_api_key: sk-ant-...
scan_interval_hours: 6
min_score_for_outreach: 7
```

## Running in Production on Mac Mini
```bash
# Keep alive on boot via launchd
cp com.leadflow.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.leadflow.plist

# Or simple caffeinate approach
caffeinate -i python3 app.py &

# Access from any device on same network
http://<mac-mini-local-ip>:8000
```

## Cost Model
| Component        | Cost/month |
|-----------------|------------|
| Mac Mini        | $0 (owned) |
| Ollama models   | $0         |
| Claude API      | $5-15      |
| Data sources    | $0-99      |
| Total           | $5-114     |

vs cloud equivalent: $200-500/month

## Environment Variables
Set in shell profile or .env file:
  ANTHROPIC_API_KEY=sk-ant-...
  DB_PATH=database/leads.db

## Testing
```bash
# Test classifier only
python3 -c "from ai.classifier import classify_lead; print(classify_lead({'name':'Test','years_owned':10,'equity':200000}))"

# Test geo filter
python3 -c "from geo.filter import in_corridor; print(in_corridor(37.4,'San Jose, CA','San Francisco, CA'))"

# Run dev server
uvicorn app:app --reload --port 8000
```
