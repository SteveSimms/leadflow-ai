"""Seed demo leads so the dashboard is populated on first launch."""
import sqlite3, json, os
from datetime import datetime, timedelta
import random

os.makedirs("database", exist_ok=True)
conn = sqlite3.connect("database/leads.db")
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

DEMO_LEADS = [
    {
        "name": "Marcus & Linda Chen",
        "address": "4821 Willow Creek Rd",
        "city": "San Mateo, CA",
        "lat": 37.563, "lng": -122.322,
        "phone": "650-555-0142", "email": "",
        "years_owned": 14, "equity": 680000,
        "score": 9, "motivation": "hot",
        "timeline": "0-3mo", "approach": "phone",
        "talking_points": json.dumps(["High equity ($680k)", "14 years owned", "Kids left for college", "Recently listed then pulled"]),
        "email_outreach": "Hi Marcus & Linda,\n\nI noticed your home on Willow Creek Road was briefly listed last month — totally understand if the timing wasn't right. The market between San Jose and San Francisco is moving fast right now, and homes with your level of equity are in serious demand.\n\nI'd love to have a no-pressure conversation about what your options look like. Would a quick 15-minute call work this week?\n\nWarm regards,\n[Agent Name]",
        "sms_outreach": "Hi Marcus, saw your Willow Creek home was briefly listed. Market is hot right now — happy to chat options whenever works for you. [Agent Name]",
        "voicemail_outreach": "Hi Marcus, this is [Agent Name] calling. I specialize in the San Jose to San Francisco corridor and noticed your home on Willow Creek was listed recently. I'd love to connect — no pressure at all. Please call me back at your convenience. Have a great day!",
        "source": "expired_listing",
        "status": "new",
    },
    {
        "name": "Patricia Osei",
        "address": "102 Bayside Ave",
        "city": "Burlingame, CA",
        "lat": 37.584, "lng": -122.366,
        "phone": "415-555-0289", "email": "",
        "years_owned": 22, "equity": 1100000,
        "score": 8, "motivation": "hot",
        "timeline": "0-3mo", "approach": "email",
        "talking_points": json.dumps(["22 years — long tenure", "Equity over $1M", "Recent job change (LinkedIn)", "Empty nester signal"]),
        "email_outreach": "Hi Patricia,\n\nWith 22 years in your Burlingame home, you've built incredible equity — over a million dollars. That kind of position gives you real options, whether that's downsizing, relocating, or investing in something new.\n\nI work with homeowners all along the Peninsula and would love to share what comparable homes are fetching right now. A quick market update, zero obligation.\n\nBest,\n[Agent Name]",
        "sms_outreach": "Hi Patricia, I work with long-term Burlingame homeowners exploring their options. With equity like yours, timing matters. Happy to share a quick market update — no commitment needed!",
        "voicemail_outreach": "Hi Patricia, this is [Agent Name]. I specialize in helping long-term homeowners on the Peninsula understand what their equity can do for them. I'd love to share a quick market update for Burlingame — no pressure at all. Give me a call when you get a chance!",
        "source": "county_records",
        "status": "new",
    },
    {
        "name": "Javier Morales",
        "address": "778 Summit Glen Dr",
        "city": "Millbrae, CA",
        "lat": 37.599, "lng": -122.387,
        "phone": "650-555-0371", "email": "",
        "years_owned": 9, "equity": 420000,
        "score": 7, "motivation": "hot",
        "timeline": "3-6mo", "approach": "email",
        "talking_points": json.dumps(["Divorce filing detected", "9 years equity built up", "Need to split asset"]),
        "email_outreach": "Hi Javier,\n\nI understand this may be a transitional time, and I want to make this as smooth as possible for you. Homes in Millbrae are moving quickly, and yours has strong equity to work with.\n\nI'm happy to provide a confidential, no-obligation valuation whenever you're ready — on your timeline entirely.\n\n[Agent Name]",
        "sms_outreach": "Hi Javier, I work with homeowners in Millbrae navigating transitions. Happy to provide a confidential valuation whenever you're ready. No rush at all. [Agent Name]",
        "voicemail_outreach": "Hi Javier, this is [Agent Name]. I work with homeowners in Millbrae and wanted to offer a confidential, no-obligation market valuation. Please call me back whenever the time is right.",
        "source": "public_records",
        "status": "new",
    },
    {
        "name": "Susan & Tom Whitfield",
        "address": "3390 Oak Hollow Lane",
        "city": "San Carlos, CA",
        "lat": 37.507, "lng": -122.261,
        "phone": "650-555-0498", "email": "",
        "years_owned": 7, "equity": 310000,
        "score": 6, "motivation": "warm",
        "timeline": "3-6mo", "approach": "direct_mail",
        "talking_points": json.dumps(["Growing family, likely upsizing", "7 years equity", "School district change signal"]),
        "email_outreach": "",
        "sms_outreach": "Hi Susan, homes in San Carlos near the new school district boundary are selling fast! If you've been thinking about upsizing, now's a great time to explore. Happy to chat. [Agent Name]",
        "voicemail_outreach": "",
        "source": "craigslist",
        "status": "new",
    },
    {
        "name": "Derek Huang",
        "address": "211 Portola Ave",
        "city": "Daly City, CA",
        "lat": 37.706, "lng": -122.461,
        "phone": "415-555-0612", "email": "",
        "years_owned": 5, "equity": 180000,
        "score": 5, "motivation": "warm",
        "timeline": "6-12mo", "approach": "email",
        "talking_points": json.dumps(["Relocation signal (new job SF)", "5 years owned", "Starter home likely outgrown"]),
        "email_outreach": "",
        "sms_outreach": "Hi Derek, congrats on the new role! If a move is on your radar, Daly City homes are in high demand. Happy to provide a free valuation. [Agent Name]",
        "voicemail_outreach": "",
        "source": "craigslist",
        "status": "contacted",
    },
    {
        "name": "Amara Diallo",
        "address": "55 Cypress Point Ct",
        "city": "South San Francisco, CA",
        "lat": 37.654, "lng": -122.408,
        "phone": "", "email": "",
        "years_owned": 3, "equity": 95000,
        "score": 3, "motivation": "cold",
        "timeline": "12mo+", "approach": "direct_mail",
        "talking_points": json.dumps(["Early-stage equity", "3 years owned"]),
        "email_outreach": "", "sms_outreach": "", "voicemail_outreach": "",
        "source": "craigslist",
        "status": "new",
    },
    {
        "name": "Robert & Claire Nakamura",
        "address": "890 El Camino Real",
        "city": "San Bruno, CA",
        "lat": 37.627, "lng": -122.431,
        "phone": "650-555-0733", "email": "",
        "years_owned": 18, "equity": 820000,
        "score": 8, "motivation": "hot",
        "timeline": "0-3mo", "approach": "phone",
        "talking_points": json.dumps(["18 years owned", "$820k equity", "Retirement age signal", "Downsizing candidate"]),
        "email_outreach": "Hi Robert & Claire,\n\nAfter 18 years in San Bruno, you've built extraordinary equity — over $820,000. Many homeowners in your position are finding that now is the ideal time to convert that equity into a retirement upgrade or a smaller, lower-maintenance home.\n\nI'd love to show you what the market looks like and what a sale could mean for your next chapter.\n\n[Agent Name]",
        "sms_outreach": "Hi Robert, 18 years in San Bruno has built amazing equity! If retirement or downsizing is on your mind, I'd love to share what your home could fetch today. [Agent Name]",
        "voicemail_outreach": "Hi Robert, this is [Agent Name]. After 18 years in San Bruno you've built incredible equity and I think you'd be surprised what your home could sell for right now. I'd love to chat about your options — please give me a call!",
        "source": "county_records",
        "status": "new",
    },
]

ts_base = datetime.now()
for i, lead in enumerate(DEMO_LEADS):
    created = (ts_base - timedelta(hours=i*3)).isoformat()
    conn.execute("""
        INSERT INTO leads
        (name,address,city,lat,lng,phone,email,years_owned,equity,
         score,motivation,timeline,approach,talking_points,
         email_outreach,sms_outreach,voicemail_outreach,
         status,source,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        lead["name"], lead["address"], lead["city"], lead["lat"], lead["lng"],
        lead["phone"], lead["email"], lead["years_owned"], lead["equity"],
        lead["score"], lead["motivation"], lead["timeline"], lead["approach"],
        lead["talking_points"], lead["email_outreach"], lead["sms_outreach"],
        lead["voicemail_outreach"], lead["status"], lead["source"], created
    ))

conn.commit()
conn.close()
print(f"✅ Seeded {len(DEMO_LEADS)} demo leads into database/leads.db")
