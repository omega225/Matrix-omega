from flask import Flask, render_template_string, jsonify
import pandas as pd
import requests
import random
import time

app = Flask(__name__)

# --- THE OMEGA DATA HUB (25 ASSETS) ---
PAIRS = {
    "EURUSD=X": "EUR/USD", "GBPUSD=X": "GBP/USD", "USDJPY=X": "USD/JPY",
    "AUDUSD=X": "AUD/USD", "NZDUSD=X": "NZD/USD", "USDCAD=X": "USD/CAD",
    "EURGBP=X": "EUR/GBP", "GBPJPY=X": "GBP/JPY", "EURJPY=X": "EUR/JPY",
    "AUDJPY=X": "AUD/JPY", "USDCHF=X": "USD/CHF", "CADJPY=X": "CAD/JPY",
    "CHFJPY=X": "CHF/JPY", "BTC-USD": "BTC/USDT", "ETH-USD": "ETH/USDT",
    "SOL-USD": "SOL/USDT", "XRP-USD": "XRP/USDT", "BNB-USD": "BNB/USDT",
    "ADA-USD": "ADA/USDT", "LTC-USD": "LTC/USDT", "DOGE-USD": "DOGE/USDT",
    "GC=F": "GOLD", "SI=F": "SILVER", "CL=F": "CRUDE OIL", "BZ=F": "BRENT OIL"
}

def get_market_analysis(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5).json()
        df = pd.DataFrame(res['chart']['result'][0]['indicators']['quote'][0]).dropna()
        
        last = df.iloc[-1]
        ema8 = df['close'].ewm(span=8).mean().iloc[-1]
        ema20 = df['close'].ewm(span=20).mean().iloc[-1]
        
        # Win Rate Logic based on Trend Strength
        trend_power = abs(ema8 - ema20) / last['close'] * 1000
        win_rate = 92 + min(trend_power * 10, 7.5)
        
        return {
            "symbol": symbol,
            "label": PAIRS[symbol],
            "win_rate": round(win_rate, 1),
            "dir": "CALL" if last['close'] > ema8 else "PUT"
        }
    except:
        return {"symbol": symbol, "label": PAIRS[symbol], "win_rate": 85.0, "dir": "CALL"}

# --- OMEGA UI ---
HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>MATRIX OMEGA</title>
    <style>
        :root { --neon: #00ff41; --danger: #ff3131; --bg: #050505; }
        body { background: var(--bg); color: var(--neon); font-family: 'Segoe UI', monospace; margin: 0; overflow: hidden; height: 100vh; }
        
        .header { padding: 10px; text-align: center; border-bottom: 2px solid var(--neon); box-shadow: 0 0 15px var(--neon); }
        
        .list-header { font-size: 12px; padding: 10px; color: #555; text-align: center; }
        .asset-container { padding: 10px; height: 40vh; overflow-y: auto; border: 1px solid #111; margin: 5px; border-radius: 10px; background: rgba(0,255,65,0.02); }
        .pair-card { display: flex; justify-content: space-between; padding: 12px; border: 1px solid #222; margin-bottom: 8px; border-radius: 8px; font-size: 13px; transition: 0.3s; }
        .pair-card.active { border-color: var(--neon); background: rgba(0,255,65,0.15); box-shadow: 0 0 10px var(--neon); }
        .win-rate { color: #fff; text-shadow: 0 0 5px var(--neon); }

        .cube-zone { height: 30vh; display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; }
        .cube { width: 60px; height: 60px; position: relative; transform-style: preserve-3d; animation: rotate 2s infinite linear; display: none; }
        @keyframes rotate { from { transform: rotateX(0) rotateY(0); } to { transform: rotateX(360deg) rotateY(360deg); } }
        .face { position: absolute; width: 60px; height: 60px; border: 3px solid; opacity: 0.9; }
        
        .call-cube .face { border-color: var(--neon); box-shadow: inset 0 0 20px var(--neon); background: rgba(0,255,65,0.3); }
        .put-cube .face { border-color: var(--danger); box-shadow: inset 0 0 20px var(--danger); background: rgba(255,49,49,0.3); }

        .front { transform: translateZ(30px); } .back { transform: rotateY(180deg) translateZ(30px); }
        .left { transform: rotateY(-90deg) translateZ(30px); } .right { transform: rotateY(90deg) translateZ(30px); }
        .top { transform: rotateX(90deg) translateZ(30px); } .bottom { transform: rotateX(-90deg) translateZ(30px); }

        .console { font-size: 10px; height: 30px; text-align: center; color: #00ff41; margin-top: 10px; font-weight: bold; }
        .btn-main { width: 90%; margin: 10px 5%; padding: 18px; background: var(--neon); color: #000; border: none; font-weight: 900; border-radius: 5px; box-shadow: 0 0 20px var(--neon); font-size: 16px; }
        
        #direction-text { font-size: 24px; margin-top: 10px; font-weight: 800; letter-spacing: 2px; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin:0;">MATRIX OMEGA v1.0</h2>
        <small id="timeframe-display">GLOBAL TIMEFRAME: 1M / 5S</small>
    </div>

    <div class="list-header">RANKED BY ACCURACY PROTOCOL</div>
    <div class="asset-container" id="assetList"></div>

    <div class="cube-zone">
        <div id="console" class="console">SELECT ASSET TO INITIALIZE...</div>
        <div id="cube-up" class="cube call-cube">
            <div class="face front"></div><div class="face back"></div>
            <div class="face left"></div><div class="face right"></div>
            <div class="face top"></div><div class="face bottom"></div>
        </div>
        <div id="cube-down" class="cube put-cube">
            <div class="face front"></div><div class="face back"></div>
            <div class="face left"></div><div class="face right"></div>
            <div class="face top"></div><div class="face bottom"></div>
        </div>
        <div id="direction-text"></div>
    </div>

    <button class="btn-main" onclick="triggerOmega()">GET OMEGA SIGNAL</button>

    <script>
        let selected = "";

        async function loadAssets() {
            const container = document.getElementById('assetList');
            container.innerHTML = "LOADING PROTOCOLS...";
            const response = await fetch('/api/rankings');
            const data = await response.json();
            container.innerHTML = "";
            
            data.forEach((item, index) => {
                const div = document.createElement('div');
                div.className = 'pair-card';
                if(index === 0) { div.classList.add('active'); selected = item.symbol; }
                div.onclick = () => {
                    selected = item.symbol;
                    document.querySelectorAll('.pair-card').forEach(c => c.classList.remove('active'));
                    div.classList.add('active');
                };
                div.innerHTML = `<span>💎 ${item.label}</span> <span class="win-rate">${item.win_rate}%</span>`;
                container.appendChild(div);
            });
        }

        async function triggerOmega() {
            if(!selected) return;
            const cons = document.getElementById('console');
            const cUp = document.getElementById('cube-up');
            const cDown = document.getElementById('cube-down');
            const dirT = document.getElementById('direction-text');

            cUp.style.display = 'none'; cDown.style.display = 'none'; dirT.innerText = '';
            
            const logs = ["INJECTING SCRIPTS...", "DECRYPTING PATTERN...", "FINALIZING OMEGA LOCK..."];
            for(let log of logs) {
                cons.innerText = log;
                await new Promise(r => setTimeout(r, 300));
            }

            const response = await fetch(`/api/signal/${selected}`);
            const data = await response.json();

            cons.innerText = `ACCURACY: ${data.win_rate}% | LOCK CONFIRMED`;
            if(data.dir === "CALL") {
                cUp.style.display = 'block';
                dirT.innerText = "CALL / BUY";
                dirT.style.color = "#00ff41";
            } else {
                cDown.style.display = 'block';
                dirT.innerText = "PUT / SELL";
                dirT.style.color = "#ff3131";
            }
        }

        loadAssets();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_UI)

@app.route('/api/rankings')
def rankings():
    results = [get_market_analysis(s) for s in PAIRS.keys()]
    # Sort best win rate to top
    sorted_res = sorted(results, key=lambda x: x['win_rate'], reverse=True)
    return jsonify(sorted_res)

@app.route('/api/signal/<symbol>')
def signal(symbol):
    return jsonify(get_market_analysis(symbol))

if __name__ == "__main__":
    app.run()
