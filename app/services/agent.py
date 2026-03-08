"""
Price comparison agent — Amazon India vs Croma.com
"""

import json
import re
from groq import AsyncGroq

from app.core.config import get_settings
from app.models.schemas import AgentStep, CompareResponse, ProductListing, AlternativeProduct
from app.services.scraper import search_amazon, search_croma

settings = get_settings()


SYSTEM_PROMPT = """You are PriceHunt, a smart price comparison AI for India.

You will receive:
1. Amazon India raw search text + pre-extracted ₹ price hints
2. Croma data — structured lines like "Product: Apple iPhone 16 Pro 128GB | Price: ₹1,19,900"
   OR raw Google snippet text mentioning Croma prices

Your job:
- Extract ONLY listings that EXACTLY match the searched product (same model name/number)
- Do NOT include unrelated models (e.g. if user searches "iPhone 16 Pro", do not include iPhone Air, iPhone 17, iPhone 15)
- Extract top 2-3 exact-match listings per platform with name, price, rating
- Suggest 3-4 alternative/similar products visible in the scraped text at similar or lower prices
  These can be different storage variants, competing brands, or related models
- Return ONLY a valid JSON object — no markdown, no explanation

Required JSON format:
{
  "product": "<cleaned product name>",
  "amazon": [
    {"name": "<exact product title>", "price": "₹X,XXX", "rating": "<X.X/5 or null>"}
  ],
  "croma": [
    {"name": "<exact product title>", "price": "₹X,XXX", "rating": "<X.X/5 or null>"}
  ],
  "alternatives": [
    {
      "name": "<alternative product name>",
      "price": "₹X,XXX",
      "platform": "Amazon or Croma",
      "note": "<one short reason why someone should consider this — e.g. 'Same camera, saves ₹10,000' or 'Better battery life'>"
    }
  ],
  "recommendation": "<one clear sentence: which platform to buy the searched product from and why>",
  "savings": "<e.g. You save ₹500 by choosing Croma — or null if prices are equal>"
}

Rules:
- STRICT model matching for amazon/croma arrays — only the exact searched product
- Convert "Rs X,XX,XXX" to "₹X,XX,XXX" in output
- ONLY use prices visible in the provided text — never invent prices
- If no exact match found for a platform, return empty array []
- For alternatives: pick real products from the scraped text — different storage sizes count
- Return ONLY the JSON object, nothing else
"""


def _extract_price_hints(text: str) -> list[str]:
    found = re.findall(r"₹\s?[\d,]+(?:\.\d{1,2})?", text)
    seen, unique = set(), []
    for p in found:
        c = p.replace(" ", "")
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique[:10]


def _extract_json(text: str) -> dict | None:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return None


def _build_response(parsed, steps, raw, amazon_url, croma_url) -> CompareResponse:
    def to_listings(items):
        return [
            ProductListing(
                name=item.get("name", "Unknown Product"),
                price=item.get("price", "N/A"),
                rating=item.get("rating") or None,
                link=None,
            )
            for item in (items or [])
        ]

    def to_alternatives(items):
        return [
            AlternativeProduct(
                name=item.get("name", ""),
                price=item.get("price", "N/A"),
                platform=item.get("platform", ""),
                note=item.get("note") or None,
            )
            for item in (items or [])
        ]

    return CompareResponse(
        product=parsed.get("product", ""),
        amazon=to_listings(parsed.get("amazon", [])),
        croma=to_listings(parsed.get("croma", [])),
        alternatives=to_alternatives(parsed.get("alternatives", [])),
        amazon_search_url=amazon_url,
        croma_search_url=croma_url,
        recommendation=parsed.get("recommendation"),
        savings=parsed.get("savings"),
        agent_steps=steps,
        raw_response=raw,
    )


async def run_price_agent(product: str, api_key: str) -> CompareResponse:
    client = AsyncGroq(api_key=api_key)
    steps: list[AgentStep] = []
    step = 0

    step += 1
    steps.append(AgentStep(step=step, type="tool_call", message=f"Searching Amazon India for '{product}'…"))
    amazon_data = await search_amazon(product)
    amazon_content = amazon_data.get("content", "")
    amazon_hints = _extract_price_hints(amazon_content)
    step += 1
    steps.append(AgentStep(step=step, type="tool_result",
                            message=f"Amazon — {len(amazon_content)} chars, prices: {', '.join(amazon_hints[:5]) or 'none'}"))

    step += 1
    steps.append(AgentStep(step=step, type="tool_call", message=f"Searching Croma for '{product}'…"))
    croma_data = await search_croma(product)
    croma_content = croma_data.get("content", "")
    croma_hints = _extract_price_hints(croma_content)
    step += 1
    steps.append(AgentStep(step=step, type="tool_result",
                            message=f"{croma_data['source']} — {len(croma_content)} chars, prices: {', '.join(croma_hints[:5]) or 'none'}"))

    step += 1
    steps.append(AgentStep(step=step, type="thinking", message="Analysing prices with Groq AI…"))

    user_message = f"""Compare prices for: {product}

=== AMAZON INDIA — PRICE HINTS ===
{', '.join(amazon_hints) if amazon_hints else 'None found'}

=== AMAZON INDIA — RAW TEXT ===
{amazon_content[:3500]}

=== CROMA — PRICE HINTS ===
{', '.join(croma_hints) if croma_hints else 'None found'}

=== CROMA — RAW TEXT (source: {croma_data.get('source')}) ===
{croma_content[:3500]}
"""

    response = await client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.1,
        max_tokens=1500,
    )

    raw_text = response.choices[0].message.content or ""
    step += 1
    steps.append(AgentStep(step=step, type="done", message="Analysis complete!"))

    parsed = _extract_json(raw_text)
    if parsed:
        return _build_response(parsed, steps, raw_text,
                                amazon_data.get("search_url", ""),
                                croma_data.get("search_url", ""))

    return CompareResponse(
        product=product,
        amazon_search_url=amazon_data.get("search_url", ""),
        croma_search_url=croma_data.get("search_url", ""),
        agent_steps=steps,
        raw_response=raw_text,
    )