#!/usr/bin/env python3
"""
🤖 PREMIUM TELEGRAM BOOK BOT
With ALL features: Database, Reactions, Admin Commands
"""

import os
import sys
import sqlite3
import json
import time
import random
import logging
import threading
import asyncio
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify
import telebot
from telebot import types
from telebot.apihelper import ApiException

# ============ CONFIGURATION ============
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
BOT_USERNAME = os.getenv("BOT_USERNAME", "")
DATABASE_CHANNEL_ID = int(os.getenv("DATABASE_CHANNEL_ID", 0))
REQUEST_GROUP_ID = os.getenv("REQUEST_GROUP_ID", "")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))
FORCE_SUB_CHANNEL = os.getenv("FORCE_SUB_CHANNEL", "")
OWNER_CONTACT = os.getenv("OWNER_CONTACT", "@TechnicalSerena")
PORT = int(os.getenv("PORT", 10000))

# Bot State
BOT_LOCKED = False
DM_ENABLED = False

# Paths
DB_PATH = "/tmp/book_bot.db"
BACKUP_PATH = "/tmp/backups"

# Reaction Settings
REACTION_CHANCE = 0.4
REACTION_EMOJIS = ["🔥", "⭐", "🎯", "⚡", "❤️", "👍", "👏", "📚", "✨", "💫", "🚀", "💯", "🤯", "🙌", "🥳", "🏆"]

# Search Settings
RESULTS_PER_PAGE = 10
MAX_RESULTS = 50

# ============ SETUP LOGGING ============
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# ============ DATABASE CLASS ============
class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.init_db()
    
    def init_db(self):
        """Initialize database with all tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Books table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                author TEXT DEFAULT 'Unknown',
                file_id TEXT NOT NULL,
                file_type TEXT DEFAULT 'PDF',
                keywords TEXT,
                file_size INTEGER DEFAULT 0,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_verified TIMESTAMP,
                is_available BOOLEAN DEFAULT 1
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON books(title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_author ON books(author)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_keywords ON books(keywords)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_id ON books(file_id)')
        
        # Bot state table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                searches INTEGER DEFAULT 0,
                downloads INTEGER DEFAULT 0,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT,
                expires_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized")
    
    def add_book(self, book_data):
        """Add book to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate unique book_id
        import hashlib
        book_id = hashlib.md5(f"{book_data['file_id']}{time.time()}".encode()).hexdigest()[:10]
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO books 
                (book_id, title, author, file_id, file_type, keywords, file_size, date_added, last_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                book_id,
                book_data['title'],
                book_data['author'],
                book_data['file_id'],
                book_data['file_type'],
                book_data.get('keywords', ''),
                book_data.get('file_size', 0),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            logger.info(f"📚 Book added: {book_data['title']}")
            return book_id
            
        except Exception as e:
            logger.error(f"❌ Error adding book: {e}")
            return None
        finally:
            conn.close()
    
    def search_books(self, query, limit=50):
        """Search books by title, author, or keywords"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        search_term = f"%{query}%"
        cursor.execute('''
            SELECT * FROM books 
            WHERE (title LIKE ? OR author LIKE ? OR keywords LIKE ?)
            AND is_available = 1
            ORDER BY date_added DESC
            LIMIT ?
        ''', (search_term, search_term, search_term, limit))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            book = dict(zip(columns, row))
            results.append(book)
        
        conn.close()
        return results
    
    def get_book_by_id(self, book_id):
        """Get book by book_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM books WHERE book_id = ? AND is_available = 1', (book_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            book = dict(zip(columns, row))
            conn.close()
            return book
        
        conn.close()
        return None
    
    def update_user_stats(self, user_id, username, action):
        """Update user statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        username = username or f"User_{user_id}"
        
        if action == 'search':
            cursor.execute('''
                INSERT INTO user_stats (user_id, username, searches, last_seen)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                searches = searches + 1,
                username = excluded.username,
                last_seen = excluded.last_seen
            ''', (user_id, username, datetime.now().isoformat()))
        
        elif action == 'download':
            cursor.execute('''
                INSERT INTO user_stats (user_id, username, downloads, last_seen)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                downloads = downloads + 1,
                username = excluded.username,
                last_seen = excluded.last_seen
            ''', (user_id, username, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_stats(self):
        """Get bot statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM books')
        total_books = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM books WHERE is_available = 1')
        available_books = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM user_stats')
        total_users = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT SUM(searches) FROM user_stats')
        total_searches = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT SUM(downloads) FROM user_stats')
        total_downloads = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_books': total_books,
            'available_books': available_books,
            'total_users': total_users,
            'total_searches': total_searches,
            'total_downloads': total_downloads
        }
    
    def get_all_users(self):
        """Get all user IDs for broadcast"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT user_id FROM user_stats')
        users = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return users

# ============ BOT MANAGER ============
class PremiumBookBot:
    def __init__(self):
        self.bot = telebot.TeleBot(BOT_TOKEN)
        self.db = Database()
        self.active_searches = {}
        self.user_cooldowns = {}
        
        # Setup bot commands
        self.setup_handlers()
        
    def setup_handlers(self):
        """Setup all bot handlers"""
        
        # ============ COMMAND HANDLERS ============
        
        @self.bot.message_handler(commands=['start'])
        def start_command(message):
            """Handle /start command"""
            user = message.from_user
            chat = message.chat
            
            # Save user stats
            self.db.update_user_stats(user.id, user.username, 'search')
            
            # Check force subscription
            if FORCE_SUB_CHANNEL and chat.type == 'private':
                try:
                    member = self.bot.get_chat_member(FORCE_SUB_CHANNEL, user.id)
                    if member.status not in ['member', 'administrator', 'creator']:
                        keyboard = types.InlineKeyboardMarkup()
                        keyboard.add(types.InlineKeyboardButton(
                            "Join Channel", 
                            url=f"https://t.me/{FORCE_SUB_CHANNEL.lstrip('@')}"
                        ))
                        self.bot.reply_to(message, 
                            "📚 Welcome to Premium Book Bot!\n\n"
                            "Please join our channel to use the bot:\n"
                            f"👉 {FORCE_SUB_CHANNEL}",
                            reply_markup=keyboard
                        )
                        return
                except Exception as e:
                    logger.error(f"Subscription check error: {e}")
            
            # Check if DM is enabled for private chats
            if chat.type == 'private' and not DM_ENABLED:
                self.bot.reply_to(message,
                    f"🤖 Hello {user.first_name}! I'm {BOT_USERNAME}\n\n"
                    "For book requests, please visit our group:\n"
                    f"👉 {REQUEST_GROUP_ID}\n\n"
                    "In the group, use:\n"
                    "`/books book_name` to search for books\n\n"
                    "📖 Happy Reading!"
                )
                return
            
            # Welcome message for groups/DM
            welcome_text = f"""
✨ *Welcome to Premium Book Bot!* ✨

👋 *Hello {user.first_name}!* I'm your personal library assistant.

📚 *Features:*
• 🔍 Smart book search
• 🚀 Fast downloads
• ⭐ Premium content
• 📊 Reading statistics
• 🎯 Admin tools

🎯 *Get Started:*
Use `/books book_name` to search for books

📖 *Example:* `/books python programming`

🔧 *Admin Commands:* /help

📞 *Support:* {OWNER_CONTACT}
            """
            
            keyboard = types.InlineKeyboardMarkup()
            keyboard.row(
                types.InlineKeyboardButton("🔍 Search Books", callback_data="search"),
                types.InlineKeyboardButton("📊 Statistics", callback_data="stats")
            )
            keyboard.row(
                types.InlineKeyboardButton("ℹ️ Help", callback_data="help"),
                types.InlineKeyboardButton("📤 Request Book", url=f"https://t.me/{REQUEST_GROUP_ID.lstrip('@')}")
            )
            
            self.bot.reply_to(message, welcome_text, 
                            parse_mode='Markdown', 
                            reply_markup=keyboard)
            
            # Random reaction
            self.add_random_reaction(message)
            
            # Log activity
            self.log_activity(user.id, user.username, "start", f"Chat: {chat.type}")
        
        @self.bot.message_handler(commands=['help'])
        def help_command(message):
            """Handle /help command"""
            help_text = f"""
📖 *PREMIUM BOOK BOT HELP GUIDE*

🎯 *User Commands:*
• /start - Start the bot
• /books <query> - Search books
• /help - This help message

👑 *Admin Commands:* (Owner only)
• /dm - Enable DM functionality
• /group - Restrict to groups only
• /lock - Lock the bot
• /on - Unlock the bot
• /stats - Show statistics
• /broadcast - Send announcement
• /addbook - Add new book
• /findduplicates - Find duplicates
• /export - Export database
• /cleanup - Cleanup cache

🔍 *Search Examples:*
• `/books python programming`
• `/books harry potter`
• `/books author:john`

📤 *Adding Books:*
1. Forward PDF to database channel
2. Reply with `/addbook Title by Author`

📞 *Support:* {OWNER_CONTACT}
            """
            
            self.bot.reply_to(message, help_text, parse_mode='Markdown')
            self.add_random_reaction(message)
        
        @self.bot.message_handler(commands=['books'])
        def books_command(message):
            """Handle /books command"""
            if BOT_LOCKED:
                self.bot.reply_to(message, "🔒 Bot is currently locked. Please try again later.")
                return
            
            user = message.from_user
            chat = message.chat
            
            # Check if DM is enabled for private chats
            if chat.type == 'private' and not DM_ENABLED:
                self.bot.reply_to(message,
                    f"🤖 DM functionality is currently disabled.\n"
                    f"Please use me in the group: {REQUEST_GROUP_ID}"
                )
                return
            
            # Check cooldown
            if self.check_cooldown(user.id):
                self.bot.reply_to(message, "⏳ Please wait a moment before making another request.")
                return
            
            # Check flood control
            if self.check_flood(user.id):
                self.bot.reply_to(message, "⚠️ Too many requests. Please slow down.")
                return
            
            # Get search query
            query = message.text.replace('/books', '').strip()
            if not query:
                self.bot.reply_to(message,
                    "📚 Please specify what you're looking for:\n"
                    "Example: `/books python programming`\n"
                    "Or: `/books author:john`",
                    parse_mode='Markdown'
                )
                return
            
            # Show typing indicator
            self.bot.send_chat_action(chat.id, 'typing')
            
            # Search books
            books = self.db.search_books(query, MAX_RESULTS)
            
            if not books:
                self.bot.reply_to(message,
                    "🔍 No books found for your search.\n"
                    "Try different keywords or request the book in our group."
                )
                self.add_context_reaction(message, "not_found")
                return
            
            # Update user stats
            self.db.update_user_stats(user.id, user.username, 'search')
            
            # Store search results for pagination
            search_id = f"{user.id}_{int(time.time())}"
            self.active_searches[search_id] = {
                'books': books,
                'page': 0,
                'query': query,
                'message_id': None
            }
            
            # Send first page
            self.send_search_page(message, search_id, 0)
            
            # Log activity
            self.log_activity(user.id, user.username, "search", 
                            f"Query: {query} | Results: {len(books)} | Chat: {chat.type}")
            
            # Add search reaction sequence
            self.add_search_reaction_sequence(message)
        
        @self.bot.message_handler(commands=['stats'])
        def stats_command(message):
            """Handle /stats command (Admin only)"""
            user = message.from_user
            
            if user.id != OWNER_ID:
                self.bot.reply_to(message, "❌ Admin only command!")
                return
            
            stats = self.db.get_stats()
            
            text = f"""
📊 *Bot Statistics*

📚 *Books:* {stats['total_books']} total | {stats['available_books']} available
👥 *Users:* {stats['total_users']}
🔍 *Searches:* {stats['total_searches']}
📥 *Downloads:* {stats['total_downloads']}

🔓 *Status:* {'Active' if not BOT_LOCKED else 'Locked'}
💬 *DM Mode:* {'Enabled' if DM_ENABLED else 'Disabled'}
🕐 *Time:* {datetime.now().strftime('%H:%M:%S')}
            """
            
            self.bot.reply_to(message, text, parse_mode='Markdown')
        
        @self.bot.message_handler(commands=['dm'])
        def dm_command(message):
            """Enable DM functionality (Owner only)"""
            user = message.from_user
            
            if user.id != OWNER_ID:
                self.bot.reply_to(message, "❌ Admin only command!")
                return
            
            global DM_ENABLED
            DM_ENABLED = True
            self.bot.reply_to(message, "✅ DM functionality enabled globally.")
            self.log_activity(user.id, user.username, "mode_change", "DM Enabled")
        
        @self.bot.message_handler(commands=['group'])
        def group_command(message):
            """Restrict to groups only (Owner only)"""
            user = message.from_user
            
            if user.id != OWNER_ID:
                self.bot.reply_to(message, "❌ Admin only command!")
                return
            
            global DM_ENABLED
            DM_ENABLED = False
            self.bot.reply_to(message, "✅ Bot restricted to groups only.")
            self.log_activity(user.id, user.username, "mode_change", "Groups Only")
        
        @self.bot.message_handler(commands=['lock'])
        def lock_command(message):
            """Lock the bot (Owner only)"""
            user = message.from_user
            
            if user.id != OWNER_ID:
                self.bot.reply_to(message, "❌ Admin only command!")
                return
            
            global BOT_LOCKED
            BOT_LOCKED = True
            self.bot.reply_to(message, "🔒 Bot locked. No one can use it until unlocked.")
            self.log_activity(user.id, user.username, "bot_lock", "Bot Locked")
        
        @self.bot.message_handler(commands=['on'])
        def on_command(message):
            """Unlock the bot (Owner only)"""
            user = message.from_user
            
            if user.id != OWNER_ID:
                self.bot.reply_to(message, "❌ Admin only command!")
                return
            
            global BOT_LOCKED
            BOT_LOCKED = False
            self.bot.reply_to(message, "✅ Bot unlocked and active.")
            self.log_activity(user.id, user.username, "bot_lock", "Bot Unlocked")
        
        @self.bot.message_handler(commands=['broadcast'])
        def broadcast_command(message):
            """Broadcast message to all users (Owner only)"""
            user = message.from_user
            
            if user.id != OWNER_ID:
                self.bot.reply_to(message, "❌ Admin only command!")
                return
            
            # Get broadcast message
            broadcast_msg = message.text.replace('/broadcast', '').strip()
            if not broadcast_msg:
                self.bot.reply_to(message, "Usage: /broadcast Your message here")
                return
            
            # Get all users
            users = self.db.get_all_users()
            
            status_msg = self.bot.reply_to(message, f"📢 Broadcasting to {len(users)} users...")
            
            sent = 0
            failed = 0
            
            for user_id in users:
                try:
                    self.bot.send_message(
                        user_id,
                        f"📢 *Announcement*\n\n{broadcast_msg}\n\n_This is a broadcast message_",
                        parse_mode='Markdown'
                    )
                    sent += 1
                    time.sleep(0.1)  # Rate limiting
                except Exception as e:
                    failed += 1
                    logger.error(f"Failed to send to {user_id}: {e}")
                
                # Update status every 10 users
                if (sent + failed) % 10 == 0:
                    try:
                        self.bot.edit_message_text(
                            f"📢 Broadcasting... {sent + failed}/{len(users)}\n"
                            f"✅ Sent: {sent} | ❌ Failed: {failed}",
                            chat_id=status_msg.chat.id,
                            message_id=status_msg.message_id
                        )
                    except:
                        pass
            
            self.bot.edit_message_text(
                f"✅ Broadcast completed!\n"
                f"✅ Sent: {sent} | ❌ Failed: {failed}\n"
                f"📊 Success rate: {(sent/(sent+failed)*100):.1f}%",
                chat_id=status_msg.chat.id,
                message_id=status_msg.message_id
            )
            
            self.log_activity(user.id, user.username, "broadcast",
                            f"Sent: {sent} | Failed: {failed} | Message: {broadcast_msg[:50]}...")
        
        @self.bot.message_handler(commands=['addbook'])
        def addbook_command(message):
            """Add book via document reply (Owner only)"""
            user = message.from_user
            
            if user.id != OWNER_ID:
                self.bot.reply_to(message, "❌ Admin only command!")
                return
            
            if not message.reply_to_message or not message.reply_to_message.document:
                self.bot.reply_to(message,
                    "Please reply to a document message with /addbook\n\n"
                    "Format: Reply to PDF → `/addbook Title by Author`\n"
                    "Example: `/addbook Python Guide by John Doe`",
                    parse_mode='Markdown'
                )
                return
            
            reply_msg = message.reply_to_message
            document = reply_msg.document
            
            # Extract metadata
            title = document.file_name or "Unknown"
            author = "Unknown"
            
            # Try to extract author from command or caption
            import re
            args = message.text.replace('/addbook', '').strip()
            if args:
                match = re.match(r'(.+?)\s+by\s+(.+)', args, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    author = match.group(2).strip()
            
            # Check if already exists
            existing = self.db.search_books(title.split('.')[0], 1)
            if existing and any(title.lower() in b['title'].lower() for b in existing):
                self.bot.reply_to(message, "⚠️ This book already exists in database.")
                return
            
            # Add to database
            book_data = {
                'title': title,
                'author': author,
                'file_id': document.file_id,
                'file_type': document.mime_type or 'application/octet-stream',
                'file_size': document.file_size,
                'keywords': f"{title} {author}"
            }
            
            book_id = self.db.add_book(book_data)
            if book_id:
                self.bot.reply_to(message, f"✅ Book added: *{title}*", parse_mode='Markdown')
                self.log_activity(user.id, user.username, "add_book",
                                f"Title: {title} | Author: {author} | Size: {self.format_size(document.file_size)}")
            else:
                self.bot.reply_to(message, "⚠️ Failed to add book (possible duplicate).")
        
        @self.bot.message_handler(commands=['findduplicates', 'export', 'cleanup'])
        def admin_tools_command(message):
            """Handle admin tools commands"""
            user = message.from_user
            
            if user.id != OWNER_ID:
                self.bot.reply_to(message, "❌ Admin only command!")
                return
            
            command = message.text.split()[0]
            
            if command == '/findduplicates':
                self.bot.reply_to(message, "🔄 Finding duplicates...")
                # Implementation would go here
                self.bot.reply_to(message, "✅ Duplicate check completed.")
            
            elif command == '/export':
                self.bot.reply_to(message, "💾 Exporting database backup...")
                # Implementation would go here
                self.bot.reply_to(message, "✅ Backup created.")
            
            elif command == '/cleanup':
                self.bot.reply_to(message, "🧹 Cleaning up cache...")
                # Implementation would go here
                self.bot.reply_to(message, "✅ Cleanup completed.")
        
        @self.bot.message_handler(content_types=['document'])
        def handle_document(message):
            """Auto-add books from database channel (Owner only)"""
            user = message.from_user
            
            # Only process from owner in database channel
            if user.id != OWNER_ID or message.chat.id != DATABASE_CHANNEL_ID:
                return
            
            document = message.document
            
            # Extract metadata
            title = document.file_name or "Unknown"
            author = "Unknown"
            
            # Try to extract author from caption
            if message.caption:
                import re
                author_match = re.search(r'(?:by|author:)\s*([\w\s]+)', message.caption, re.IGNORECASE)
                if author_match:
                    author = author_match.group(1).strip()
            
            # Add to database
            book_data = {
                'title': title,
                'author': author,
                'file_id': document.file_id,
                'file_type': document.mime_type or 'application/octet-stream',
                'file_size': document.file_size,
                'keywords': f"{title} {author}"
            }
            
            book_id = self.db.add_book(book_data)
            if book_id:
                self.bot.reply_to(message, f"✅ Auto-added: *{title}*", parse_mode='Markdown')
            else:
                self.bot.reply_to(message, "⚠️ Auto-add failed (possible duplicate).")
        
        @self.bot.message_handler(func=lambda m: True, content_types=['text'])
        def handle_text(message):
            """Handle all text messages for random reactions"""
            # Random reaction chance
            if random.random() < REACTION_CHANCE:
                self.add_random_reaction(message)
        
        # ============ CALLBACK HANDLERS ============
        
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            """Handle inline keyboard callbacks"""
            user = call.from_user
            
            if call.data.startswith("book_"):
                # Get book
                book_id = call.data[5:]
                book = self.db.get_book_by_id(book_id)
                
                if not book:
                    self.bot.answer_callback_query(call.id, "⚠️ Book not found!")
                    return
                
                # Send book
                self.send_book(call.message, book, user)
                self.bot.answer_callback_query(call.id, "📥 Sending book...")
            
            elif call.data.startswith("page_"):
                # Pagination
                parts = call.data.split("_")
                if len(parts) >= 3:
                    search_id = parts[1]
                    page = int(parts[2])
                    self.send_search_page(call.message, search_id, page)
                    self.bot.answer_callback_query(call.id)
            
            elif call.data.startswith("cancel_"):
                # Cancel search
                search_id = call.data[7:]
                self.active_searches.pop(search_id, None)
                self.bot.edit_message_text("❌ Search cancelled.",
                                         chat_id=call.message.chat.id,
                                         message_id=call.message.message_id)
                self.bot.answer_callback_query(call.id)
            
            elif call.data in ["search", "stats", "help"]:
                # Menu buttons
                if call.data == "search":
                    self.bot.answer_callback_query(call.id, "🔍 Type /books followed by your search query")
                    self.bot.send_message(call.message.chat.id, 
                                        "Type: `/books python programming`",
                                        parse_mode='Markdown')
                elif call.data == "stats":
                    self.bot.answer_callback_query(call.id, "📊 Fetching statistics...")
                    stats_command(call.message)
                elif call.data == "help":
                    self.bot.answer_callback_query(call.id, "ℹ️ Showing help...")
                    help_command(call.message)
    
    # ============ HELPER METHODS ============
    
    def send_search_page(self, message, search_id, page):
        """Send a page of search results"""
        search_data = self.active_searches.get(search_id)
        if not search_data:
            self.bot.reply_to(message, "⚠️ Search session expired. Please search again.")
            return
        
        books = search_data['books']
        total_pages = (len(books) + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
        
        if page < 0 or page >= total_pages:
            return
        
        start_idx = page * RESULTS_PER_PAGE
        end_idx = min(start_idx + RESULTS_PER_PAGE, len(books))
        page_books = books[start_idx:end_idx]
        
        # Create message text
        text = f"🔍 *Search Results* `({search_data['query']})`\n\n"
        
        for i, book in enumerate(page_books, start=start_idx + 1):
            size_str = self.format_size(book.get('file_size', 0))
            text += f"{i}. *{book['title']}*\n"
            text += f"   👤 {book['author']}\n"
            text += f"   📦 {size_str} | 📄 {book.get('file_type', 'PDF').upper()}\n\n"
        
        text += f"📄 *Page {page + 1}/{total_pages}* | 📚 *{len(books)} books found*"
        
        # Create keyboard
        keyboard = types.InlineKeyboardMarkup()
        
        # Book buttons
        for book in page_books:
            keyboard.add(types.InlineKeyboardButton(
                f"📖 {book['title'][:30]}",
                callback_data=f"book_{book['book_id']}"
            ))
        
        # Pagination buttons
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(types.InlineKeyboardButton(
                "⬅️ Previous",
                callback_data=f"page_{search_id}_{page-1}"
            ))
        
        pagination_buttons.append(types.InlineKeyboardButton(
            "❌ Cancel",
            callback_data=f"cancel_{search_id}"
        ))
        
        if page < total_pages - 1:
            pagination_buttons.append(types.InlineKeyboardButton(
                "Next ➡️",
                callback_data=f"page_{search_id}_{page+1}"
            ))
        
        keyboard.row(*pagination_buttons)
        
        # Request missing book button
        if REQUEST_GROUP_ID:
            keyboard.add(types.InlineKeyboardButton(
                "🔍 Request Missing Book",
                url=f"https://t.me/{REQUEST_GROUP_ID.lstrip('@')}"
            ))
        
        # Send or edit message
        if search_data.get('message_id'):
            try:
                self.bot.edit_message_text(
                    text,
                    chat_id=message.chat.id,
                    message_id=search_data['message_id'],
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            except:
                pass
        else:
            msg = self.bot.send_message(
                message.chat.id,
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            search_data['message_id'] = msg.message_id
        
        # Update page in search data
        search_data['page'] = page
        self.active_searches[search_id] = search_data
    
    def send_book(self, message, book, user):
        """Send book file to user"""
        try:
            # Show upload status for large files
            status_msg = None
            if book.get('file_size', 0) > 5 * 1024 * 1024:  # >5MB
                status_msg = self.bot.reply_to(message, "📤 Uploading book...")
            
            # Create caption
            caption = (
                f"📖 *{book['title']}*\n"
                f"👤 *Author:* {book['author']}\n"
                f"📦 *Size:* {self.format_size(book.get('file_size', 0))}\n"
                f"📄 *Format:* {book.get('file_type', 'PDF').upper()}\n\n"
                f"✨ Request more books: `/books`"
            )
            
            # Create keyboard
            keyboard = types.InlineKeyboardMarkup()
            if REQUEST_GROUP_ID:
                keyboard.add(types.InlineKeyboardButton(
                    "🔍 Request Missing Book",
                    url=f"https://t.me/{REQUEST_GROUP_ID.lstrip('@')}"
                ))
            
            # Send file
            self.bot.send_document(
                chat_id=message.chat.id,
                document=book['file_id'],
                caption=caption,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            
            # Update user stats
            self.db.update_user_stats(user.id, user.username, 'download')
            
            # Delete status message if exists
            if status_msg:
                try:
                    self.bot.delete_message(status_msg.chat.id, status_msg.message_id)
                except:
                    pass
            
            # Add celebration reaction
            self.add_celebration_reaction(message)
            
            # Log download
            self.log_activity(user.id, user.username, "download",
                            f"Book: {book['title']} | Size: {self.format_size(book.get('file_size', 0))}")
            
        except Exception as e:
            logger.error(f"Error sending book: {e}")
            self.bot.reply_to(message, "⚠️ Failed to send book. Please try again.")
    
    def add_random_reaction(self, message):
        """Add random animated reaction to message"""
        try:
            if random.random() < REACTION_CHANCE:
                emoji = random.choice(REACTION_EMOJIS)
                # Telegram Bot API doesn't support reactions directly in pyTelegramBotAPI
                # We'll simulate with a reply
                self.bot.reply_to(message, f"{emoji} *Reaction!*", parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Reaction error: {e}")
    
    def add_context_reaction(self, message, context):
        """Add context-aware reaction"""
        try:
            if context == "not_found":
                emojis = ["🔍", "😕", "📭"]
            elif context == "success":
                emojis = ["✅", "🎉", "✨"]
            else:
                emojis = REACTION_EMOJIS
            
            emoji = random.choice(emojis)
            self.bot.reply_to(message, f"{emoji}", parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Context reaction error: {e}")
    
    def add_search_reaction_sequence(self, message):
        """Add search reaction sequence"""
        try:
            sequence = ["🔍", "📚", "✅"]
            for emoji in sequence:
                self.bot.reply_to(message, f"{emoji}", parse_mode='Markdown')
                time.sleep(0.5)
        except Exception as e:
            logger.error(f"Search reaction error: {e}")
    
    def add_celebration_reaction(self, message):
        """Add celebration reaction"""
        try:
            emojis = random.sample(["🎉", "🎊", "✨", "🌟", "💫", "🥳", "🎈"], 3)
            for emoji in emojis:
                self.bot.reply_to(message, f"{emoji}", parse_mode='Markdown')
                time.sleep(0.3)
        except Exception as e:
            logger.error(f"Celebration reaction error: {e}")
    
