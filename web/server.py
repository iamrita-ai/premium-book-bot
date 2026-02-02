#!/usr/bin/env python3
"""
Web server for health checks and monitoring
"""

from flask import Flask, jsonify, render_template_string
import logging
from threading import Thread
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

app = Flask(__name__)
config = Config()

# HTML template for status page
STATUS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>📚 Premium Book Bot Status</title>
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
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }
        .status-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 50px;
            font-weight: bold;
            margin: 20px 0;
            font-size: 1.2em;
        }
        .status-up { background: #10B981; }
        .status-down { background: #EF4444; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.15);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            transition: transform 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.2);
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }
        .stat-label {
            opacity: 0.9;
            font-size: 0.9em;
        }
        .info-section {
            margin: 40px 0;
            padding: 30px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
        }
        .info-item {
            margin: 15px 0;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            justify-content: space-between;
        }
        .endpoints {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 30px 0;
        }
        .endpoint {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .endpoint a {
            color: #93c5fd;
            text-decoration: none;
            font-weight: bold;
        }
        .endpoint a:hover {
            text-decoration: underline;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            opacity: 0.8;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Premium Book Bot</h1>
            <p>Telegram Book Distribution System</p>
            
            <div class="status-badge status-up">
                ✅ SYSTEM STATUS: OPERATIONAL
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Bot Status</div>
                <div class="stat-value">{{ '🟢' if bot_online else '🔴' }}</div>
                <div class="stat-label">{{ 'Online' if bot_online else 'Offline' }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">Uptime</div>
                <div class="stat-value">{{ uptime }}</div>
                <div class="stat-label">Since Start</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">Memory</div>
                <div class="stat-value">{{ memory_usage }}%</div>
                <div class="stat-label">Usage</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">Port</div>
                <div class="stat-value">{{ port }}</div>
                <div class="stat-label">HTTP Server</div>
            </div>
        </div>
        
        <div class="info-section">
            <h2>📊 System Information</h2>
            <div class="info-item">
                <span>Bot Token Configured:</span>
                <span>{{ '✅ Yes' if bot_token else '❌ No' }}</span>
            </div>
            <div class="info-item">
                <span>Database Path:</span>
                <span>{{ db_path }}</span>
            </div>
            <div class="info-item">
                <span>Owner ID:</span>
                <span>{{ owner_id }}</span>
            </div>
            <div class="info-item">
                <span>Server Time:</span>
                <span>{{ current_time }}</span>
            </div>
        </div>
        
        <h2>🔗 Available Endpoints</h2>
        <div class="endpoints">
            <div class="endpoint">
                <a href="/health">/health</a>
                <p>Health check endpoint</p>
            </div>
            <div class="endpoint">
                <a href="/stats">/stats</a>
                <p>Bot statistics</p>
            </div>
            <div class="endpoint">
                <a href="/ping">/ping</a>
                <p>Simple ping response</p>
            </div>
            <div class="endpoint">
                <a href="/config">/config</a>
                <p>Configuration info</p>
            </div>
        </div>
        
        <div class="footer">
            <p>📚 Premium Book Bot v1.0.0 | Powered by Render</p>
            <p>Last updated: {{ current_time }}</p>
        </div>
    </div>
</body>
</html>
"""

# Store startup time for uptime calculation
import time
startup_time = time.time()

def get_uptime():
    """Calculate uptime in human readable format"""
    uptime_seconds = int(time.time() - startup_time)
    
    days = uptime_seconds // (24 * 3600)
    uptime_seconds %= (24 * 3600)
    hours = uptime_seconds // 3600
    uptime_seconds %= 3600
    minutes = uptime_seconds // 60
    seconds = uptime_seconds % 60
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def get_memory_usage():
    """Get memory usage percentage"""
    try:
        import psutil
        return round(psutil.virtual_memory().percent, 1)
    except:
        return "N/A"

@app.route('/')
def index():
    """Main status page"""
    from datetime import datetime
    
    return render_template_string(STATUS_TEMPLATE, {
        'bot_online': bool(config.BOT_TOKEN),
        'uptime': get_uptime(),
        'memory_usage': get_memory_usage(),
        'port': config.PORT,
        'bot_token': bool(config.BOT_TOKEN),
        'db_path': config.DB_PATH,
        'owner_id': config.OWNER_ID if config.OWNER_ID else "Not set",
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    health_status = {
        "status": "healthy" if config.BOT_TOKEN else "unhealthy",
        "timestamp": time.time(),
        "service": "telegram-book-bot",
        "version": "1.0.0",
        "bot_token_configured": bool(config.BOT_TOKEN),
        "uptime": get_uptime()
    }
    
    status_code = 200 if config.BOT_TOKEN else 503
    return jsonify(health_status), status_code

@app.route('/stats')
def stats():
    """Bot statistics endpoint"""
    stats_data = {
        "bot": {
            "username": config.BOT_USERNAME or "Not set",
            "owner_id": config.OWNER_ID,
            "locked": config.BOT_LOCKED,
            "dm_enabled": config.DM_ENABLED
        },
        "system": {
            "uptime": get_uptime(),
            "memory_usage": get_memory_usage(),
            "port": config.PORT
        },
        "channels": {
            "database_channel": config.DATABASE_CHANNEL_ID if config.DATABASE_CHANNEL_ID else "Not set",
            "log_channel": config.LOG_CHANNEL_ID if config.LOG_CHANNEL_ID else "Not set",
            "request_group": config.REQUEST_GROUP_ID or "Not set"
        }
    }
    return jsonify(stats_data)

@app.route('/ping')
def ping():
    """Simple ping endpoint"""
    return jsonify({
        "message": "pong",
        "timestamp": time.time()
    })

@app.route('/config')
def config_info():
    """Configuration info (safe version)"""
    safe_config = {
        "bot_username": config.BOT_USERNAME or "Not set",
        "owner_id": config.OWNER_ID,
        "database_channel_set": bool(config.DATABASE_CHANNEL_ID),
        "log_channel_set": bool(config.LOG_CHANNEL_ID),
        "force_sub_channel": config.FORCE_SUB_CHANNEL or "Not set",
        "bot_locked": config.BOT_LOCKED,
        "dm_enabled": config.DM_ENABLED,
        "maintenance": config.MAINTENANCE,
        "port": config.PORT,
        "host": config.HOST
    }
    return jsonify(safe_config)

def start_server():
    """Start the Flask server"""
    port = config.PORT
    host = config.HOST
    
    logging.info(f"🌐 Starting web server on {host}:{port}")
    
    # Run without reloader in production
    app.run(host=host, port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    start_server()
