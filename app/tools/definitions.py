"""
Tool schemas passed to the Groq chat-completion API.
Each dict follows the OpenAI/Groq function-calling format.
"""

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_amazon",
            "description": (
                "Search for a product on Amazon India and return the raw page text "
                "containing product listings with prices, ratings, and names."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "The product name to search for on Amazon India.",
                    }
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_flipkart",
            "description": (
                "Search for a product on Flipkart and return the raw page text "
                "containing product listings with prices, ratings, and names."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "The product name to search for on Flipkart.",
                    }
                },
                "required": ["product_name"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are PriceHunt, a smart AI price comparison agent for India.

When a user asks about a product you MUST:
1. Call search_amazon with the product name
2. Call search_flipkart with the product name
3. Parse the returned text and extract the top 2-3 product listings per platform

After calling both tools, respond ONLY with a valid JSON object (no markdown fences):
{
  "product": "<cleaned product name>",
  "amazon": [
    {"name": "<product title>", "price": "₹X,XXX", "rating": "<X.X/5>", "link": null}
  ],
  "flipkart": [
    {"name": "<product title>", "price": "₹X,XXX", "rating": "<X.X/5>", "link": null}
  ],
  "recommendation": "<one-sentence verdict>",
  "savings": "<e.g. You save ₹500 by choosing Flipkart or null>"
}

Rules:
- You MUST call both tools before responding with JSON.
- Extract ACTUAL prices from tool results (look for ₹ symbols).
- If a price is missing, use "N/A".
- ALWAYS set "link" to null — never generate or guess product URLs.
- Only output the JSON object after tools have been called, nothing else.
"""