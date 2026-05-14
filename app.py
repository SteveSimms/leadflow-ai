"""
Real Estate Lead Engine - FastAPI Backend
Serves the dashboard and handles all lead processing
"""
# Load .env first so all env vars are available to every module
from dotenv import load_dotenv
load_dotenv()

import sqlite3, json, os, yaml
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import anthropic
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests
from bs4 import BeautifulSoup
from scrapers.craigslist import scrape_craigslist_fsbo
from scrapers.market_data import get_corridor_market_data

app = FastAPI(title="RE Lead Engine")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

DB_PATH = "database/leads.db"
CONFIG_PATH = "config.yaml"

# ── Database ──────────────────────────────────────────────────────────────────
def get_db():
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, address TEXT, city TEXT,
            lat REAL, lng REAL, phone TEXT, email TEXT,
            years_owned INTEGER, equity INTEGER,
            score INTEGER DEFAULT 0,
            motivation TEXT, timeline TEXT,
            approach TEXT, talking_points TEXT,
            email_outreach TEXT, sms_outreach TEXT, voicemail_outreach TEXT,
            status TEXT DEFAULT 'new',
            source TEXT, created_at TEXT, contacted_at TEXT
        )
    """)
    conn.commit()
    return conn

# ── Config ────────────────────────────────────────────────────────────────────
def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f) or {}

def save_config(data: dict):
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(data, f)

# ── Geo Filter ────────────────────────────────────────────────────────────────
geo = Nominatim(user_agent="re_lead_engine")

def in_corridor(lat, lng, city_x, city_y, buffer_miles=15):
    try:
        cx = geo.geocode(city_x)
        cy = geo.geocode(city_y)
        if not cx or not cy:
            return True
        px = (cx.latitude, cx.longitude)
        py = (cy.latitude, cy.longitude)
        pl = (lat, lng)
        corridor = geodesic(px, py).miles
        return (geodesic(px, pl).miles + geodesic(py, pl).miles) <= corridor + buffer_miles
    except:
        return True

# ── AI: Local Classifier (Ollama or Mock fallback) ────────────────────────────
def classify_lead(lead: dict) -> dict:
    """Uses Ollama locally. Falls back to heuristic scoring if Ollama not running."""
    try:
        import ollama as _ollama
        prompt = f"""Classify this real estate lead. Return JSON only.
Lead: {json.dumps(lead)}
Return: {{"score":1-10,"motivation":"hot|warm|cold","timeline":"0-3mo|3-6mo|6-12mo","approach":"email|phone|direct_mail","talking_points":["p1","p2"]}}"""
        r = _ollama.chat(model="llama3.1:8b", messages=[{"role":"user","content":prompt}], format="json")
        return json.loads(r["message"]["content"])
    except Exception:
        # Heuristic fallback for sandbox/demo mode
        equity = lead.get("equity", 0)
        years = lead.get("years_owned", 0)
        score = min(10, max(1, int((equity / 100000) + (years / 3))))
        motivation = "hot" if score >= 7 else ("warm" if score >= 4 else "cold")
        points = []
        if years >= 10: points.append(f"{years} years owned — long tenure")
        if equity >= 300000: points.append(f"High equity (${equity:,})")
        return {"score": score, "motivation": motivation, "timeline": "3-6mo",
                "approach": "email", "talking_points": points}

# ── AI: Outreach Writer (Gemini → Claude → Template fallback) ────────────────
def _outreach_prompt(lead: dict, cls: dict) -> str:
    return f"""You are a real estate agent writing outreach for a motivated seller lead.
Write short, conversational, personalized outreach. Be warm and human — not salesy.

Lead details:
- Name: {lead.get('name')}
- Address: {lead.get('address')}, {lead.get('city')}
- Years owned: {lead.get('years_owned')} years
- Estimated equity: ${lead.get('equity', 0):,}
- Source: {lead.get('source')}
- Key signals: {', '.join(cls.get('talking_points', []))}
- Agent name: Ellen Beltran

Return ONLY valid JSON (no markdown, no preamble):
{{"email_subject":"...","email_body":"...(under 120 words)","sms":"...(under 160 chars)","voicemail":"...(under 30 seconds, natural speech)"}}"""

def _write_with_gemini(lead: dict, cls: dict) -> dict:
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key:
        return {}
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        r = model.generate_content(_outreach_prompt(lead, cls))
        text = r.text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception as e:
        print(f"[gemini] Outreach error: {e}")
        return {}

def _write_with_claude(lead: dict, cls: dict) -> dict:
    claude_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not claude_key:
        return {}
    try:
        client = anthropic.Anthropic(api_key=claude_key)
        r = client.messages.create(
            model="claude-3-5-haiku-20241022", max_tokens=600,
            messages=[{"role": "user", "content": _outreach_prompt(lead, cls)}]
        )
        return json.loads(r.content[0].text)
    except Exception as e:
        print(f"[claude] Outreach error: {e}")
        return {}

def _write_template(lead: dict, cls: dict) -> dict:
    """Solid template outreach — no API key needed."""
    name     = lead.get("name", "there").split("&")[0].strip().split()[0]
    city     = lead.get("city", "your area").split(",")[0]
    equity   = lead.get("equity", 0)
    years    = lead.get("years_owned", 0)
    signals  = cls.get("talking_points", [])
    key_signal = signals[0] if signals else f"{years} years owned"
    return {
        "email_subject": f"Your {city} home — what it's worth today",
        "email_body": (
            f"Hi {name},\n\n"
            f"I came across your property and wanted to reach out. "
            f"With {years} years in your home, you've built real equity"
            + (f" — around ${equity:,}" if equity else "") + f" — and the {city} market is moving.\n\n"
            f"{key_signal}. That's worth a conversation.\n\n"
            f"I'd love to share a no-obligation market snapshot whenever works for you.\n\n"
            f"Warm regards,\nEllen Beltran"
        ),
        "sms": (
            f"Hi {name}, I work with homeowners in {city} and your property caught my attention. "
            f"Happy to share a quick market update — no commitment needed! — Ellen Beltran"
        )[:160],
        "voicemail": (
            f"Hi {name}, this is Ellen Beltran. I specialize in the Menifee to San Diego corridor "
            f"and your home in {city} caught my attention. I'd love to share what comparable homes "
            f"are selling for right now — no pressure at all. Please call me back whenever works!"
        ),
    }

def write_outreach(lead: dict, cls: dict, api_key: str = "") -> dict:
    """Try Gemini → Claude → template. Always returns something."""
    if cls.get("score", 0) < 4:
        return _write_template(lead, cls)
    result = _write_with_gemini(lead, cls)
    if result:
        print(f"[ai] Outreach written by Gemini for {lead.get('name')}")
        return result
    result = _write_with_claude(lead, cls)
    if result:
        print(f"[ai] Outreach written by Claude for {lead.get('name')}")
        return result
    print(f"[ai] Using template outreach for {lead.get('name')}")
    return _write_template(lead, cls)


# ── Market data cache (avoid hammering Census API) ───────────────────────────
_market_cache: dict = {}
_market_cache_ts: str = ""

# ── API Routes ────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    with open("static/index.html") as f:
        return HTMLResponse(f.read())

@app.get("/api/config")
def get_config():
    return load_config()

@app.post("/api/config")
async def update_config(request: Request):
    data = await request.json()
    save_config(data)
    return {"status": "saved"}

@app.get("/api/leads")
def get_leads(status: str = None):
    db = get_db()
    q = "SELECT * FROM leads ORDER BY score DESC, created_at DESC"
    rows = db.execute(q).fetchall()
    leads = [dict(r) for r in rows]
    if status:
        leads = [l for l in leads if l["status"] == status]
    db.close()
    return leads

@app.get("/api/stats")
def get_stats():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    hot   = db.execute("SELECT COUNT(*) FROM leads WHERE score >= 7").fetchone()[0]
    warm  = db.execute("SELECT COUNT(*) FROM leads WHERE score >= 4 AND score < 7").fetchone()[0]
    contacted = db.execute("SELECT COUNT(*) FROM leads WHERE status='contacted'").fetchone()[0]
    db.close()
    return {"total": total, "hot": hot, "warm": warm, "contacted": contacted}

@app.post("/api/scan")
async def run_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(do_scan)
    return {"status": "scanning", "message": "Lead scan started — scraping Craigslist FSBO + county records"}

def do_scan():
    global _market_cache, _market_cache_ts
    cfg = load_config()
    city_x = cfg.get("city_x", "San Jose, CA")
    city_y = cfg.get("city_y", "San Francisco, CA")
    api_key = cfg.get("claude_api_key", "")
    radius  = cfg.get("radius_miles", 15)

    print(f"[scan] Starting — corridor: {city_x} → {city_y}")

    # ── 1. Scrape Craigslist FSBO for both cities ────────────────────────────
    raw: list[dict] = []
    raw += scrape_craigslist_fsbo(city_x, max_results=25)
    raw += scrape_craigslist_fsbo(city_y, max_results=25)
    print(f"[scan] Raw leads from Craigslist: {len(raw)}")

    # ── 2. Filter to corridor ────────────────────────────────────────────────
    corridor_leads = [
        l for l in raw
        if in_corridor(l["lat"], l["lng"], city_x, city_y, buffer_miles=radius)
    ]
    print(f"[scan] After geo filter: {len(corridor_leads)} in corridor")

    # ── 3. Classify + generate outreach ─────────────────────────────────────
    db = get_db()
    added = 0
    for lead in corridor_leads:
        # Skip duplicates (same address already in DB)
        exists = db.execute(
            "SELECT id FROM leads WHERE address=?", (lead["address"],)
        ).fetchone()
        if exists:
            continue

        cls      = classify_lead(lead)
        outreach = write_outreach(lead, cls, api_key)

        db.execute("""
            INSERT INTO leads (name,address,city,lat,lng,phone,email,
            equity,years_owned,score,motivation,timeline,approach,
            talking_points,email_outreach,sms_outreach,voicemail_outreach,
            source,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            lead["name"], lead["address"], lead["city"],
            lead["lat"],  lead["lng"],
            lead.get("phone",""), lead.get("email",""),
            lead["equity"], lead["years_owned"],
            cls["score"], cls["motivation"], cls["timeline"], cls["approach"],
            json.dumps(cls.get("talking_points",[])),
            outreach.get("email_body",""), outreach.get("sms",""),
            outreach.get("voicemail",""),
            lead["source"], lead["created_at"]
        ))
        added += 1

    db.commit()
    db.close()

    # ── 4. Refresh market data cache ─────────────────────────────────────────
    try:
        _market_cache    = get_corridor_market_data(city_x, city_y)
        _market_cache_ts = datetime.now().isoformat()
        print("[scan] Market data refreshed")
    except Exception as e:
        print(f"[scan] Market data error: {e}")

    print(f"[scan] ✅ Complete — {added} new leads added")

@app.get("/api/market")
def get_market():
    """Return cached corridor market data (or fetch fresh if cache is empty)."""
    global _market_cache, _market_cache_ts
    if _market_cache:
        return {**_market_cache, "cached_at": _market_cache_ts}
    cfg    = load_config()
    city_x = cfg.get("city_x", "San Jose, CA")
    city_y = cfg.get("city_y", "San Francisco, CA")
    if not city_x or not city_y:
        return {"error": "Configure your corridor cities first"}
    try:
        _market_cache    = get_corridor_market_data(city_x, city_y)
        _market_cache_ts = datetime.now().isoformat()
        return {**_market_cache, "cached_at": _market_cache_ts}
    except Exception as e:
        return {"error": str(e)}

@app.patch("/api/leads/{lead_id}")
async def update_lead(lead_id: int, request: Request):
    data = await request.json()
    db = get_db()
    if "status" in data:
        db.execute("UPDATE leads SET status=? WHERE id=?", (data["status"], lead_id))
        if data["status"] == "contacted":
            db.execute("UPDATE leads SET contacted_at=? WHERE id=?",
                       (datetime.now().isoformat(), lead_id))
    db.commit()
    db.close()
    return {"status": "updated"}

if __name__ == "__main__":
    import uvicorn
    get_db()
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=False)
