#!/usr/bin/env python3
"""
🤖 PREMIUM BOOK BOT - UPDATED FOR PTB 21.x
"""

import os
import sys
import asyncio
import logging
import time
import threading
from datetime import datetime
from flask import Flask, jsonify

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__)
start_time = time.time()

# CONFIG
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "@Admin")
BOT_USERNAME = os.getenv("BOT_USERNAME", "@PremiumBookBot")
PORT = int(os.getenv("PORT", 10000))

# EMOJIS
EMOJIS = {
    "book": "📚", "search": "🔍", "download": "📥", "star": "⭐",
    "fire": "🔥", "heart": "❤️", "rocket": "🚀", "crown": "👑",
    "trophy": "🏆", "gem": "💎", "sparkle": "✨", "check": "✅",
    "warning": "⚠️", "error": "❌", "info": "ℹ️", "lock": "🔒",
    "unlock": "🔓", "user": "👤", "time": "🕐", "stats": "📊",
    "home": "🏠", "back": "🔙", "next": "➡️", "prev": "⬅️"
}

def get_emoji(key):
    return EMOJIS.get(key, "📚")

# SIMPLE DATABASE
class Database:
    def __init__(self):
        self.db_path = "/tmp/book_bot.db"
    
    def initialize(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                author TEXT,
                file_id TEXT,
                category TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized")
    
    def get_stats(self):
        return {'total_books': 3, 'total_users': 1}

# TELEGRAM BOT - UPDATED FOR PTB 21.x
async def start_telegram_bot():
    """Start Telegram bot with PTB 21.x"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set!")
        return
    
    try:
        logger.info("🚀 Starting Telegram Bot (PTB 21.x)...")
        
        # Import telegram with PTB 21.x
        from telegram import Update
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # /start command
        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user = update.effective_user
            
            welcome_text = f"""
{get_emoji('crown')} *WELCOME TO PREMIUM BOOK BOT!* {get_emoji('crown')}

👋 *Hello {user.first_name}!* I'm your personal library assistant.

📚 *Features:*
• 🔍 Smart book search
• 🚀 Fast downloads
• ⭐ Premium content
• 📊 Reading statistics

🎯 *Get Started:*
Use `/books python` to search for books

📞 *Support:* {OWNER_USERNAME}
            """
            
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = [
                [
                    InlineKeyboardButton(f"{get_emoji('search')} Search", callback_data="search"),
                    InlineKeyboardButton(f"{get_emoji('stats')} Stats", callback_data="stats")
                ],
                [
                    InlineKeyboardButton(f"{get_emoji('info')} Help", callback_data="help")
                ]
            ]
            
            await update.message.reply_text(
                welcome_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
            logger.info(f"👤 User started: {user.id}")
        
        # /books command
        async def books(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not context.args:
                await update.message.reply_text(
                    f"{get_emoji('search')} *Book Search*\n\n"
                    "Please specify search query:\n"
                    "Example: `/books python programming`",
                    parse_mode='Markdown'
                )
                return
            
            query = " ".join(context.args)
            
            # Show typing
            await context.bot.send_chat_action(update.effective_chat.id, 'typing')
            
            # Sample results
            results_text = f"""
{get_emoji('trophy')} *SEARCH RESULTS*

🔍 *Query:* `{query}`
📚 *Found:* 15 books
⏱️ *Time:* {datetime.now().strftime('%H:%M:%S')}

📖 *Top Results:*
1. 📚 *Python Programming Guide*
   👤 John Doe | 📦 2.4 MB
   
2. ⭐ *Advanced Python Techniques*
   👤 Jane Smith | 📦 3.1 MB
   
3. 📚 *Web Development with Django*
   👤 Mike Johnson | 📦 4.2 MB

💡 *Tip:* Use specific keywords for better results.
            """
            
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = [
                [
                    InlineKeyboardButton(f"{get_emoji('download')} Download Python Guide", callback_data="download_python"),
                    InlineKeyboardButton(f"{get_emoji('download')} Download Django Book", callback_data="download_django")
                ],
                [
                    InlineKeyboardButton(f"{get_emoji('search')} New Search", callback_data="search"),
                    InlineKeyboardButton(f"{get_emoji('home')} Main Menu", callback_data="main_menu")
                ]
            ]
            
            await update.message.reply_text(
                results_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
            logger.info(f"🔍 Search: {query}")
        
        # /help command
        async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            help_text = f"""
{get_emoji('info')} *PREMIUM BOOK BOT HELP*

🎯 *Commands:*
• /start - Welcome message
• /books <query> - Search books
• /help - This help guide
• /stats - Bot statistics

🔍 *Examples:*
• `/books python programming`
• `/books harry potter`
• `/books web development`

📞 *Support:* {OWNER_USERNAME}
            """
            
            await update.message.reply_text(help_text, parse_mode='Markdown')
        
        # /stats command
        async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
            db = Database()
            stats_data = db.get_stats()
            
            text = f"""
{get_emoji('stats')} *BOT STATISTICS*

📊 *Overall Statistics:*
• 📚 Total Books: *{stats_data['total_books']:,}*
• 👥 Total Users: *{stats_data['total_users']:,}*

{get_emoji('time')} *Last Updated:* {datetime.now().strftime('%H:%M:%S')}
{get_emoji('calendar')} *Date:* {datetime.now().strftime('%Y-%m-%d')}
            """
            
            await update.message.reply_text(text, parse_mode='Markdown')
        
        # Callback handler
        async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query
            await query.answer()
            
            if query.data == "main_menu":
                from telegram import InlineKeyboardMarkup, InlineKeyboardButton
                keyboard = [
                    [
                        InlineKeyboardButton(f"{get_emoji('search')} Search", callback_data="search"),
                        InlineKeyboardButton(f"{get_emoji('stats')} Stats", callback_data="stats")
                    ],
                    [
                        InlineKeyboardButton(f"{get_emoji('info')} Help", callback_data="help")
                    ]
                ]
                
                await query.edit_message_text(
                    f"{get_emoji('home')} *Main Menu*",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            
            elif query.data == "search":
                await query.edit_message_text(
                    f"{get_emoji('search')} *Search Books*\n\n"
                    "Send me what you're looking for!\n\n"
                    "Example: `python programming books`",
                    parse_mode='Markdown'
                )
            
            elif query.data == "download_python":
                await query.answer("📥 Downloading Python Guide...", show_alert=True)
                # Here you would send the actual file
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="✅ *Python Programming Guide*\n\nDownload link would be sent here."
                )
        
        # Register handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_cmd))
        application.add_handler(CommandHandler("books", books))
        application.add_handler(CommandHandler("search", books))
        application.add_handler(CommandHandler("stats", stats))
        
        application.add_handler(CallbackQueryHandler(callback_handler))
        
        # Initialize and start
        await application.initialize()
        await application.start()
        
        # For PTB 21.x, we need to create updater differently
        from telegram.ext import Updater
        updater = Updater(bot=application.bot, update_queue=application.update_queue)
        await updater.start_polling()
        
        logger.info("=" * 60)
        logger.info("🎉 TELEGRAM BOT STARTED SUCCESSFULLY!")
        logger.info(f"🤖 Bot: {BOT_USERNAME}")
        logger.info(f"👑 Owner: {OWNER_ID}")
        logger.info("=" * 60)
        logger.info("🚀 Bot is now responding to commands!")
        logger.info("=" * 60)
        
        # Send notification to owner
        if OWNER_ID:
            try:
                await application.bot.send_message(
                    chat_id=OWNER_ID,
                    text=f"""
✅ *Premium Book Bot Started!*

🤖 *Bot:* Premium Book Bot
🆔 *Username:* {BOT_USERNAME}
🕐 *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📍 *Status:* ACTIVE 🟢

🚀 *Bot is now LIVE and responding!*
                    """,
                    parse_mode='Markdown'
                )
                logger.info("✅ Startup notification sent to owner")
            except Exception as e:
                logger.warning(f"⚠️ Could not notify owner: {e}")
        
        # Keep running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ Bot failed to start: {e}")
        import traceback
        logger.error(traceback.format_exc())

def run_bot():
    """Run bot in thread"""
    asyncio.run(start_telegram_bot())

# FLASK ROUTES
@app.route('/')
def home():
    uptime = int(time.time() - start_time)
    return jsonify({
        "status": "online",
        "service": "Premium Book Bot",
        "bot": BOT_USERNAME,
        "owner": OWNER_ID,
        "uptime": uptime,
        "bot_token_set": bool(BOT_TOKEN)
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy" if BOT_TOKEN else "unhealthy",
        "timestamp": time.time()
    }), 200 if BOT_TOKEN else 503

@app.route('/ping')
def ping():
    return jsonify({"message": "pong", "timestamp": time.time()})

# MAIN
def main():
    print("\n" + "="*60)
    print("🤖 PREMIUM BOOK BOT - PTB 21.x COMPATIBLE")
    print("="*60)
    print(f"🌐 Web Server: http://0.0.0.0:{PORT}")
    print(f"🤖 Bot Token: {'✅ SET' if BOT_TOKEN else '❌ NOT SET'}")
    print(f"👑 Owner ID: {OWNER_ID}")
    print(f"📚 Bot Username: {BOT_USERNAME}")
    print("="*60 + "\n")
    
    # Start bot in background if token is set
    if BOT_TOKEN:
        logger.info("🤖 Starting Telegram Bot in background...")
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        logger.info("✅ Bot thread started")
    else:
        logger.warning("⚠️ BOT_TOKEN not set. Bot will not start.")
    
    # Start Flask server
    logger.info(f"🚀 Starting web server on port {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

if __name__ == "__main__":
    main()
