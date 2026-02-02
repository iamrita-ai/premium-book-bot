from flask import Flask, jsonify, render_template_string
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>📚 Book Bot Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                color: white;
                text-align: center;
            }
            .container {
                max-width: 800px;
                margin: 50px auto;
                padding: 40px;
                background: rgba(255,255,255,0.1);
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            h1 { font-size: 3em; margin-bottom: 20px; }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 40px 0;
            }
            .stat-card {
                background: rgba(255,255,255,0.15);
                padding: 20px;
                border-radius: 15px;
            }
            .stat-value {
                font-size: 2.5em;
                font-weight: bold;
                margin: 10px 0;
            }
            .btn {
                display: inline-block;
                background: white;
                color: #667eea;
                padding: 15px 40px;
                border-radius: 50px;
                text-decoration: none;
                font-weight: bold;
                margin: 20px 10px;
                font-size: 1.1em;
                transition: all 0.3s;
            }
            .btn:hover {
                transform: scale(1.05);
                box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            }
            .telegram-btn { background: #0088cc; color: white; }
            .status {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 10px;
                background: #4CAF50;
                box-shadow: 0 0 10px #4CAF50;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📚 Book Bot</h1>
            <p>Your Digital Library Assistant</p>
            
            <div style="margin: 30px 0;">
                <span class="status"></span>
                <strong>Status: ONLINE & RUNNING</strong>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div>📚 Total Books</div>
                    <div class="stat-value">10,245</div>
                </div>
                <div class="stat-card">
                    <div>👥 Total Users</div>
                    <div class="stat-value">5,892</div>
                </div>
                <div class="stat-card">
                    <div>✅ Success Rate</div>
                    <div class="stat-value">99.2%</div>
                </div>
                <div class="stat-color: white;
                    padding: 15px 40px;
                    border-radius: 50px;
                    text-decoration: none;
                    font-weight: bold;
                    margin: 20px 10px;
                    font-size: 1.1em;
                    transition: all 0.3s;
                }
                .btn:hover {
                    transform: scale(1.05);
                    box-shadow: 0 10px 20px rgba(0,0,0,0.2);
                }
                .telegram-btn { background: #0088cc; color: white; }
                .status {
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    margin-right: 10px;
                    background: #4CAF50;
                    box-shadow: 0 0 10px #4CAF50;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📚 Book Bot</h1>
                <p>Your Digital Library Assistant</p>
                
                <div style="margin: 30px 0;">
                    <span class="status"></span>
                    <strong>Status: ONLINE & RUNNING</strong>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <div>📚 Total Books</div>
                        <div class="stat-value">10,245</div>
                    </div>
                    <div class="stat-card">
                        <div>👥 Total Users</div>
                        <div class="stat-value">5,892</div>
                    </div>
                    <div class="stat-card">
                        <div>✅ Success Rate</div>
                        <div class="stat-value">99.2%</div>
                    </div>
                    <div class="stat-card">
                        <div>⚡ Uptime</div>
                        <div class="stat-value">99.9%</div>
                    </div>
                </div>
                
                <div style="margin: 40px 0;">
                    <a href="https://t.me/{BOT_USERNAME}" class="btn telegram-btn" target="_blank">
                        💬 Open in Telegram
                    </a>
                    <a href="/health" class="btn">
                        🩺 Health Check
                    </a>
                    <a href="/api/stats" class="btn">
                        📊 API Stats
                    </a>
                </div>
                
                <div style="opacity: 0.8; margin-top: 40px;">
                    <p>© 2024 Book Bot | Deployed on Render.com</p>
                    <p>Made with ❤️ for readers worldwide</p>
                </div>
            </div>
        </body>
        </html>
    """
    
    BOT_USERNAME = os.getenv("BOT_USERNAME", "@BookBot").lstrip('@')
    return render_template_string(html, BOT_USERNAME=BOT_USERNAME)

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "telegram-book-bot"
    })

@app.route('/api/stats')
def api_stats():
    return jsonify({
        "bot": "online",
        "version": "2.0.0",
        "features": [
            "auto_delete_searches",
            "reaction_system",
            "broadcast",
            "wishlist",
            "analytics"
        ]
    })

if __name__ == '__main__':
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
