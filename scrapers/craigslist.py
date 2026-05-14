"""
Craigslist FSBO scraper.
Maps city names → Craigslist subdomains, scrapes real-estate-for-sale listings,
geocodes each result, and returns standardised lead dicts.
"""
import re, time, requests
from bs4 import BeautifulSoup
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

_geo = Nominatim(user_agent="leadflow_scraper", timeout=5)

# City name (lowercase) → Craigslist subdomain
CITY_TO_SUBDOMAIN: dict[str, str] = {
    "san francisco": "sfbay", "san jose": "sfbay", "oakland": "sfbay",
    "berkeley": "sfbay", "san mateo": "sfbay", "burlingame": "sfbay",
    "daly city": "sfbay", "san bruno": "sfbay", "millbrae": "sfbay",
    "san carlos": "sfbay", "redwood city": "sfbay", "palo alto": "sfbay",
    "fremont": "sfbay", "hayward": "sfbay", "santa clara": "sfbay",
    "sunnyvale": "sfbay", "mountain view": "sfbay", "los altos": "sfbay",
    "los angeles": "losangeles", "long beach": "losangeles",
    "anaheim": "losangeles", "santa ana": "losangeles",
    "san diego": "sandiego", "chula vista": "sandiego",
    "sacramento": "sacramento", "fresno": "fresno", "bakersfield": "bakersfield",
    "seattle": "seattle", "tacoma": "seattle", "bellevue": "seattle",
    "portland": "portland", "eugene": "portland",
    "phoenix": "phoenix", "tempe": "phoenix", "scottsdale": "phoenix",
    "las vegas": "lasvegas", "henderson": "lasvegas",
    "denver": "denver", "aurora": "denver", "boulder": "denver",
    "chicago": "chicago", "naperville": "chicago",
    "houston": "houston", "dallas": "dallas", "austin": "austin",
    "san antonio": "sanantonio", "fort worth": "dallas",
    "new york": "newyork", "brooklyn": "newyork", "bronx": "newyork",
    "miami": "miami", "fort lauderdale": "miami", "orlando": "orlando",
    "atlanta": "atlanta", "charlotte": "charlotte",
    "boston": "boston", "cambridge": "boston",
    "washington": "washingtondc", "arlington": "washingtondc",
}

def _subdomain_for(city: str) -> str:
    key = city.lower().split(",")[0].strip()
    for k, v in CITY_TO_SUBDOMAIN.items():
        if k in key or key in k:
            return v
    return "sfbay"  # fallback

def _geocode(address: str, city: str) -> tuple[float, float]:
    try:
        loc = _geo.geocode(f"{address}, {city}")
        if loc:
            return loc.latitude, loc.longitude
    except GeocoderTimedOut:
        pass
    # Fallback: geocode just the city
    try:
        loc = _geo.geocode(city)
        if loc:
            return loc.latitude, loc.longitude
    except Exception:
        pass
    return 0.0, 0.0

def _parse_price(text: str) -> int:
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else 0

def scrape_craigslist_fsbo(city: str, max_results: int = 25) -> list[dict]:
    """
    Scrape Craigslist real-estate-for-sale (by owner) for a given city.
    Returns a list of lead dicts ready for the classification pipeline.
    """
    subdomain = _subdomain_for(city)
    # Craigslist real estate for sale — filter by owner keyword
    url = (
        f"https://{subdomain}.craigslist.org/search/rea"
        f"?query=by+owner&sort=date&s=0"
    )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    leads = []
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Craigslist switched to a new layout — handle both old and new
        items = soup.select("li.cl-search-result") or soup.select(".result-row")

        for item in items[:max_results]:
            # ── New layout ────────────────────────────────────────────────
            title_el = (item.select_one("a.cl-app-anchor") or
                        item.select_one(".result-title"))
            price_el = (item.select_one(".priceinfo") or
                        item.select_one(".result-price"))
            meta_el  = (item.select_one(".meta") or
                        item.select_one(".result-hood"))

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            price = _parse_price(price_el.get_text()) if price_el else 0
            hood  = meta_el.get_text(strip=True).strip("() ") if meta_el else city

            # Skip non-residential or suspiciously cheap listings
            if price and price < 50_000:
                continue

            lat, lng = _geocode(title, hood or city)

            leads.append({
                "name":        "FSBO Owner",
                "address":     title,
                "city":        hood or city,
                "lat":         lat,
                "lng":         lng,
                "phone":       "",
                "email":       "",
                "years_owned": 0,
                "equity":      price,
                "source":      "craigslist_fsbo",
                "listing_url": title_el.get("href", ""),
                "created_at":  datetime.now().isoformat(),
            })
            time.sleep(0.3)  # be polite to Craigslist

    except Exception as exc:
        print(f"[craigslist] Scrape failed for '{city}': {exc}")

    print(f"[craigslist] Found {len(leads)} FSBO listings for '{city}'")
    return leads
