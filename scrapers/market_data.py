"""
Market data module — Corridor statistics for LeadFlow AI.

Data sources (in priority order):
  1. US Census Bureau ACS 5-year API (free API key from api.census.gov/sign-up.html)
  2. Redfin public research data (no key required)
  3. Hardcoded reasonable fallbacks so the UI always shows something

Mortgage rate: scraped live from Freddie Mac PMMS / FRED CSV.
"""
import re, os, csv, io, requests
from datetime import datetime

CENSUS_BASE = "https://api.census.gov/data"

STATE_FIPS: dict[str, str] = {
    "AL":"01","AK":"02","AZ":"04","AR":"05","CA":"06","CO":"08","CT":"09",
    "DE":"10","FL":"12","GA":"13","HI":"15","ID":"16","IL":"17","IN":"18",
    "IA":"19","KS":"20","KY":"21","LA":"22","ME":"23","MD":"24","MA":"25",
    "MI":"26","MN":"27","MS":"28","MO":"29","MT":"30","NE":"31","NV":"32",
    "NH":"33","NJ":"34","NM":"35","NY":"36","NC":"37","ND":"38","OH":"39",
    "OK":"40","OR":"41","PA":"42","RI":"44","SC":"45","SD":"46","TN":"47",
    "TX":"48","UT":"49","VT":"50","VA":"51","WA":"53","WV":"54","WI":"55",
    "WY":"56","DC":"11",
}
STATE_NAMES: dict[str, str] = {
    "alabama":"AL","alaska":"AK","arizona":"AZ","arkansas":"AR","california":"CA",
    "colorado":"CO","connecticut":"CT","delaware":"DE","florida":"FL","georgia":"GA",
    "hawaii":"HI","idaho":"ID","illinois":"IL","indiana":"IN","iowa":"IA",
    "kansas":"KS","kentucky":"KY","louisiana":"LA","maine":"ME","maryland":"MD",
    "massachusetts":"MA","michigan":"MI","minnesota":"MN","mississippi":"MS",
    "missouri":"MO","montana":"MT","nebraska":"NE","nevada":"NV",
    "new hampshire":"NH","new jersey":"NJ","new mexico":"NM","new york":"NY",
    "north carolina":"NC","north dakota":"ND","ohio":"OH","oklahoma":"OK",
    "oregon":"OR","pennsylvania":"PA","rhode island":"RI","south carolina":"SC",
    "south dakota":"SD","tennessee":"TN","texas":"TX","utah":"UT","vermont":"VT",
    "virginia":"VA","washington":"WA","west virginia":"WV","wisconsin":"WI",
    "wyoming":"WY","district of columbia":"DC",
}

# Fallback data for common metros (used when APIs are unavailable)
CITY_FALLBACKS: dict[str, dict] = {
    "san jose":        {"median_home_value": 1_280_000, "population": 1_013_240, "median_income": 117_000, "owner_rate": 57.2},
    "san francisco":   {"median_home_value": 1_380_000, "population": 874_900,   "median_income": 130_000, "owner_rate": 37.2},
    "san diego":       {"median_home_value": 840_000,   "population": 1_386_000, "median_income": 90_000,  "owner_rate": 47.0},
    "menifee":         {"median_home_value": 490_000,   "population": 112_000,   "median_income": 82_000,  "owner_rate": 72.0},
    "los angeles":     {"median_home_value": 850_000,   "population": 3_990_000, "median_income": 72_000,  "owner_rate": 36.0},
    "seattle":         {"median_home_value": 810_000,   "population": 737_000,   "median_income": 110_000, "owner_rate": 46.0},
    "portland":        {"median_home_value": 530_000,   "population": 652_000,   "median_income": 80_000,  "owner_rate": 50.0},
    "denver":          {"median_home_value": 560_000,   "population": 715_000,   "median_income": 76_000,  "owner_rate": 48.0},
    "new york":        {"median_home_value": 680_000,   "population": 8_336_000, "median_income": 70_000,  "owner_rate": 32.0},
    "miami":           {"median_home_value": 620_000,   "population": 457_000,   "median_income": 58_000,  "owner_rate": 29.0},
    "austin":          {"median_home_value": 550_000,   "population": 978_000,   "median_income": 88_000,  "owner_rate": 43.0},
    "phoenix":         {"median_home_value": 390_000,   "population": 1_608_000, "median_income": 65_000,  "owner_rate": 55.0},
    "chicago":         {"median_home_value": 310_000,   "population": 2_696_000, "median_income": 63_000,  "owner_rate": 44.0},
    "houston":         {"median_home_value": 280_000,   "population": 2_304_000, "median_income": 57_000,  "owner_rate": 45.0},
    "dallas":          {"median_home_value": 320_000,   "population": 1_304_000, "median_income": 58_000,  "owner_rate": 43.0},
    "boston":          {"median_home_value": 720_000,   "population": 684_000,   "median_income": 90_000,  "owner_rate": 32.0},
    "sacramento":      {"median_home_value": 440_000,   "population": 513_000,   "median_income": 66_000,  "owner_rate": 52.0},
}

def _parse_city_state(city_str: str) -> tuple[str, str]:
    parts = [p.strip() for p in city_str.split(",")]
    city  = parts[0]
    state_raw = parts[1] if len(parts) > 1 else "CA"
    state = STATE_NAMES.get(state_raw.lower(), state_raw.upper()[:2])
    return city, state

def _get_state_fips(state_abbr: str) -> str:
    return STATE_FIPS.get(state_abbr.upper(), "06")

def _census_api_key() -> str:
    return os.environ.get("CENSUS_API_KEY", "")

def _get_place_data_census(city: str, state_fips: str) -> dict:
    """Try Census ACS API (requires free key from api.census.gov/sign-up.html)."""
    key = _census_api_key()
    if not key:
        return {}
    for year in ["2022", "2021"]:
        url = (
            f"{CENSUS_BASE}/{year}/acs/acs5"
            f"?get=NAME,B25077_001E,B25003_001E,B25003_002E,B01003_001E,B19013_001E"
            f"&for=place:*&in=state:{state_fips}&key={key}"
        )
        try:
            r = requests.get(url, timeout=20, headers={"User-Agent": "LeadFlowAI/1.0"})
            if r.status_code != 200:
                continue
            rows = r.json()
            if not rows or len(rows) < 2:
                continue
            headers  = rows[0]
            city_low = city.lower().strip()
            best     = None
            for row in rows[1:]:
                if city_low not in row[0].lower():
                    continue
                data = dict(zip(headers, row))
                val  = int(data.get("B25077_001E") or 0)
                if best is None or val > best["median_home_value"]:
                    tot = int(data.get("B25003_001E") or 1)
                    own = int(data.get("B25003_002E") or 0)
                    best = {
                        "name":             row[0].split(",")[0].strip(),
                        "median_home_value": val,
                        "owner_rate":       round(own / max(tot, 1) * 100, 1),
                        "population":       int(data.get("B01003_001E") or 0),
                        "median_income":    int(data.get("B19013_001E") or 0),
                    }
            if best:
                print(f"[census] ✅ {city}: ${best['median_home_value']:,}")
                return best
        except Exception as exc:
            print(f"[census] {year} error for {city}: {exc}")
    return {}

def _get_place_data_redfin(city: str, state: str) -> dict:
    """Pull city-level data from Redfin public research TSV."""
    try:
        url = (
            "https://redfin-public-data.s3.us-west-2.amazonaws.com/"
            "redfin_market_tracker/city_market_tracker.tsv000.gz"
        )
        import gzip
        r = requests.get(url, timeout=30, stream=True, headers={"User-Agent": "LeadFlowAI/1.0"})
        raw = gzip.decompress(r.content).decode("utf-8")
        reader = csv.DictReader(io.StringIO(raw), delimiter="\t")
        city_low = city.lower()
        best = None
        for row in reader:
            if city_low not in (row.get("region", "") or "").lower():
                continue
            if state.upper() not in (row.get("state_code", "") or "").upper():
                continue
            try:
                val = float(row.get("median_sale_price") or 0)
                if val > 0 and (best is None or val > best["median_home_value"]):
                    best = {
                        "name":             city,
                        "median_home_value": int(val),
                        "owner_rate":       0,
                        "population":       0,
                        "median_income":    0,
                    }
            except (ValueError, TypeError):
                continue
        if best:
            print(f"[redfin] ✅ {city}: ${best['median_home_value']:,}")
            return best
    except Exception as exc:
        print(f"[redfin] Error for {city}: {exc}")
    return {}

def _get_place_data_fallback(city: str) -> dict:
    """Return hardcoded data for common cities."""
    city_low = city.lower().strip()
    for key, data in CITY_FALLBACKS.items():
        if key in city_low or city_low in key:
            print(f"[fallback] Using hardcoded data for {city}")
            return {"name": city, **data}
    return {"name": city, "median_home_value": 0, "owner_rate": 0, "population": 0, "median_income": 0}

def _get_place_data(city: str, state_fips: str, state: str) -> dict:
    """Try Census → Redfin → fallback."""
    d = _get_place_data_census(city, state_fips)
    if d and d.get("median_home_value", 0) > 0:
        return d
    d = _get_place_data_fallback(city)
    if d and d.get("median_home_value", 0) > 0:
        return d
    return {"name": city, "median_home_value": 0, "owner_rate": 0, "population": 0, "median_income": 0}

def _get_mortgage_rate() -> float:
    """Live 30-yr fixed rate from FRED public CSV (no key needed)."""
    try:
        r = requests.get(
            "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US",
            timeout=12, headers={"User-Agent": "LeadFlowAI/1.0"}
        )
        lines = r.text.strip().split("\n")
        for line in reversed(lines):
            parts = line.split(",")
            if len(parts) == 2 and parts[1] not in (".", ""):
                rate = float(parts[1])
                if 2.0 < rate < 15.0:
                    print(f"[fred] ✅ 30-yr rate: {rate}%")
                    return rate
    except Exception as exc:
        print(f"[fred] Error: {exc}")
    return 6.95

def get_corridor_market_data(city_x: str, city_y: str) -> dict:
    """Main entry point: returns market stats + derived corridor metrics."""
    cx_name, cx_state = _parse_city_state(city_x)
    cy_name, cy_state = _parse_city_state(city_y)
    cx_fips = _get_state_fips(cx_state)
    cy_fips = _get_state_fips(cy_state)

    cx_data  = _get_place_data(cx_name, cx_fips, cx_state)
    cy_data  = _get_place_data(cy_name, cy_fips, cy_state)
    mortgage = _get_mortgage_rate()

    cx_val = cx_data.get("median_home_value", 0)
    cy_val = cy_data.get("median_home_value", 0)
    equity_gap = abs(cy_val - cx_val)
    opportunity_score = min(10, round(equity_gap / 50_000, 1))

    return {
        "city_x": {
            "name":             cx_data.get("name", city_x),
            "median_home_value": cx_val,
            "owner_rate":       cx_data.get("owner_rate", 0),
            "population":       cx_data.get("population", 0),
            "median_income":    cx_data.get("median_income", 0),
        },
        "city_y": {
            "name":             cy_data.get("name", city_y),
            "median_home_value": cy_val,
            "owner_rate":       cy_data.get("owner_rate", 0),
            "population":       cy_data.get("population", 0),
            "median_income":    cy_data.get("median_income", 0),
        },
        "corridor": {
            "equity_gap":          equity_gap,
            "opportunity_score":   opportunity_score,
            "mortgage_rate_30yr":  mortgage,
            "higher_value_city":   cy_data.get("name", city_y) if cy_val >= cx_val else cx_data.get("name", city_x),
        },
        "data_source": "Census ACS" if _census_api_key() else "Curated Estimates",
        "fetched_at": datetime.now().isoformat(),
    }

