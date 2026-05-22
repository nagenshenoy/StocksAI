# India AI & Data Center Stock Tracker

A Bloomberg-style terminal dashboard tracking NSE-listed stocks across India's AI and data center infrastructure ecosystem.

## Features

- **37 stocks** across 7 sectors (Data Centers, Power, Cooling, Fiber, Compute, Managed Services, Construction)
- Live price data via Yahoo Finance / yfinance
- Sortable stock table with sparklines, sector filters, KPI summary
- Interactive Chart.js price charts (1D / 5D / 1M / 3M / 1Y)
- Market status indicator (NSE hours: 9:15–15:30 IST)
- Auto-refresh every 60 seconds with countdown
- Responsive: full table on desktop, card view on mobile

## Local Development

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Flask API server
```bash
# Windows
cd api
set FLASK_APP=index.py
flask run --port 5000

# macOS / Linux
cd api
FLASK_APP=index.py flask run --port 5000
```

### 3. Open the app
Visit **http://localhost:5000** in your browser — Flask now serves both the frontend and the API from the same port. No CORS issues, no file:// workarounds needed.

## Deploy to Vercel

### Prerequisites
```bash
npm i -g vercel
vercel login
```

### Deploy
```bash
cd ai-dc-tracker
vercel --prod
```

Vercel will automatically:
- Deploy `api/index.py` as a Python serverless function
- Serve `public/index.html` as a static asset
- Route `/api/*` requests to Flask, everything else to the frontend

## Project Structure

```
ai-dc-tracker/
├── vercel.json          # Vercel routing config
├── requirements.txt     # Python deps for serverless
├── README.md
├── api/
│   └── index.py         # Flask API (3 endpoints)
└── public/
    └── index.html       # Complete frontend (CSS + JS embedded)
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/quotes` | Current price data for all 37 stocks |
| `GET /api/history?ticker=X&period=1mo` | OHLCV history for one ticker |
| `GET /api/sparklines` | 7-day closing prices for all tickers (batch) |
| `GET /api/health` | Health check |

### Supported `period` values
`1d`, `5d`, `1mo`, `3mo`, `1y`

## Stock Universe

| Sector | Count |
|--------|-------|
| Data Center Operators | 6 |
| Power & Electrical | 9 |
| Cooling | 6 |
| Fiber / Networking | 5 |
| Compute & Hardware | 2 |
| Managed Services | 2 |
| Building / Construction | 3 |

## Data Source

Yahoo Finance via the `yfinance` library. NSE data is typically delayed ~15 minutes.

## Disclaimer

For informational purposes only. Not investment advice. Past performance is not indicative of future results.
