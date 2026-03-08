# 🔍 PriceHunt AI

> Real-time product price comparison between **Amazon India** and **Croma** — powered by [Groq](https://groq.com) AI.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?style=flat-square&logo=fastapi)
![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-orange?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-purple?style=flat-square)

---

## ✨ Features

- 🛒 **Amazon India vs 🏪 Croma** — side-by-side price comparison
- 🤖 **Groq AI analysis** — extracts exact product matches, filters out unrelated results
- 💡 **Alternative suggestions** — similar devices at the same price range
- 🏆 **AI recommendation** — tells you where to buy and how much you save
- ⚡ **Fast** — Groq's LLaMA 3.3 70B delivers results in seconds
- 🌐 **Web UI** — clean dark-themed interface, no login required

---

## 📁 Project Structure

```
AiAgent/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app + serves frontend
│   ├── api/
│   │   ├── __init__.py          # api_router definition
│   │   └── routes/
│   │       ├── compare.py       # POST /api/v1/compare/
│   │       └── health.py        # GET /health + debug routes
│   ├── core/
│   │   └── config.py            # Pydantic settings (.env loader)
│   ├── models/
│   │   └── schemas.py           # Request/Response Pydantic models
│   └── services/
│       ├── agent.py             # Groq AI analysis loop
│       └── scraper.py           # Amazon + Croma scrapers
├── templates/
│   └── index.html               # Frontend (single-file HTML/CSS/JS)
├── tests/
│   └── test_compare.py
├── .env                         # Your API keys (not committed)
├── requirements.txt
└── run.py                       # Entry point
```

---

## 🚀 Setup & Installation

### 1. Clone & create virtual environment

```bash
git clone <your-repo-url>
cd AiAgent
python3 -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
APP_ENV=development
APP_PORT=8000
```

Get your free Groq API key at → [console.groq.com](https://console.groq.com)

### 4. Run the server

```bash
python run.py
```

### 5. Open in browser

```
http://localhost:8000
```

---

## 🔌 API Reference

### `GET /health`
Check server status.

**Response:**
```json
{
  "status": "ok",
  "env": "development",
  "model": "llama-3.3-70b-versatile",
  "groq_key_configured": true
}
```

---

### `POST /api/v1/compare/`
Compare product prices across Amazon India and Croma.

**Request body:**
```json
{
  "product": "iPhone 16 Pro"
}
```

**Response:**
```json
{
  "product": "iPhone 16 Pro",
  "amazon": [
    { "name": "Apple iPhone 16 Pro 128GB Desert Titanium", "price": "₹1,19,900", "rating": "4.5/5" }
  ],
  "croma": [
    { "name": "Apple iPhone 16 Pro 128GB Desert Titanium", "price": "₹1,19,900", "rating": "4.6/5" }
  ],
  "alternatives": [
    { "name": "iPhone 15 Pro 128GB", "price": "₹94,900", "platform": "Amazon", "note": "Same chip, saves ₹25,000" }
  ],
  "recommendation": "Both platforms offer the same price; choose Amazon for faster delivery.",
  "savings": null,
  "agent_steps": [ ... ],
  "amazon_search_url": "https://www.amazon.in/s?k=iPhone+16+Pro&i=electronics",
  "croma_search_url": "https://www.croma.com/search?q=iPhone+16+Pro"
}
```

---

### `GET /debug/amazon?q=<product>`
Test the Amazon scraper directly.

### `GET /debug/croma?q=<product>`
Test the Croma scraper directly.

---

## ⚙️ How It Works

```
User searches "iPhone 16 Pro"
        │
        ▼
┌─────────────────┐     ┌──────────────────────────────┐
│  Amazon scraper │     │  Croma scraper               │
│  amazon.in/s?k= │     │  Google → croma.com product  │
│  + electronics  │     │  pages → parse JSON-LD price │
└────────┬────────┘     └──────────────┬───────────────┘
         │                             │
         └──────────┬──────────────────┘
                    ▼
         ┌─────────────────────┐
         │   Groq LLaMA 3.3    │
         │   70B analysis      │
         │                     │
         │  - Extract exact    │
         │    model matches    │
         │  - Find alternatives│
         │  - Give verdict     │
         └──────────┬──────────┘
                    ▼
            JSON response
            → Web UI renders
```

### Croma Scraping Strategy

Croma is a React SPA — direct HTML scraping returns an empty shell. The scraper uses this fallback chain:

| Priority | Method | Why |
|----------|--------|-----|
| 1 | Google search → find `croma.com/p/XXXXX` URLs | Google indexes Croma product pages with prices |
| 2 | Fetch each product page → extract JSON-LD price | Product pages embed structured data |
| 3 | Pricebaba / Smartprix aggregators | Server-rendered pages listing Croma prices |

---

## 🛠️ Configuration Options

All settings are in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | — | **Required.** Your Groq API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model to use |
| `APP_ENV` | `development` | `development` enables hot reload |
| `APP_PORT` | `8000` | Port to run the server on |
| `MAX_AGENT_ITERATIONS` | `6` | Max scraper retries |
| `FETCH_TIMEOUT` | `30` | HTTP request timeout in seconds |
| `MAX_CONTENT_CHARS` | `8000` | Max chars to send to Groq |

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 🐛 Troubleshooting

**`Failed to fetch` in browser**
→ Make sure you open `http://localhost:8000` — NOT the HTML file directly (`file://...`)

**`ImportError: cannot import name 'api_router'`**
→ Delete all `__pycache__` folders:
```bash
find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
```

**Croma shows empty results**
→ Run the debug endpoint to check what's being fetched:
```bash
curl "http://localhost:8000/debug/croma?q=iPhone+16+Pro"
```

**Wrong Groq model error**
→ Make sure `.env` uses `llama-3.3-70b-versatile` (not the old deprecated models)

**Port already in use**
```bash
kill $(lsof -t -i:8000) && python run.py
```

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | 0.115.0 | Web framework |
| `uvicorn[standard]` | 0.30.6 | ASGI server |
| `httpx` | 0.27.2 | Async HTTP client for scraping |
| `groq` | 0.11.0 | Groq AI SDK |
| `pydantic` | 2.9.2 | Data validation |
| `pydantic-settings` | 2.5.2 | `.env` config loading |
| `python-dotenv` | 1.0.1 | Environment variables |

---

## 📄 License

MIT — free to use, modify, and distribute.

---

<p align="center">Built with ⚡ FastAPI + 🤖 Groq + 🐍 Python</p>
