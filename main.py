#!/usr/bin/env python3
"""
🤖 PREMIUM BOOK BOT - ALL IN ONE
Web Server + Telegram Bot in single file
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

# Flask App for health checks
app = Flask(__name__)
start_time = time.time()

# 🔧 CONFIGURATION
class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    OWNER_ID = int(os.getenv("OWNER_ID", 0))
    OWNER_USERNAME = os.getenv("OWNER_USERNAME", "@Admin")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "@PremiumBookBot")
    BOT_NAME = "📚 Premium Book Bot"
    BOT_LOCKED = False
    DM_ENABLED = True
    DB_PATH = "/tmp/book_bot.db"
    
    # Emojis
    EMOJIS = {
        "book": "📚", "search": "🔍", "download": "📥", "star": "⭐",
        "fire": "🔥", "heart": "❤️", "rocket": "🚀", "crown": "👑",
        "trophy": "🏆", "gem": "💎", "sparkle": "✨", "check": "✅",
        "warning": "⚠️", "error": "❌", "info": "ℹ️", "lock": "🔒",
        "unlock": "🔓", "user": "👤", "time": "🕐", "stats": "📊",
        "home": "🏠", "back": "🔙", "next": "➡️", "prev": "⬅️"
    }
    
    @classmethod
    def get_emoji(cls, key):
        return cls.EMOJIS.get(key, "📚")

# 💾 SIMPLE DATABASE
class Database:
    def __init__(self):
        self.db_path = Config.DB_PATH
        
    def initialize(self):
        """Initialize database"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id TEXT UNIQUE,
                title TEXT,
                author TEXT,
                file_id TEXT,
                file_type TEXT,
                file_size INTEGER,
                category TEXT,
                is_available BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                total_searches INTEGER DEFAULT 0,
                total_downloads INTEGER DEFAULT 0,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized")
        
        # Add sample books
        self._add_sample_books()
    
    def _add_sample_books(self):
        """Add sample books for testing"""
        sample_books = [
            {
                'book_id': 'python_guide',
                'title': 'Python Programming Guide',
                'author': 'John Doe',
                'file_id': 'BQACAgUAAxkBAAMIZj2kX5MAAe6TkCv2w1bh8LrWXGJWAALBCAACwQNxVj7DD_ZCj5S8MAQ',
                'file_type': 'PDF',
                'file_size': 2500000,
                'category': 'Programming'
            },
            {
                'book_id': 'web_dev',
                'title': 'Web Development with Django',
                'author': 'Jane Smith',
                'file_id': 'BQACAgUAAxkBAAMKZj2kYc_8oZ7p3q3h5nP5VQ2n3wACwggAAsEDcVaFQ8YyZ6nQvDAE',
                'file_type': 'PDF',
                'file_size': 3100000,
                'category': 'Web Development'
            },
            {
                'book_id': 'javascript',
                'title': 'JavaScript Mastery',
                'author': 'Mike Johnson',
                'file_id': 'BQACAgUAAxkBAAMMZj2kZQtxLr8jF3p5nK7lVQ2n3wACxAgAAsEDcVY6W6ZyZ6nQvDAE',
                'file_type': 'PDF',
                'file_size': 2800000,
                'category': 'Programming'
            }
        ]
        
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for book in sample_books:
            cursor.execute('''
                INSERT OR IGNORE INTO books 
                (book_id, title, author, file_id, file_type, file_size, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                book['book_id'],
                book['title'],
                book['author'],
                book['file_id'],
                book['file_type'],
                book['file_size'],
                book['category']
            ))
        
        conn.commit()
        conn.close()
        logger.info("📚 Sample books added")
    
    def search_books(self, query, limit=10):
        """Search books"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        search_term = f"%{query}%"
        cursor.execute('''
            SELECT * FROM books 
            WHERE (title LIKE ? OR author LIKE ? OR category LIKE ?)
            AND is_available = 1
            LIMIT ?
        ''', (search_term, search_term, search_term, limit))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        conn.close()
        return results
    
    def get_stats(self):
        """Get statistics"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM books WHERE is_available = 1')
        total_books = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_books': total_books,
            'total_users': total_users,
            'total_searches': 0,
            'total_downloads': 0
        }

# 🎨 TELEGRAM BOT
class PremiumBookBot:
    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.bot_app = None
        self.bot_running = False
    
    async def start_bot(self):
        """Start the Telegram bot"""
        try:
            # Check bot token
            if not self.config.BOT_TOKEN:
                logger.error("❌ BOT_TOKEN not found!")
                return
            
            logger.info("🚀 Starting Telegram Bot...")
            
            # Import telegram here to avoid early import errors
            from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
            from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
            
            # Create bot application
            self.bot_app = Application.builder().token(self.config.BOT_TOKEN).build()
            
            # Initialize database
            self.db.initialize()
            
            # 🎯 COMMAND HANDLERS
            
            # /start command
            async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
                user = update.effective_user
                
                welcome_text = f"""
{Config.get_emoji('crown')} *WELCOME TO PREMIUM BOOK BOT!* {Config.get_emoji('crown')}

👋 *Hello {user.first_name}!* I'm your personal library assistant.

{Config.get_emoji('book')} *What I Offer:*
• 🔍 Smart book search
• 📚 Vast collection
• 🚀 Fast downloads
• ⭐ Premium content
• 📊 Reading stats

{Config.get_emoji('rocket')} *Get Started:*
1. Use `/books python` to search
2. Browse `/categories`
3. Check `/stats`
4. Use `/help` for guidance

{Config.get_emoji('sparkle')} *Example:* `/books programming`

📞 *Support:* {self.config.OWNER_USERNAME}
                """
                
                keyboard = [
                    [
                        InlineKeyboardButton(f"{Config.get_emoji('search')} Search", callback_data="search"),
                        InlineKeyboardButton(f"{Config.get_emoji('category')} Categories", callback_data="categories")
                    ],
                    [
                        InlineKeyboardButton(f"{Config.get_emoji('stats')} Stats", callback_data="stats"),
                        InlineKeyboardButton(f"{Config.get_emoji('info')} Help", callback_data="help")
                    ]
                ]
                
                await update.message.reply_text(
                    welcome_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                
                logger.info(f"👤 User started: {user.id} - {user.username}")
            
            # /books command
            async def books(update: Update, context: ContextTypes.DEFAULT_TYPE):
                if self.config.BOT_LOCKED:
                    await update.message.reply_text(
                        f"{Config.get_emoji('lock')} *Bot under maintenance*\nPlease try again later.",
                        parse_mode='Markdown'
                    )
                    return
                
                if not context.args:
                    await update.message.reply_text(
                        f"{Config.get_emoji('search')} *Book Search*\n\n"
                        "Please specify search query:\n"
                        "Example: `/books python programming`",
                        parse_mode='Markdown'
                    )
                    return
                
                query = " ".join(context.args)
                
                # Show typing indicator
                await context.bot.send_chat_action(update.effective_chat.id, 'typing')
                
                # Search books
                books_found = self.db.search_books(query, limit=10)
                
                if not books_found:
                    await update.message.reply_text(
                        f"{Config.get_emoji('warning')} *No books found!*\n\n"
                        f"Query: `{query}`\n\n"
                        "💡 Try different keywords or check spelling.",
                        parse_mode='Markdown'
                    )
                    return
                
                # Format results
                text = f"""
{Config.get_emoji('trophy')} *SEARCH RESULTS* {Config.get_emoji('trophy')}

🔍 *Query:* `{query}`
📚 *Found:* {len(books_found)} books
⏱️ *Time:* {datetime.now().strftime('%H:%M:%S')}

📖 *Top Results:*
                """
                
                for i, book in enumerate(books_found[:5], 1):
                    text += f"\n{i}. {Config.get_emoji('book')} *{book['title']}*"
                    text += f"\n   👤 {book['author']} | 📦 {self._format_size(book.get('file_size', 0))}"
                
                if len(books_found) > 5:
                    text += f"\n\n📄 *+ {len(books_found) - 5} more books...*"
                
                # Create keyboard
                keyboard = []
                for book in books_found[:5]:
                    keyboard.append([
                        InlineKeyboardButton(
                            f"{Config.get_emoji('book')} {book['title'][:20]}",
                            callback_data=f"book_{book['book_id']}"
                        )
                    ])
                
                keyboard.append([
                    InlineKeyboardButton(f"{Config.get_emoji('search')} New Search", callback_data="search"),
                    InlineKeyboardButton(f"{Config.get_emoji('home')} Main Menu", callback_data="main_menu")
                ])
                
                await update.message.reply_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                
                logger.info(f"🔍 Search: {query} - {len(books_found)} results")
            
            # /stats command
            async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
                stats_data = self.db.get_stats()
                
                text = f"""
{Config.get_emoji('stats')} *BOT STATISTICS* {Config.get_emoji('stats')}

📊 *Overall Statistics:*
• 📚 Total Books: *{stats_data['total_books']:,}*
• 👥 Total Users: *{stats_data['total_users']:,}*
• 🔍 Total Searches: *{stats_data['total_searches']:,}*
• 📥 Total Downloads: *{stats_data['total_downloads']:,}*

{Config.get_emoji('time')} *Last Updated:* {datetime.now().strftime('%H:%M:%S')}
{Config.get_emoji('calendar')} *Date:* {datetime.now().strftime('%Y-%m-%d')}
                """
                
                await update.message.reply_text(text, parse_mode='Markdown')
            
            # /help command
            async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
                help_text = f"""
{Config.get_emoji('info')} *PREMIUM BOOK BOT HELP* {Config.get_emoji('info')}

🎯 *Basic Commands:*
• /start - Welcome message
• /books <query> - Search books
• /help - This help guide
• /stats - Bot statistics

🔍 *Search Examples:*
• `/books python programming`
• `/books harry potter`
• `/books web development`

📞 *Support:* {self.config.OWNER_USERNAME}

✨ *Enjoy reading!* 📚
                """
                
                await update.message.reply_text(help_text, parse_mode='Markdown')
            
            # /categories command
            async def categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
                categories = [
                    "📚 Fiction", "🔬 Science", "💻 Technology", "📈 Business",
                    "🏥 Health", "🎨 Arts", "📖 Education", "🌍 Travel"
                ]
                
                keyboard = []
                row = []
                for i, category in enumerate(categories, 1):
                    row.append(InlineKeyboardButton(category, callback_data=f"cat_{category[2:]}"))
                    if i % 2 == 0:
                        keyboard.append(row)
                        row = []
                
                if row:
                    keyboard.append(row)
                
                await update.message.reply_text(
                    f"{Config.get_emoji('category')} *Book Categories*",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            
            # Handle callback queries
            async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                query = update.callback_query
                await query.answer()
                
                if query.data == "main_menu":
                    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
                    keyboard = [
                        [
                            InlineKeyboardButton(f"{Config.get_emoji('search')} Search", callback_data="search"),
                            InlineKeyboardButton(f"{Config.get_emoji('category')} Categories", callback_data="categories")
                        ],
                        [
                            InlineKeyboardButton(f"{Config.get_emoji('stats')} Stats", callback_data="stats"),
                            InlineKeyboardButton(f"{Config.get_emoji('info')} Help", callback_data="help")
                        ]
                    ]
                    
                    await query.edit_message_text(
                        f"{Config.get_emoji('home')} *Main Menu*",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
                
                elif query.data == "search":
                    await query.edit_message_text(
                        f"{Config.get_emoji('search')} *Search Books*\n\n"
                        "Send me what you're looking for!\n\n"
                        "Example: `python programming books`",
                        parse_mode='Markdown'
                    )
                
                elif query.data.startswith("book_"):
                    book_id = query.data[5:]
                    await query.answer(f"📖 Book ID: {book_id}", show_alert=True)
            
            # Register handlers
            self.bot_app.add_handler(CommandHandler("start", start))
            self.bot_app.add_handler(CommandHandler("help", help_cmd))
            self.bot_app.add_handler(CommandHandler("books", books))
            self.bot_app.add_handler(CommandHandler("search", books))
            self.bot_app.add_handler(CommandHandler("stats", stats))
            self.bot_app.add_handler(CommandHandler("categories", categories))
            
            from telegram.ext import CallbackQueryHandler
            self.bot_app.add_handler(CallbackQueryHandler(callback_handler))
            
            # Start bot
            await self.bot_app.initialize()
            await self.bot_app.start()
            await self.bot_app.updater.start_polling()
            
            self.bot_running = True
            
            # 🎉 BOT STARTED SUCCESSFULLY
            logger.info("=" * 60)
            logger.info("🎉 TELEGRAM BOT STARTED SUCCESSFULLY!")
            logger.info("=" * 60)
            logger.info(f"🤖 Bot Username: {self.config.BOT_USERNAME}")
            logger.info(f"👑 Owner ID: {self.config.OWNER_ID}")
            logger.info(f"📊 Books: {self.db.get_stats()['total_books']}")
            logger.info(f"👥 Users: {self.db.get_stats()['total_users']}")
            logger.info("=" * 60)
            logger.info("🚀 Bot is now responding to commands!")
            logger.info("💬 Send /start to your bot on Telegram")
            logger.info("=" * 60)
            
            # Send notification to owner
            if self.config.OWNER_ID:
                try:
                    await self.bot_app.bot.send_message(
                        chat_id=self.config.OWNER_ID,
                        text=f"""
✅ *Premium Book Bot Started!*

🤖 *Bot:* {self.config.BOT_NAME}
🆔 *Username:* {self.config.BOT_USERNAME}
🕐 *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📍 *Status:* ACTIVE 🟢

📊 *Statistics:*
• Books: {self.db.get_stats()['total_books']}
• Users: {self.db.get_stats()['total_users']}

🚀 *Bot is now LIVE and responding!*
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
            self.bot_running = False
    
    def _format_size(self, size_bytes):
        """Format file size"""
        if not size_bytes:
            return "Unknown"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

# 🌐 FLASK ROUTES
@app.route('/')
def home():
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
    
    return jsonify({
        "status": "online",
        "service": "Premium Book Bot",
        "version": "2.0.0",
        "bot_configured": bool(Config.BOT_TOKEN),
        "owner_id": Config.OWNER_ID,
        "bot_username": Config.BOT_USERNAME,
        "uptime": uptime_str,
        "timestamp": time.time()
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy" if Config.BOT_TOKEN else "unhealthy",
        "bot": "premium-book-bot",
        "web_server": "running",
        "timestamp": time.time()
    }), 200 if Config.BOT_TOKEN else 503

@app.route('/ping')
def ping():
    return jsonify({"message": "pong", "timestamp": time.time()})

@app.route('/bot-status')
def bot_status():
    bot = PremiumBookBot()
    return jsonify({
        "telegram_bot": {
            "running": bot.bot_running,
            "configured": bool(Config.BOT_TOKEN),
            "username": Config.BOT_USERNAME
        },
        "web_server": {
            "running": True,
            "port": os.getenv("PORT", 10000),
            "uptime": int(time.time() - start_time)
        }
    })

# 🚀 MAIN FUNCTION
def start_bot_in_background():
    """Start Telegram bot in background thread"""
    bot = PremiumBookBot()
    
    def run_bot():
        try:
            asyncio.run(bot.start_bot())
        except Exception as e:
            logger.error(f"❌ Bot thread error: {e}")
    
    # Start bot thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("🤖 Telegram Bot starting in background thread...")

def main():
    """Main entry point - Start both web server and bot"""
    print("\n" + "="*60)
    print("🤖 PREMIUM BOOK BOT - ALL IN ONE")
    print("="*60)
    print(f"🌐 Web Server: http://0.0.0.0:{os.getenv('PORT', 10000)}")
    print(f"🤖 Bot Token: {'✅ SET' if Config.BOT_TOKEN else '❌ NOT SET'}")
    print(f"👑 Owner ID: {Config.OWNER_ID}")
    print(f"📚 Bot Username: {Config.BOT_USERNAME}")
    print("="*60 + "\n")
    
    # Start Telegram bot in background
    if Config.BOT_TOKEN:
        start_bot_in_background()
    else:
        logger.warning("⚠️ BOT_TOKEN not set. Bot will not start.")
    
    # Start Flask web server
    port = int(os.getenv("PORT", 10000))
    logger.info(f"🚀 Starting web server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    main()
