"""Seed demo leads matched to the Menifee → San Diego corridor."""
import sqlite3, json, os
from datetime import datetime, timedelta

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

# ── Clear any old Bay Area demo leads ──────────────────────────────────────
conn.execute("DELETE FROM leads WHERE city LIKE '%San Mateo%' OR city LIKE '%Burlingame%' OR city LIKE '%Millbrae%' OR city LIKE '%San Carlos%' OR city LIKE '%Daly City%' OR city LIKE '%South San Francisco%' OR city LIKE '%San Bruno%'")
conn.commit()
print("🧹 Cleared old Bay Area demo leads")

DEMO_LEADS = [
    # ── Menifee side ────────────────────────────────────────────────────────
    {
        "name": "Carlos & Maria Reyes",
        "address": "29410 Stonegate Dr",
        "city": "Menifee, CA",
        "lat": 33.6972, "lng": -117.1844,
        "phone": "951-555-0142", "email": "",
        "years_owned": 12, "equity": 290000,
        "score": 9, "motivation": "hot",
        "timeline": "0-3mo", "approach": "phone",
        "talking_points": json.dumps([
            "12 years owned — strong equity position",
            "Price dropped twice on Zillow this month",
            "Kids now at college — empty nesters",
            "$290k equity — motivated to unlock"
        ]),
        "email_outreach": "Hi Carlos & Maria,\n\nI noticed your home on Stonegate Drive and wanted to reach out — the Menifee market is moving fast right now, and homes with your equity position are exactly what buyers in the San Diego corridor are hunting for.\n\nWould you be open to a quick, no-pressure conversation about what your options look like?\n\nWarm regards,\nEllen Beltran",
        "sms_outreach": "Hi Carlos, I work with homeowners in Menifee looking to upgrade toward San Diego. Your equity could go a long way. Happy to chat whenever works! — Ellen Beltran",
        "voicemail_outreach": "Hi Carlos, this is Ellen Beltran. I specialize in the Menifee to San Diego corridor and your home on Stonegate caught my attention. I'd love to share what comparable homes are fetching right now — no pressure at all. Please call me back whenever you get a chance!",
        "source": "craigslist_fsbo",
        "status": "new",
    },
    {
        "name": "Rachel Tompkins",
        "address": "25880 Newport Rd",
        "city": "Menifee, CA",
        "lat": 33.6843, "lng": -117.2021,
        "phone": "951-555-0289", "email": "",
        "years_owned": 8, "equity": 195000,
        "score": 7, "motivation": "hot",
        "timeline": "3-6mo", "approach": "email",
        "talking_points": json.dumps([
            "FSBO listing on Craigslist — selling without agent",
            "8 years equity built up",
            "Relocating for new job signal"
        ]),
        "email_outreach": "Hi Rachel,\n\nI came across your FSBO listing and wanted to reach out. Many sellers in Menifee who start FSBO end up leaving money on the table in the final negotiation — I'd love to show you what a represented sale could net you versus going it alone.\n\nNo commitment, just data. Would a 15-minute call work?\n\nBest,\nEllen Beltran",
        "sms_outreach": "Hi Rachel, saw your FSBO listing in Menifee! I help sellers maximize their net in the Menifee-San Diego corridor. Happy to share a quick comparison — no obligation. — Ellen Beltran",
        "voicemail_outreach": "Hi Rachel, this is Ellen Beltran calling about your Menifee home. FSBO sellers in this corridor are often surprised by what a full-service listing nets them. I'd love to share the numbers with you — no pressure at all. Call me back at your convenience!",
        "source": "craigslist_fsbo",
        "status": "new",
    },
    {
        "name": "David & Kim Park",
        "address": "27300 Encanto Dr",
        "city": "Menifee, CA",
        "lat": 33.7213, "lng": -117.1652,
        "phone": "951-555-0371", "email": "",
        "years_owned": 18, "equity": 410000,
        "score": 8, "motivation": "hot",
        "timeline": "0-3mo", "approach": "phone",
        "talking_points": json.dumps([
            "18 years — retirement age signal",
            "$410k equity — largest in corridor",
            "Downsizing candidate",
            "County records — no recent activity"
        ]),
        "email_outreach": "Hi David & Kim,\n\nAfter 18 years in Menifee, you've built an extraordinary equity position — over $400,000. Many homeowners at this stage find that the timing is right to either downsize locally or leverage that equity to move closer to San Diego.\n\nI'd love to walk you through what the current market looks like and what a sale could mean for your next chapter.\n\nEllen Beltran",
        "sms_outreach": "Hi David, 18 years in Menifee has built serious equity! If downsizing or a move toward San Diego is on your radar, I'd love to share the numbers. — Ellen Beltran",
        "voicemail_outreach": "Hi David, this is Ellen Beltran. After 18 years in Menifee you've built remarkable equity, and I think you'd be surprised what your home could sell for right now. I'd love to chat — please give me a call when you get a chance!",
        "source": "county_records",
        "status": "new",
    },
    # ── Mid-corridor ────────────────────────────────────────────────────────
    {
        "name": "Tom & Jessica Avila",
        "address": "34120 Brixton St",
        "city": "Murrieta, CA",
        "lat": 33.5539, "lng": -117.2139,
        "phone": "951-555-0498", "email": "",
        "years_owned": 6, "equity": 175000,
        "score": 6, "motivation": "warm",
        "timeline": "3-6mo", "approach": "direct_mail",
        "talking_points": json.dumps([
            "Growing family, likely upsizing",
            "6 years equity",
            "Searched San Diego schools online"
        ]),
        "email_outreach": "",
        "sms_outreach": "Hi Jessica, homes in Murrieta near the I-15 are moving fast! If upsizing toward San Diego is on your mind, I'd love to help map out the options. — Ellen Beltran",
        "voicemail_outreach": "",
        "source": "craigslist_fsbo",
        "status": "new",
    },
    {
        "name": "Andre Johnson",
        "address": "41880 Calle Medusa",
        "city": "Temecula, CA",
        "lat": 33.4936, "lng": -117.1484,
        "phone": "951-555-0612", "email": "",
        "years_owned": 4, "equity": 120000,
        "score": 5, "motivation": "warm",
        "timeline": "6-12mo", "approach": "email",
        "talking_points": json.dumps([
            "Relocation signal — job posting in San Diego",
            "4 years owned",
            "Starter home, likely ready to upgrade"
        ]),
        "email_outreach": "",
        "sms_outreach": "Hi Andre, congrats on the new opportunity! If a move toward San Diego is in the cards, Temecula homes are in demand right now. Happy to provide a free valuation. — Ellen Beltran",
        "voicemail_outreach": "",
        "source": "craigslist_fsbo",
        "status": "contacted",
    },
    # ── San Diego side ──────────────────────────────────────────────────────
    {
        "name": "Linda Okafor",
        "address": "5920 Rancho Mission Rd",
        "city": "San Diego, CA",
        "lat": 32.7886, "lng": -117.0847,
        "phone": "619-555-0733", "email": "",
        "years_owned": 15, "equity": 540000,
        "score": 8, "motivation": "hot",
        "timeline": "0-3mo", "approach": "phone",
        "talking_points": json.dumps([
            "15 years owned — strong equity",
            "$540k equity in San Diego market",
            "Retirement signal — recent searches",
            "Downsizing to Menifee or Temecula corridor"
        ]),
        "email_outreach": "Hi Linda,\n\nAfter 15 years on Rancho Mission Road, you've built an incredible equity position. Many San Diego homeowners in your situation are finding that moving to the Menifee/Temecula corridor lets them pocket significant cash while maintaining a great lifestyle.\n\nI'd love to walk you through what your home is worth today and what the move could look like.\n\nEllen Beltran",
        "sms_outreach": "Hi Linda, 15 years in San Diego has built serious equity! If downsizing toward Menifee or Temecula is on your mind, I'd love to run the numbers for you. — Ellen Beltran",
        "voicemail_outreach": "Hi Linda, this is Ellen Beltran. I specialize in the San Diego to Menifee corridor and your home on Rancho Mission caught my attention. With your equity position, your options are really exciting. Please call me back at your convenience!",
        "source": "county_records",
        "status": "new",
    },
    {
        "name": "Marco & Sofia Delgado",
        "address": "2840 Dewey Rd",
        "city": "San Diego, CA",
        "lat": 32.7209, "lng": -117.1356,
        "phone": "619-555-0891", "email": "",
        "years_owned": 9, "equity": 310000,
        "score": 7, "motivation": "hot",
        "timeline": "0-3mo", "approach": "email",
        "talking_points": json.dumps([
            "FSBO listing — selling without agent",
            "9 years equity in San Diego",
            "Listed and pulled twice — motivated"
        ]),
        "email_outreach": "Hi Marco & Sofia,\n\nI noticed your home on Dewey Road and wanted to reach out. The San Diego market is competitive right now and FSBO sellers are often leaving 5-8% on the table in negotiations.\n\nI'd love to show you what a full-service listing could net you. Can we find 15 minutes this week?\n\nEllen Beltran",
        "sms_outreach": "Hi Marco, saw your FSBO listing in San Diego! I help sellers in this market maximize their net. Quick comparison — no obligation? — Ellen Beltran",
        "voicemail_outreach": "Hi Marco, this is Ellen Beltran. I saw your home on Dewey and wanted to reach out — FSBO sellers in San Diego are often surprised by what represented listings net them. I'd love to share the data. Call me back when you get a chance!",
        "source": "craigslist_fsbo",
        "status": "new",
    },
]

ts_base = datetime.now()
added = 0
for i, lead in enumerate(DEMO_LEADS):
    # Skip if address already exists
    exists = conn.execute("SELECT id FROM leads WHERE address=?", (lead["address"],)).fetchone()
    if exists:
        continue
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
    added += 1

conn.commit()
conn.close()
print(f"✅ Seeded {added} Menifee→San Diego corridor leads into database/leads.db")
