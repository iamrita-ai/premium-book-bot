from flask import Flask, jsonify, render_template_string
import os
import time

app = Flask(__name__)
start_time = time.time()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>📚 Premium Book Bot</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            max-width: 800px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
        }
        h1 {
            font-size: 3em;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }
        .status {
            display: inline-block;
            padding: 10px 30px;
            border-radius: 50px;
            font-weight: bold;
            margin: 20px 0;
            font-size: 1.2em;
            background: #10B981;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 30px 0;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.15);
            padding: 20px;
            border-radius: 15px;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .endpoints {
            margin: 30px 0;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
        }
        .endpoint {
            margin: 10px 0;
            padding: 10px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
        }
        a {
            color: #93c5fd;
            text-decoration: none;
            font-weight: bold;
        }
        .footer {
            margin-top: 30px;
            opacity: 0.8;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Premium Book Bot</h1>
        <p>Telegram Book Distribution System</p>
        
        <div class="status">✅ SYSTEM STATUS: OPERATIONAL</div>
        
        <div class="stats">
            <div class="stat-card">
                <div>Uptime</div>
                <div class="stat-value">{{ uptime }}</div>
            </div>
            <div class="stat-card">
                <div>Bot Status</div>
                <div class="stat-value">{{ '🟢' if bot_online else '🔴' }}</div>
            </div>
            <div class="stat-card">
                <div>Port</div>
                <div class="stat-value">{{ port }}</div>
            </div>
        </div>
        
        <div class="endpoints">
            <h3>🔗 Available Endpoints</h3>
            <div class="endpoint"><a href="/health">/health</a> - Health check</div>
            <div class="endpoint"><a href="/ping">/ping</a> - Ping test</div>
            <div class="endpoint"><a href="/stats">/stats</a> - Bot statistics</div>
        </div>
        
        <div class="footer">
            <p>📚 Premium Book Bot v2.0.0 | Powered by Render</p>
            <p>🕐 {{ current_time }}</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    from datetime import datetime
    
    uptime_seconds = int(time.time() - start_time)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    uptime_str = f"{hours}h {minutes}m {seconds}s"
    
    bot_online = bool(os.getenv("BOT_TOKEN"))
    
    return render_template_string(
        HTML_TEMPLATE,
        uptime=uptime_str,
        bot_online=bot_online,
        port=os.getenv("PORT", 10000),
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

@app.route('/health')
def health():
    bot_token = os.getenv("BOT_TOKEN")
    status = "healthy" if bot_token else "unhealthy"
    code = 200 if bot_token else 503
    
    return jsonify({
        "status": status,
        "service": "premium-book-bot",
        "version": "2.0.0",
        "timestamp": time.time(),
        "bot_configured": bool(bot_token),
        "uptime": int(time.time() - start_time)
    }), code

@app.route('/ping')
def ping():
    return jsonify({"message": "pong", "timestamp": time.time()})

@app.route('/stats')
def stats():
    return jsonify({
        "bot": {
            "name": "Premium Book Bot",
            "version": "2.0.0",
            "status": "running",
            "bot_token_set": bool(os.getenv("BOT_TOKEN"))
        },
        "system": {
            "uptime": int(time.time() - start_time),
            "port": os.getenv("PORT", 10000)
        }
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"🚀 Premium Book Bot Web Server")
    print(f"🌐 http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
