"""
Scraper — Amazon India vs Croma.com
  - If JINA_API_KEY is set → use r.jina.ai with Bearer auth (clean text, no HTML)
  - If not set            → direct httpx with browser headers + HTML stripping
"""

import re
import httpx
from urllib.parse import quote_plus
from app.core.config import get_settings

settings = get_settings()

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
}


def _clean_html(html: str) -> str:
    """Strip HTML tags and collapse whitespace to plain text."""
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>",   " ", text,  flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()[: settings.max_content_chars]


async def _fetch(url: str) -> str:
    """
    Fetch a URL as clean plain text.
    Uses Jina Reader (authenticated) if JINA_API_KEY is configured,
    otherwise falls back to direct httpx with real browser headers.
    """
    if settings.jina_api_key:
        jina_url = f"https://r.jina.ai/{url}"
        headers = {
            "Authorization": f"Bearer {settings.jina_api_key}",
            "Accept": "text/plain",
            "X-Return-Format": "text",
            "X-No-Cache": "true",
            "X-Remove-Selector": "header,footer,nav,script,style",
        }
        async with httpx.AsyncClient(
            timeout=settings.fetch_timeout, follow_redirects=True
        ) as c:
            r = await c.get(jina_url, headers=headers)
            r.raise_for_status()
            return r.text[: settings.max_content_chars]
    else:
        async with httpx.AsyncClient(
            timeout=settings.fetch_timeout,
            follow_redirects=True,
            headers=BROWSER_HEADERS,
        ) as c:
            r = await c.get(url)
            r.raise_for_status()
            return _clean_html(r.text)


# ── Amazon India ──────────────────────────────────────────────────────────────

async def search_amazon(product_name: str) -> dict:
    query = quote_plus(product_name)
    search_url = f"https://www.amazon.in/s?k={query}"
    try:
        content = await _fetch(search_url)
        return {"source": "Amazon India", "search_url": search_url, "content": content}
    except Exception as exc:
        return {"source": "Amazon India", "search_url": search_url,
                "content": f"Error fetching Amazon: {exc}"}


# ── Croma ─────────────────────────────────────────────────────────────────────

async def _google_search_croma(product_name: str) -> list[str]:
    """
    Use Google to find direct Croma product page URLs.
    Google indexes Croma product pages with prices in meta tags.
    """
    query = quote_plus(f"{product_name} site:croma.com")
    url = f"https://www.google.com/search?q={query}&num=5"
    try:
        content = await _fetch(url)
        # Extract croma.com/...../p/XXXXXX URLs
        urls = re.findall(r'https://www\.croma\.com/[^\s"<>]+/p/\d+', content)
        # Deduplicate
        seen, unique = set(), []
        for u in urls:
            if u not in seen:
                seen.add(u)
                unique.append(u)
        return unique[:4]
    except Exception:
        return []


async def search_croma(product_name: str) -> dict:
    """
    Croma is a React SPA — HTML pages are empty shells.
    Strategy:
    1. Use Google to find direct Croma product page URLs (Google indexes them with prices)
    2. Fetch each product page — Croma product pages have price in JSON-LD / meta tags
    3. Parse prices from the structured data
    """
    query = quote_plus(product_name)
    canonical_url = f"https://www.croma.com/search?q={query}"

    # ── Step 1: Find product URLs via Google ──────────────────────────────────
    product_urls = await _google_search_croma(product_name)

    if product_urls:
        lines = []
        for url in product_urls[:3]:
            try:
                async with httpx.AsyncClient(
                    timeout=settings.fetch_timeout,
                    follow_redirects=True,
                    headers=BROWSER_HEADERS,
                ) as c:
                    r = await c.get(url)
                    html = r.text

                # Extract price from JSON-LD structured data
                json_ld_matches = re.findall(
                    r'"price"\s*:\s*"?([\d,]+)"?', html
                )
                # Extract product name from title tag
                title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE)
                name = title_match.group(1).replace("| Croma", "").strip() if title_match else ""

                # Also try og:price or meta price
                meta_price = re.search(
                    r'(?:product:price:amount|og:price)["\s]+content="([\d,]+)"', html
                )
                price_val = meta_price.group(1) if meta_price else (
                    json_ld_matches[0] if json_ld_matches else ""
                )

                if name and price_val:
                    # Format price with ₹
                    price_str = f"₹{price_val}" if not price_val.startswith("₹") else price_val
                    lines.append(f"Product: {name} | Price: {price_str}")

            except Exception:
                continue

        if lines:
            return {
                "source": "Croma",
                "search_url": canonical_url,
                "content": "\n".join(lines),
            }

    # ── Fallback: Hardcode known price from Google search snippets ────────────
    # Google search already returned real Croma prices above (Rs 1,19,900 for 128GB etc.)
    # Use Groq to reason about these based on product name match
    try:
        g_query = quote_plus(f"{product_name} croma price india Rs")
        google_url = f"https://www.google.com/search?q={g_query}&num=5"
        content = await _fetch(google_url)
        if "croma" in content.lower() and (
            "Rs" in content or "₹" in content or "price" in content.lower()
        ):
            return {
                "source": "Croma (via Google)",
                "search_url": canonical_url,
                "content": content,
            }
    except Exception:
        pass

    return {
        "source": "Croma",
        "search_url": canonical_url,
        "content": "Could not fetch Croma pricing data.",
    }