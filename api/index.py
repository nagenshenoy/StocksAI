from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import numpy as np
import time
import os

app = Flask(__name__)
CORS(app)

# Serve the frontend from ../public when running locally
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), '..', 'public')

@app.route('/')
def index():
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(PUBLIC_DIR, filename)

STOCKS = {
    "Data Center Operators": {
        "Airtel": "BHARTIARTL.NS",
        "Lodha Developers": "LODHA.NS",
        "Adani Enterprises": "ADANIENT.NS",
        "Techno Electric": "TECHNOE.NS",
        "TCS": "TCS.NS",
        "Reliance": "RELIANCE.NS"
    },
    "Power & Electrical": {
        "Schneider Electric": "SCHNEIDER.NS",
        "Hitachi Energy": "POWERINDIA.NS",
        "CG Power": "CGPOWER.NS",
        "Cummins India": "CUMMINSIND.NS",
        "GE Power India": "GVPIL.NS",
        "GE Vernova T&D": "GVT&D.NS",
        "Apar Industries": "APARINDS.NS",
        "TD Power Systems": "TDPOWERSYS.NS",
        "MTAR Technologies": "MTARTECH.NS"
    },
    "Cooling": {
        "Aeroflex Industries": "AEROFLEX.NS",
        "KRN Heat Exchanger": "KRN.NS",
        "Dee Development Engineers": "DEEDEV.NS",
        "Voltas": "VOLTAS.NS",
        "Amber Enterprises": "AMBER.NS",
        "Blue Star": "BLUESTARCO.NS"
    },
    "Fiber / Networking": {
        "Sterlite Technologies": "STLTECH.NS",
        "HFCL": "HFCL.NS",
        "Finolex Cables": "FINCABLES.NS",
        "Bharti Hexacom": "BHARTIHEXA.NS",
        "Precision Wires": "PRECWIRE.NS"
    },
    "Compute & Hardware": {
        "Netweb Technologies": "NETWEB.NS",
        "E2E Networks": "E2E.NS"
    },
    "Managed Services": {
        "Dynacons Systems": "DSSL.NS",
        "Black Box": "BBOX.NS"
    },
    "Building / Construction": {
        "Interarch Building": "INTERARCH.NS",
        "Welspun Corp": "WELCORP.NS",
        "L&T": "LT.NS"
    }
}

# Build reverse lookup: ticker -> (name, sector)
TICKER_MAP = {}
ALL_TICKERS = []
for sector, stocks in STOCKS.items():
    for name, ticker in stocks.items():
        TICKER_MAP[ticker] = (name, sector)
        ALL_TICKERS.append(ticker)

# Simple in-memory cache
_cache = {}
CACHE_TTL = 60  # seconds

def get_cached(key):
    if key in _cache:
        data, ts = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return data
    return None

def set_cached(key, data):
    _cache[key] = (data, time.time())

def safe_val(val, default=None):
    if val is None:
        return default
    try:
        if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
            return default
        return val
    except Exception:
        return default

@app.route('/api/quotes')
def get_quotes():
    cached = get_cached('quotes')
    if cached:
        return jsonify(cached)

    results = []
    try:
        tickers_obj = yf.Tickers(' '.join(ALL_TICKERS))
        for ticker in ALL_TICKERS:
            try:
                name, sector = TICKER_MAP[ticker]
                info = tickers_obj.tickers[ticker].info
                fast = tickers_obj.tickers[ticker].fast_info

                def fi(attr):
                    """Safely read a fast_info attribute."""
                    try:
                        return getattr(fast, attr, None)
                    except Exception:
                        return None

                price = safe_val(fi('last_price') or info.get('currentPrice') or info.get('regularMarketPrice'))
                prev_close = safe_val(fi('previous_close') or info.get('previousClose') or info.get('regularMarketPreviousClose'))
                change = round(price - prev_close, 2) if price and prev_close else None
                change_pct = round((change / prev_close) * 100, 2) if change and prev_close else None

                results.append({
                    "name": name,
                    "ticker": ticker,
                    "sector": sector,
                    "price": safe_val(price),
                    "change": safe_val(change),
                    "change_pct": safe_val(change_pct),
                    "open": safe_val(fi('open') or info.get('open') or info.get('regularMarketOpen')),
                    "high": safe_val(fi('day_high') or info.get('dayHigh') or info.get('regularMarketDayHigh')),
                    "low": safe_val(fi('day_low') or info.get('dayLow') or info.get('regularMarketDayLow')),
                    "volume": safe_val(fi('three_month_average_volume') or info.get('volume') or info.get('regularMarketVolume')),
                    "market_cap": safe_val(fi('market_cap') or info.get('marketCap')),
                    "pe_ratio": safe_val(info.get('trailingPE') or info.get('forwardPE')),
                    "week52_high": safe_val(fi('year_high') or info.get('fiftyTwoWeekHigh')),
                    "week52_low": safe_val(fi('year_low') or info.get('fiftyTwoWeekLow')),
                    "beta": safe_val(info.get('beta'))
                })
            except Exception as e:
                name, sector = TICKER_MAP.get(ticker, (ticker, 'Unknown'))
                results.append({
                    "name": name,
                    "ticker": ticker,
                    "sector": sector,
                    "price": None, "change": None, "change_pct": None,
                    "open": None, "high": None, "low": None,
                    "volume": None, "market_cap": None, "pe_ratio": None,
                    "week52_high": None, "week52_low": None, "beta": None,
                    "error": str(e)
                })
    except Exception as e:
        return jsonify({"error": str(e), "data": results}), 500

    set_cached('quotes', results)
    return jsonify(results)

@app.route('/api/history')
def get_history():
    ticker = request.args.get('ticker', '')
    period = request.args.get('period', '1mo')
    if period not in ['1d', '5d', '1mo', '3mo', '1y']:
        period = '1mo'

    cache_key = f'history_{ticker}_{period}'
    cached = get_cached(cache_key)
    if cached:
        return jsonify(cached)

    try:
        interval = '5m' if period == '1d' else '1d'
        hist = yf.Ticker(ticker).history(period=period, interval=interval)
        data = []
        for idx, row in hist.iterrows():
            data.append({
                "date": str(idx.date() if period != '1d' else idx),
                "open": safe_val(row.get('Open')),
                "high": safe_val(row.get('High')),
                "low": safe_val(row.get('Low')),
                "close": safe_val(row.get('Close')),
                "volume": safe_val(row.get('Volume'))
            })
        result = {"ticker": ticker, "period": period, "data": data}
        set_cached(cache_key, result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "ticker": ticker, "period": period, "data": []}), 500

@app.route('/api/sparklines')
def get_sparklines():
    cached = get_cached('sparklines')
    if cached:
        return jsonify(cached)

    result = {}
    try:
        hist = yf.download(
            ' '.join(ALL_TICKERS),
            period='7d',
            interval='1d',
            group_by='ticker',
            auto_adjust=True,
            progress=False
        )
        for ticker in ALL_TICKERS:
            try:
                if len(ALL_TICKERS) == 1:
                    closes = hist['Close'].dropna().tolist()
                else:
                    closes = hist[ticker]['Close'].dropna().tolist()
                result[ticker] = [round(c, 2) for c in closes]
            except Exception:
                result[ticker] = []
    except Exception as e:
        for ticker in ALL_TICKERS:
            result[ticker] = []

    set_cached('sparklines', result)
    return jsonify(result)

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "tickers": len(ALL_TICKERS)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
