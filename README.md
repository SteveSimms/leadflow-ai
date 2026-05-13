# 🏠 LeadFlow AI

> **AI-powered real estate lead generation that runs 24/7 on your Mac Mini.**
> Find motivated sellers between any two cities, scored and outreach-ready — all for under $15/month.

![Dashboard](docs/assets/dashboard-preview.png)

---

## ✨ Features

- 🔍 **Auto-scrapes** FSBO listings, expired MLS, and public records
- 🧠 **AI Lead Scoring** — local Ollama LLM scores every lead 1–10 (free)
- ✉️ **Personalized Outreach** — Claude generates email, SMS & voicemail scripts for hot leads
- 📍 **Geo Corridor Filter** — targets only leads between City X → City Y
- 🖥️ **Beautiful Dashboard** — dark-mode web UI, no installs for the agent
- 💾 **100% Local** — all data stays on your Mac Mini, private and secure
- ⚡ **One-click copy** — copy AI-written outreach directly to clipboard

---

## 💰 Cost Comparison

| | Traditional Tools | LeadFlow AI |
|--|--|--|
| Lead generation software | $100–300/mo | **$0** |
| AI writing tools | $50–100/mo | **$0–15/mo** |
| Cloud server | $20–50/mo | **$0** (Mac Mini) |
| **Total** | **$170–450/mo** | **$5–15/mo** |

---

## 🖥️ Requirements

| Requirement | Notes |
|---|---|
| Mac Mini M1 or newer | Any modern Mac works too |
| macOS 13+ | Ventura or later |
| Python 3.11+ | Installed via Homebrew |
| [uv](https://docs.astral.sh/uv/) | Fast Python package manager |
| Claude API Key | From [console.anthropic.com](https://console.anthropic.com) |
| [Ollama](https://ollama.com) (optional) | For free local AI scoring |

---

## 🚀 Quick Start (First Time Setup)

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/leadflow-ai.git
cd leadflow-ai
```

### 2. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Create virtual environment & install dependencies

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

### 4. (Optional but recommended) Install Ollama for free local AI

```bash
brew install ollama
ollama pull llama3.1:8b   # ~4.7GB download, one-time
```

### 5. Seed demo data (to see the dashboard right away)

```bash
.venv/bin/python seed_demo.py
```

### 6. Start the app

```bash
.venv/bin/python app.py
```

### 7. Open your browser

```
http://localhost:8080
```

Fill in the setup screen with your two target cities and your Claude API key. That's it!

---

## 🔄 Running Every Day

### Option A — Manual (simplest)
Double-click your terminal, run:
```bash
cd leadflow-ai && .venv/bin/python app.py
```
Then visit `http://localhost:8080` and click **Scan for Leads**.

### Option B — Auto-start on Mac boot (recommended)

Create a launch agent so LeadFlow starts automatically when your Mac Mini boots:

```bash
bash scripts/install_launch_agent.sh
```

Once installed, LeadFlow will:
- Start automatically on login
- Be accessible at `http://localhost:8080` at all times
- Run lead scans every 6 hours in the background

### Option C — Access from any device on your network

Find your Mac Mini's local IP:
```bash
ipconfig getifaddr en0
```

Then on any phone/tablet/laptop on the same WiFi:
```
http://192.168.X.X:8080
```

---

## ⚙️ Configuration

Edit `config.yaml` (created on first run) or use the ⚙️ Settings button in the dashboard:

```yaml
agent_name: Jane Smith
city_x: San Jose, CA          # Start of your corridor
city_y: San Francisco, CA     # End of your corridor
radius_miles: 15              # How wide the search net is
claude_api_key: sk-ant-...    # From console.anthropic.com
scan_interval_hours: 6        # How often to auto-scan
min_score_for_outreach: 7     # Only generate outreach for leads above this score
```

---

## 📊 Understanding Lead Scores

| Score | Color | Label | Recommended Action |
|---|---|---|---|
| 7–10 | 🔴 Red | 🔥 Hot | Contact same day — AI outreach ready |
| 4–6 | 🟠 Orange | 🌤 Warm | Follow up within the week |
| 1–3 | 🔵 Blue | ❄️ Cold | Add to nurture drip |

**Signals the AI looks for:**
- Long tenure (10+ years at same address = high equity likely)
- Recent life events (divorce filings, job changes, empty nester signals)
- Expired MLS listings (frustrated sellers)
- FSBO attempts (motivated but un-represented)
- High equity estimate relative to purchase price

---

## 🗂️ Project Structure

```
leadflow-ai/
├── app.py                  # FastAPI server — all routes and business logic
├── seed_demo.py            # Populate DB with demo leads for testing
├── requirements.txt        # Python dependencies
├── config.yaml             # Your settings (auto-created, git-ignored)
├── static/
│   ├── index.html          # Dashboard UI
│   ├── style.css           # Dark-mode design system
│   └── app.js              # Frontend logic
├── database/
│   └── leads.db            # SQLite database (auto-created, git-ignored)
├── scripts/
│   └── install_launch_agent.sh   # Mac auto-start installer
└── docs/
    ├── AGENT_GUIDE.md      # Plain-English guide for non-technical agents
    └── TECHNICAL_GUIDE.md  # Developer reference
```

---

## 🔌 Adding More Data Sources

The scraper pipeline is modular. Each scraper returns a list of lead dicts:

```python
# Example scraper shape
{
    "name": "John Smith",
    "address": "123 Oak St",
    "city": "San Mateo, CA",
    "lat": 37.563,
    "lng": -122.322,
    "equity": 450000,
    "years_owned": 12,
    "source": "county_records",
    "created_at": "2024-01-15T08:00:00"
}
```

**Data sources to add next:**
- County assessor public APIs (free)
- PropStream API (best quality, ~$99/mo)
- Facebook Marketplace FSBO (requires Playwright)
- Expired MLS via MLS API

---

## 🚢 Roadmap

- [ ] Email delivery via SendGrid (auto-send outreach)
- [ ] SMS delivery via Twilio
- [ ] CRM sync — Follow Up Boss, KVCore
- [ ] CSV export
- [ ] Weekly lead report email to agent
- [ ] Mobile-friendly PWA view
- [ ] Multiple corridor support
- [ ] PropStream API integration

---

## 🔐 Privacy & Security

- All lead data is stored locally in `database/leads.db` on your Mac Mini
- Your Claude API key is stored in `config.yaml` (never committed to git)
- Only outreach generation text is sent to Anthropic's servers
- No data is sent to any third-party analytics or tracking services

---

## 📄 License

MIT — free to use, modify, and distribute.

---

## 🙋 Support

- Check `docs/AGENT_GUIDE.md` for non-technical help
- Check `docs/TECHNICAL_GUIDE.md` for developer reference
- Open an issue on GitHub for bugs or feature requests
