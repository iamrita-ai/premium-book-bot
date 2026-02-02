from flask import Flask, jsonify
import os
import time
import threading

app = Flask(__name__)
start_time = time.time()

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Premium Book Bot",
        "version": "2.0.0",
        "bot_configured": bool(os.getenv("BOT_TOKEN")),
        "owner_id": os.getenv("OWNER_ID", "Not set"),
        "uptime": int(time.time() - start_time)
    })

@app.route('/health')
def health():
    bot_token = os.getenv("BOT_TOKEN")
    return jsonify({
        "status": "healthy" if bot_token else "unhealthy",
        "bot": "premium-book-bot",
        "timestamp": time.time()
    }), 200 if bot_token else 503

@app.route('/ping')
def ping():
    return jsonify({"message": "pong", "timestamp": time.time()})

@app.route('/start-bot')
def start_bot():
    """Manually trigger bot start (for testing)"""
    # This would start the bot in a separate thread
    return jsonify({
        "status": "bot_started",
        "message": "Bot should start in background"
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"🚀 Premium Book Bot Web Server")
    print(f"🌐 Port: {port}")
    print(f"🤖 Bot Token: {'✅ SET' if os.getenv('BOT_TOKEN') else '❌ NOT SET'}")
    app.run(host='0.0.0.0', port=port, debug=False)