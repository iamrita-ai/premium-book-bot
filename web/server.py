#!/usr/bin/env python3
"""
ALL-IN-ONE: Web Server + Telegram Bot in one file
"""

import os
import time
import asyncio
import threading
from flask import Flask, jsonify, render_template_string
from telegram.ext import Application, CommandHandler
import logging

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__)
start_time = time.time()

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🤖 Premium Book Bot</title>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            padding: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            max-width: 800px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 25px;
            padding: 50px;
            box-shadow: 0 25px 75px rgba(0,0,0,0.3);
            text-align: center;
        }
        h1 {
            font-size: 3.5em;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
        }
        .bot-status {
            display: inline-block;
            padding: 12px 35px;
            border-radius: 50px;
            font-weight: bold;
            margin: 25px 0;
            font-size: 1.3em;
            background: #10B981;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin: 35px 0;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.15);
            padding: 25px;
            border-radius: 20px;
            transition: all 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.25);
        }
        .stat-value {
            font-size: 2.8em;
            font-weight: bold;
            margin: 15px 0;
        }
        .bot-info {
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 20px;
            margin: 30px 0;
            text-align: left;
        }
        .info-item {
            margin: 15px 0;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            display: flex;
            justify-content: space-between;
            font-size: 1.1em;
        }
        .endpoints {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 30px 0;
        }
        .endpoint {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            transition: all 0.3s;
        }
        .endpoint:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        a {
            color: #93c5fd;
            text-decoration: none;
            font-weight: bold;
            font-size: 1.1em;
        }
        .footer {
            margin-top: 40px;
            opacity: 0.9;
            font-size: 0.95em;
        }
        .telegram-btn {
            display: inline-block;
            background: #0088cc;
            color: white;
            padding: 15px 30px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: bold;
            margin: 20px 0;
            font-size: 1.2em;
            transition: all 0.3s;
        }
        .telegram-btn:hover {
            background: #0077b5;
            transform: scale(1.05);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Premium Book Bot</h1>
        <p style="font-size: 1.3em; opacity: 0.9;">Telegram Book Distribution System</p>
        
        <div class="bot-status">
            ✅ BOT STATUS: {{ 'ACTIVE 🟢' if bot_running else 'INACTIVE 🔴' }}
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div style="font-size: 1.1em;">Uptime</div>
                <div class="stat-value">{{ uptime }}</div>
                <div>Since startup</div>
            </div>
            <div class="stat-card">
                <div style="font-size: 1.1em;">Bot Token</div>
                <div class="stat-value">{{ '✅' if has_token else '❌' }}</div>
                <div>Configured</div>
            </div>
            <div class="stat-card">
                <div style="font-size: 1.1em;">Server Port</div>
                <div class="stat-value">{{ port }}</div>
                <div>HTTP Server</div>
            </div>
            <div class="stat-card">
                <div style="font-size: 1.1em;">Requests</div>
                <div class="stat-value">{{ request_count }}</div>
                <div>Total served</div>
            </div>
        </div>
        
        <div class="bot-info">
            <h3 style="margin-bottom: 20px; text-align: center;">📊 Bot Information</h3>
            <div class="info-item">
                <span>🤖 Bot Name:</span>
                <span>Premium Book Bot</span>
            </div>
            <div class="info-item">
                <span>🔧 Version:</span>
                <span>2.0.0</span>
            </div>
            <div class="info-item">
                <span>🔄 Last Update:</span>
                <span>{{ current_time }}</span>
            </div>
            <div class="info-item">
                <span>📁 Database:</span>
                <span>/tmp/book_bot.db</span>
            </div>
            <div class="info-item">
                <span>👑 Owner ID:</span>
                <span>{{ owner_id if owner_id else 'Not set' }}</span>
            </div>
        </div>
        
        <a href="https://t.me/{{ bot_username }}" class="telegram-btn" target="_blank">
            💬 Start Chatting with Bot
        </a>
        
        <div class="endpoints">
            <div class="endpoint">
                <a href="/health">/health</a>
                <p style="margin-top: 10px; opacity: 0.8;">Health check endpoint</p>
            </div>
            <div class="endpoint">
                <a href="/ping">/ping</a>
                <p style="margin-top: 10px; opacity: 0.8;">Ping test</p>
            </div>
            <div class="endpoint">
                <a href="/bot-status">/bot-status</a>
                <p style="margin-top: 10px; opacity: 0.8;">Bot status</p>
            </div>
            <div class="endpoint">
                <a href="/start-bot">/start-bot</a>
                <p style="margin-top: 10px; opacity: 0.8;">Start bot manually</p>
            </div>
        </div>
        
        <div class="footer">
            <p>🚀 Powered by Render | ⚡ Premium Book Bot v2.0.0</p>
            <p style="margin-top: 10px;">🕐 {{ current_time }} | 📍 Server is running</p>
        </div>
    </div>
</body>
</html>
"""

# Global variables
bot_app = None
bot_running = False
request_count = 0
bot_username = os.getenv("BOT_USERNAME", "@PremiumBookBot")

# Flask Routes
@app.route('/')
def home():
    global request_count
    request_count += 1
    
    from datetime import datetime
    
    # Calculate uptime
    uptime_seconds = int(time.time() - start_time)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    
    if hours > 0:
        uptime_str = f"{hours}h {minutes}m"
    elif minutes > 0:
        uptime_str = f"{minutes}m {seconds}s"
    else:
        uptime_str = f"{seconds}s"
    
    return render_template_string(
        HTML_TEMPLATE,
        bot_running=bot_running,
        uptime=uptime_str,
        has_token=bool(os.getenv("BOT_TOKEN")),
        port=os.getenv("PORT", 10000),
        request_count=request_count,
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        owner_id=os.getenv("OWNER_ID", ""),
        bot_username=bot_username.lstrip('@')
    )

@app.route('/health')
def health():
    bot_token = os.getenv("BOT_TOKEN")
    status = "healthy" if bot_token else "unhealthy"
    code = 200 if bot_token else 503
    
    return jsonify({
        "status": status,
        "bot": "premium-book-bot",
        "version": "2.0.0",
        "bot_running": bot_running,
        "bot_token_configured": bool(bot_token),
        "web_server": "running",
        "uptime": int(time.time() - start_time),
        "timestamp": time.time()
    }), code

@app.route('/ping')
def ping():
    return jsonify({
        "message": "pong",
        "bot_status": "running" if bot_running else "stopped",
        "timestamp": time.time()
    })

@app.route('/bot-status')
def bot_status():
    return jsonify({
        "telegram_bot": {
            "running": bot_running,
            "username": bot_username,
            "configured": bool(os.getenv("BOT_TOKEN"))
        },
        "web_server": {
            "running": True,
            "port": os.getenv("PORT", 10000),
            "uptime": int(time.time() - start_time)
        }
    })

@app.route('/start-bot')
def start_bot_manual():
    """Manually start the bot"""
    global bot_running
    
    if bot_running:
        return jsonify({
            "status": "already_running",
            "message": "Bot is already running"
        })
    
    # Start bot in background thread
    bot_thread = threading.Thread(target=start_telegram_bot, daemon=True)
    bot_thread.start()
    
    return jsonify({
        "status": "starting",
        "message": "Bot is starting in background...",
        "check_after": "30 seconds"
    })

# Telegram Bot Functions
async def start_command(update, context):
    """Handle /start command"""
    user = update.effective_user
    
    welcome_text = f"""
✨ *WELCOME TO PREMIUM BOOK BOT!* ✨

👋 *Hello {user.first_name}!* I'm your personal library assistant.

📚 *What I Offer:*
• 🔍 Smart book search
• 🚀 Instant downloads
• ⭐ Premium content
• 📊 Reading statistics

🎯 *Get Started:*
1. Use `/books python` to search
2. Browse `/categories`
3. Check `/stats`

💡 *Example:* `/books harry potter`

📞 *Support:* Contact the admin for help.

Enjoy reading! 📖
    """
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    # Log user
    logger.info(f"👤 User started: {user.id} - {user.username}")

async def help_command(update, context):
    """Handle /help command"""
    help_text = """
📖 *PREMIUM BOOK BOT HELP*

🎯 *Commands:*
• /start - Welcome message
• /books <query> - Search books
• /help - This help
• /stats - Bot statistics
• /categories - Browse categories

🔍 *Search Examples:*
• `/books python programming`
• `/books harry potter`
• `/books self help`

👑 *Admin Commands:*
• /addbook - Add new book
• /broadcast - Send announcement

📞 *Support:* Contact admin for help.
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def books_command(update, context):
    """Handle /books command"""
    if not context.args:
        await update.message.reply_text(
            "🔍 *Book Search*\n\n"
            "Please specify what you're looking for:\n"
            "Example: `/books python programming`\n"
            "Or: `/books harry potter`",
            parse_mode='Markdown'
        )
        return
    
    query = " ".join(context.args)
    
    # Show searching animation
    searching_msg = await update.message.reply_text(
        f"🔍 *Searching for:* `{query}`\n\n"
        f"{'▰' * 15}",
        parse_mode='Markdown'
    )
    
    # Simulate search
    await asyncio.sleep(1)
    
    # Mock results
    results_text = f"""
🎯 *SEARCH RESULTS*

🔍 *Query:* `{query}`
📚 *Found:* 15 books
⏱️ *Time:* 1.2 seconds

📖 *Top Results:*
1. 📚 *Python Programming Guide*
   👤 John Doe | 📦 2.4 MB
   
2. ⭐ *Advanced Python Techniques*
   👤 Jane Smith | 📦 3.1 MB
   
3. 📚 *Python for Beginners*
   👤 Mike Johnson | 📦 1.8 MB

💡 *Tip:* Use specific keywords for better results.
    """
    
    await searching_msg.edit_text(results_text, parse_mode='Markdown')

async def stats_command(update, context):
    """Handle /stats command"""
    stats_text = f"""
📊 *BOT STATISTICS*

📚 *Database:*
• Total Books: 1,250
• Available: 1,200
• Premium: 150

👥 *Users:*
• Total Users: 850
• Active Today: 45
• Total Searches: 12,450

🚀 *Performance:*
• Uptime: 24 hours
• Response Time: < 1s
• Success Rate: 99.8%

🕐 *Last Updated:* {time.strftime('%H:%M:%S')}
    """
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def categories_command(update, context):
    """Handle /categories command"""
    categories_text = """
🏷️ *BOOK CATEGORIES*

📚 *Fiction:*
• Romance 💖
• Mystery 🕵️
• Sci-Fi 🚀
• Fantasy 🧙

🔬 *Non-Fiction:*
• Science 🔭
• Technology 💻
• Business 💼
• Health 🏥

🎨 *Creative:*
• Arts 🎨
• Photography 📷
• Music 🎵
• Writing ✍️

📖 *Education:*
• Programming 💻
• Mathematics ➗
• Languages 🗣️
• History 📜

🔍 *Browse:* Use `/books <category>` to explore.
    """
    
    await update.message.reply_text(categories_text, parse_mode='Markdown')

async def start_telegram_bot_task():
    """Start the Telegram bot"""
    global bot_app, bot_running
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("❌ BOT_TOKEN not found in environment!")
        logger.error("💡 Please set BOT_TOKEN in Render Environment Variables")
        return
    
    try:
        logger.info("🚀 Starting Telegram Bot...")
        
        # Create application
        bot_app = Application.builder().token(bot_token).build()
        
        # Add handlers
        bot_app.add_handler(CommandHandler("start", start_command))
        bot_app.add_handler(CommandHandler("help", help_command))
        bot_app.add_handler(CommandHandler("books", books_command))
        bot_app.add_handler(CommandHandler("search", books_command))
        bot_app.add_handler(CommandHandler("stats", stats_command))
        bot_app.add_handler(CommandHandler("categories", categories_command))
        
        # Start bot
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling()
        
        bot_running = True
        logger.info("✅ Telegram Bot started successfully!")
        logger.info(f"🤖 Bot username: {bot_username}")
        
        # Send startup notification to owner
        owner_id = os.getenv("OWNER_ID")
        if owner_id:
            try:
                await bot_app.bot.send_message(
                    chat_id=int(owner_id),
                    text=f"""
✅ *Bot Started Successfully!*

🤖 *Bot:* Premium Book Bot
🆔 *Username:* {bot_username}
🕐 *Time:* {time.strftime('%Y-%m-%d %H:%M:%S')}
📍 *Status:* ACTIVE 🟢
🌐 *Server:* Running on Render

🎯 *Bot is now LIVE and responding to commands!*
📚 Users can start searching with `/books`
                    """,
                    parse_mode='Markdown'
                )
                logger.info("✅ Startup notification sent to owner")
            except Exception as e:
                logger.warning(f"⚠️ Could not notify owner: {e}")
        
        # Keep bot running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ Bot failed to start: {e}")
        bot_running = False

def start_telegram_bot():
    """Start bot in a separate thread"""
    try:
        asyncio.run(start_telegram_bot_task())
    except Exception as e:
        logger.error(f"❌ Bot thread error: {e}")

# Start bot automatically when server starts
def start_bot_in_background():
    """Start bot in background thread"""
    bot_token = os.getenv("BOT_TOKEN")
    if bot_token:
        logger.info("🔄 Starting Telegram Bot in background...")
        bot_thread = threading.Thread(target=start_telegram_bot, daemon=True)
        bot_thread.start()
    else:
        logger.warning("⚠️ BOT_TOKEN not set. Bot will not start.")

# Main function
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 PREMIUM BOOK BOT - ALL IN ONE")
    print("="*60)
    print(f"🌐 Web Server: http://0.0.0.0:{os.getenv('PORT', 10000)}")
    print(f"🤖 Bot Token: {'✅ SET' if os.getenv('BOT_TOKEN') else '❌ NOT SET'}")
    print(f"👑 Owner ID: {os.getenv('OWNER_ID', 'Not set')}")
    print(f"📚 Bot Username: {bot_username}")
    print("="*60 + "\n")
    
    # Start bot in background
    start_bot_in_background()
    
    # Start Flask server
    port = int(os.getenv("PORT", 10000))
    print(f"🚀 Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
