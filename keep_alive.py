from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return '''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flux Bot</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background: #0d0d1a;
            color: #fff;
            font-family: 'Segoe UI', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }

        .bg {
            position: fixed;
            inset: 0;
            background: radial-gradient(ellipse at 20% 50%, #1a0a3a 0%, transparent 60%),
                        radial-gradient(ellipse at 80% 20%, #0a1a3a 0%, transparent 60%),
                        radial-gradient(ellipse at 60% 80%, #1a1a0a 0%, transparent 60%);
        }

        .stars {
            position: fixed;
            inset: 0;
            pointer-events: none;
        }

        .star {
            position: absolute;
            width: 2px;
            height: 2px;
            background: white;
            border-radius: 50%;
            animation: twinkle var(--d) ease-in-out infinite;
            opacity: 0;
        }

        @keyframes twinkle {
            0%, 100% { opacity: 0; }
            50% { opacity: var(--o); }
        }

        .card {
            position: relative;
            z-index: 1;
            text-align: center;
            padding: 60px 80px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 24px;
            backdrop-filter: blur(20px);
            box-shadow: 0 0 80px rgba(88, 101, 242, 0.15);
            max-width: 500px;
            width: 90%;
        }

        .logo {
            width: 90px;
            height: 90px;
            background: linear-gradient(135deg, #5865f2, #9b59b6);
            border-radius: 50%;
            margin: 0 auto 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 40px;
            box-shadow: 0 0 40px rgba(88,101,242,0.5);
            animation: pulse 3s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 40px rgba(88,101,242,0.5); }
            50% { box-shadow: 0 0 70px rgba(88,101,242,0.8); }
        }

        h1 {
            font-size: 2.4rem;
            font-weight: 700;
            background: linear-gradient(135deg, #fff, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
            letter-spacing: -0.5px;
        }

        .tagline {
            color: rgba(255,255,255,0.5);
            font-size: 0.95rem;
            margin-bottom: 36px;
        }

        .status {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: rgba(87, 242, 135, 0.1);
            border: 1px solid rgba(87, 242, 135, 0.25);
            padding: 10px 22px;
            border-radius: 100px;
            font-size: 0.9rem;
            color: #57f287;
            margin-bottom: 40px;
            font-weight: 500;
        }

        .dot {
            width: 8px;
            height: 8px;
            background: #57f287;
            border-radius: 50%;
            animation: blink 1.5s ease-in-out infinite;
        }

        @keyframes blink {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.7); }
        }

        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 16px;
            margin-bottom: 36px;
        }

        .stat {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 14px;
            padding: 16px 10px;
        }

        .stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #a78bfa;
            margin-bottom: 4px;
        }

        .stat-label {
            font-size: 0.72rem;
            color: rgba(255,255,255,0.4);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .features {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: center;
        }

        .badge {
            background: rgba(88,101,242,0.15);
            border: 1px solid rgba(88,101,242,0.3);
            color: #a5b4fc;
            padding: 6px 14px;
            border-radius: 100px;
            font-size: 0.8rem;
        }

        .footer {
            margin-top: 36px;
            font-size: 0.78rem;
            color: rgba(255,255,255,0.25);
        }
    </style>
</head>
<body>
    <div class="bg"></div>
    <div class="stars" id="stars"></div>

    <div class="card">
        <div class="logo">⚡</div>
        <h1>Flux Bot</h1>
        <p class="tagline">Discord Moderasyon & Eğlence Botu</p>

        <div class="status">
            <div class="dot"></div>
            Çevrimiçi & Aktif
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">!yardım</div>
                <div class="stat-label">Komut Prefix</div>
            </div>
            <div class="stat">
                <div class="stat-value">10+</div>
                <div class="stat-label">Komut</div>
            </div>
            <div class="stat">
                <div class="stat-value">24/7</div>
                <div class="stat-label">Uptime</div>
            </div>
        </div>

        <div class="features">
            <span class="badge">🛡️ Moderasyon</span>
            <span class="badge">🎫 Destek Sistemi</span>
            <span class="badge">⭐ Seviye Sistemi</span>
            <span class="badge">🎮 Eğlence</span>
            <span class="badge">⚙️ Otorol</span>
        </div>

        <p class="footer">Flux Bot &copy; 2025 — Tüm hakları saklıdır.</p>
    </div>

    <script>
        const stars = document.getElementById('stars');
        for (let i = 0; i < 120; i++) {
            const s = document.createElement('div');
            s.className = 'star';
            s.style.cssText = `
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
                --d: ${2 + Math.random() * 4}s;
                --o: ${0.3 + Math.random() * 0.7};
                animation-delay: ${Math.random() * 4}s;
            `;
            stars.appendChild(s);
        }
    </script>
</body>
</html>'''

def run():
    app.run(host='0.0.0.0', port=3000)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
