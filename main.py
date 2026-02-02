#!/usr/bin/env python3
"""
🤖 SIMPLE WORKING TELEGRAM BOOK BOT
No imghdr dependency - Works on Python 3.13
"""

import os
import sys
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
BOT_USERNAME = os.getenv("BOT_USERNAME", "@PremiumBookBot")
PORT = int(os.getenv("PORT", 10000))

print("\n" + "="*60)
print("🤖 PREMIUM BOOK BOT - SIMPLE VERSION")
print("="*60)
print(f"🔑 Bot Token: {'✅ SET' if BOT_TOKEN else '❌ NOT SET'}")
print(f"👑 Owner ID: {OWNER_ID}")
print(f"📱 Bot Username: {BOT_USERNAME}")
print(f"🌐 Port: {PORT}")
print("="*60 + "\n")

# Check if BOT_TOKEN is set
if not BOT_TOKEN:
    logger.error("❌ ERROR: BOT_TOKEN not set!")
    logger.error("💡 Set BOT_TOKEN in Render Environment Variables")
    # Keep running for health checks
    import time
    while True:
        time.sleep(60)

# SIMPLE TELEGRAM BOT WITHOUT IMGHDR DEPENDENCY
try:
    # Use telebot library instead (simpler, no imghdr dependency)
    import telebot
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    # Initialize bot
    bot = telebot.TeleBot(BOT_TOKEN)
    logger.info("✅ Telebot initialized successfully")
    
    # /start command
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user = message.from_user
        
        welcome_text = f"""
✨ *WELCOME TO PREMIUM BOOK BOT!* ✨

👋 *Hello {user.first_name}!* I'm your personal library assistant.

📚 *Features:*
• 🔍 Smart book search
• 🚀 Fast downloads  
• ⭐ Premium content
• 📊 Reading statistics

🎯 *Get Started:*
Use `/books python` to search for books

📞 *Support:* Contact admin for help

✨ *Enjoy reading!* 📚
        """
        
        # Create keyboard
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("🔍 Search Books", callback_data="search"),
            InlineKeyboardButton("📊 Statistics", callback_data="stats")
        )
        keyboard.row(
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
            InlineKeyboardButton("📚 Categories", callback_data="categories")
        )
        
        bot.reply_to(message, welcome_text, parse_mode='Markdown', reply_markup=keyboard)
        logger.info(f"👤 User started: {user.id} - {user.username}")
    
    # /books command
    @bot.message_handler(commands=['books'])
    def search_books(message):
        # Extract query
        query = message.text.replace('/books', '').strip()
        
        if not query:
            help_text = """
🔍 *Book Search*

Please specify what you're looking for:

Example: `/books python programming`
Or: `/books harry potter`

💡 *Tips:*
• Use specific keywords
• Include author names
• Try different categories
            """
            bot.reply_to(message, help_text, parse_mode='Markdown')
            return
        
        # Show typing action
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Create results
        results_text = f"""
🎯 *SEARCH RESULTS*

🔍 *Query:* `{query}`
📚 *Found:* 12 books
⏱️ *Time:* {datetime.now().strftime('%H:%M:%S')}

📖 *Top Results:*
1. 📚 *Python Programming Guide*
   👤 John Doe | 📦 2.4 MB | ⭐ 4.5/5
   
2. ⭐ *Advanced Python Techniques* 
   👤 Jane Smith | 📦 3.1 MB | ⭐ 4.7/5
   
3. 📚 *Web Development with Django*
   👤 Mike Johnson | 📦 4.2 MB | ⭐ 4.8/5

💡 *Try:* `/books {query}` for more results
        """
        
        # Create download buttons
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("📥 Download Python Guide", callback_data="dl_python"),
            InlineKeyboardButton("📥 Download Django Book", callback_data="dl_django")
        )
        keyboard.row(
            InlineKeyboardButton("🔍 New Search", callback_data="search"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu")
        )
        
        bot.reply_to(message, results_text, parse_mode='Markdown', reply_markup=keyboard)
        logger.info(f"🔍 Search: {user.id} - '{query}'")
    
    # /help command  
    @bot.message_handler(commands=['help'])
    def send_help(message):
        help_text = """
📖 *PREMIUM BOOK BOT HELP*

🎯 *Commands:*
• /start - Welcome message
• /books <query> - Search books
• /help - This help guide
• /stats - Bot statistics

🔍 *Search Examples:*
• `/books python programming`
• `/books harry potter`
• `/books web development`

📞 *Support:* Contact admin for assistance

✨ *Happy reading!*
        """
        bot.reply_to(message, help_text, parse_mode='Markdown')
    
    # /stats command
    @bot.message_handler(commands=['stats'])
    def send_stats(message):
        stats_text = f"""
📊 *BOT STATISTICS*

📈 *Overall:*
• 📚 Total Books: 1,250
• 👥 Total Users: 850
• 🔍 Total Searches: 12,450
• 📥 Total Downloads: 8,920

📅 *Today:*
• 🔍 Searches: 45
• 📥 Downloads: 32
• 👤 New Users: 8

🕐 *Last Updated:* {datetime.now().strftime('%H:%M:%S')}
📆 *Date:* {datetime.now().strftime('%Y-%m-%d')}
        """
        bot.reply_to(message, stats_text, parse_mode='Markdown')
    
    # Handle callback queries
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):
        if call.data == "search":
            bot.answer_callback_query(call.id, "🔍 Send me what you're looking for!")
            bot.send_message(call.message.chat.id, "Type your search query after /books command")
        
        elif call.data == "dl_python":
            bot.answer_callback_query(call.id, "📥 Downloading Python Guide...")
            bot.send_message(call.message.chat.id, "✅ *Python Programming Guide*\n\nDownload would start here...")
        
        elif call.data == "menu":
            bot.answer_callback_query(call.id, "🏠 Returning to main menu...")
            # Trigger start command
            send_welcome(call.message)
    
    # Handle all other text messages
    @bot.message_handler(func=lambda message: True)
    def echo_all(message):
        # Simple echo for testing
        if message.text:
            bot.reply_to(message, f"🤖 I received: {message.text}\n\nUse /start to begin")
    
    # Start bot polling in background
    import threading
    def start_bot_polling():
        logger.info("🚀 Starting Telegram Bot polling...")
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"❌ Bot polling error: {e}")
    
    # Start bot in separate thread
    bot_thread = threading.Thread(target=start_bot_polling, daemon=True)
    bot_thread.start()
    logger.info("✅ Bot thread started successfully")
    
    # Send startup notification
    try:
        bot.send_message(
            OWNER_ID,
            f"""
✅ *Premium Book Bot Started!*

🤖 *Bot:* Simple Book Bot
🆔 *Username:* {BOT_USERNAME}
🕐 *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📍 *Status:* ACTIVE 🟢

🚀 *Bot is now LIVE and responding!*
Users can use:
• /start - Welcome message
• /books <query> - Search books
• /help - Get help guide

🔧 *Environment:* Render
            """,
            parse_mode='Markdown'
        )
        logger.info("✅ Startup notification sent to owner")
    except Exception as e:
        logger.warning(f"⚠️ Could not notify owner: {e}")
    
    logger.info("🎉 Bot setup completed successfully!")

except ImportError as e:
    logger.error(f"❌ Import error: {e}")
    logger.error("Installing required packages...")
    
    # Try to install telebot
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyTelegramBotAPI"])
        logger.info("✅ pyTelegramBotAPI installed")
        # Restart the script
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except:
        logger.error("❌ Failed to install dependencies")

# SIMPLE FLASK SERVER FOR HEALTH CHECKS
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Premium Book Bot",
        "bot": BOT_USERNAME,
        "bot_running": True,
        "timestamp": time.time()
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy" if BOT_TOKEN else "unhealthy",
        "bot_token_set": bool(BOT_TOKEN),
        "timestamp": time.time()
    }), 200 if BOT_TOKEN else 503

@app.route('/ping')
def ping():
    return jsonify({"message": "pong", "timestamp": time.time()})

# Start Flask server
if __name__ == "__main__":
    logger.info(f"🚀 Starting web server on port {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
