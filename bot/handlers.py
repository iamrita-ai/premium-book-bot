import logging
import random
from datetime import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from config import Config
from .utils import format_message, create_keyboard, send_animated_message

logger = logging.getLogger(__name__)

class PremiumHandlers:
    """🎨 Premium Handlers with Beautiful UI"""
    
    def __init__(self, db, reaction_manager):
        self.config = Config()
        self.db = db
        self.reaction_manager = reaction_manager
        self.active_searches = {}
    
    def register(self, app):
        """Register all handlers"""
        
        # 🎯 BASIC COMMANDS
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("help", self.help))
        app.add_handler(CommandHandler("books", self.search_books))
        app.add_handler(CommandHandler("search", self.search_books))
        app.add_handler(CommandHandler("categories", self.categories))
        app.add_handler(CommandHandler("stats", self.stats))
        app.add_handler(CommandHandler("about", self.about))
        
        # 👑 ADMIN COMMANDS
        app.add_handler(CommandHandler("admin", self.admin))
        app.add_handler(CommandHandler("addbook", self.add_book))
        app.add_handler(CommandHandler("broadcast", self.broadcast))
        app.add_handler(CommandHandler("lock", self.lock_bot))
        app.add_handler(CommandHandler("unlock", self.unlock_bot))
        
        # 💬 MESSAGE HANDLERS
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        logger.info("✅ Premium handlers registered")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """🎯 Premium Start Command with Beautiful UI"""
        user = update.effective_user
        
        # ✨ WELCOME MESSAGE WITH FORMATTING
        welcome = f"""
{self.config.get_emoji('crown')} *WELCOME TO PREMIUM BOOK BOT!* {self.config.get_emoji('crown')}

👋 *Hello {user.first_name}!* I'm your personal library assistant.

{self.config.get_emoji('book')} *What I Offer:*
• 🔍 *Smart Search* - Find any book instantly
• 📚 *Vast Collection* - Thousands of books
• 🚀 *Fast Downloads* - Direct from Telegram
• ⭐ *Premium Content* - Exclusive books
• 📊 *Reading Stats* - Track your journey

{self.config.get_emoji('rocket')} *Get Started:*
1. Use `/books <query>` to search
2. Browse `/categories` by genre
3. Check `/stats` for bot insights
4. Use `/help` for guidance

{self.config.get_emoji('sparkle')} *Pro Tips:*
• Use specific keywords
• Include author names
• Try different categories
• Request missing books

📞 *Support:* {self.config.OWNER_USERNAME}
        """
        
        # 🎨 KEYBOARD
        keyboard = [
            [
                InlineKeyboardButton(f"{self.config.get_emoji('search')} Search Books", callback_data="search"),
                InlineKeyboardButton(f"{self.config.get_emoji('category')} Categories", callback_data="categories")
            ],
            [
                InlineKeyboardButton(f"{self.config.get_emoji('stats')} Statistics", callback_data="stats"),
                InlineKeyboardButton(f"{self.config.get_emoji('info')} Help", callback_data="help")
            ],
            [
                InlineKeyboardButton(f"{self.config.get_emoji('fire')} Popular Books", callback_data="popular"),
                InlineKeyboardButton(f"{self.config.get_emoji('gem')} Premium", callback_data="premium")
            ]
        ]
        
        # 📨 SEND WELCOME MESSAGE
        await update.message.reply_text(
            welcome,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        # ✨ ADD REACTION
        await self.reaction_manager.add_reaction(update.message, context.bot, "welcome")
        
        # 📊 LOG USER
        self.db.add_user(user.id, user.username, user.first_name)
        logger.info(f"👤 New user: {user.id} - {user.username}")
    
    async def search_books(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """🔍 Premium Search with Beautiful Results"""
        if self.config.BOT_LOCKED:
            locked_msg = f"""
{self.config.get_emoji('lock')} *BOT TEMPORARILY UNAVAILABLE* {self.config.get_emoji('lock')}

🔧 *Maintenance in progress...*
⏳ Please try again in a few minutes.

📞 Contact {self.config.OWNER_USERNAME} for updates.
            """
            await update.message.reply_text(locked_msg, parse_mode='Markdown')
            return
        
        user = update.effective_user
        
        # 📝 CHECK QUERY
        if not context.args:
            help_text = f"""
{self.config.get_emoji('search')} *BOOK SEARCH GUIDE* {self.config.get_emoji('search')}

📝 *How to Search:*
`/books python programming`
`/books harry potter`
`/books author:stephen king`
`/books self help`

💡 *Search Tips:*
• Be specific with keywords
• Include author names
• Use category names
• Try different variations

🎯 *Examples:*
• `/books python for beginners`
• `/books atomic habits`
• `/books romance novels`
• `/books business strategy`
            """
            await update.message.reply_text(help_text, parse_mode='Markdown')
            return
        
        query = " ".join(context.args)
        
        # ⏳ SHOW TYPING
        await context.bot.send_chat_action(update.effective_chat.id, 'typing')
        
        # 🎨 SEARCHING ANIMATION
        searching_msg = await update.message.reply_text(
            f"{self.config.get_emoji('search')} *Searching database...*\n"
            f"🔍 Query: `{query}`\n\n"
            f"{'▰' * 10}",
            parse_mode='Markdown'
        )
        
        # 📊 SEARCH BOOKS
        books = self.db.search_books(query, limit=10)
        
        # 📈 UPDATE STATS
        self.db.update_user_stats(user.id, 'search')
        
        if not books:
            # ❌ NO RESULTS
            no_results = f"""
{self.config.get_emoji('warning')} *NO BOOKS FOUND* {self.config.get_emoji('warning')}

🔍 *Your Search:* `{query}`
📭 *Results:* 0 books found

💡 *Suggestions:*
1. Check spelling mistakes
2. Try different keywords
3. Search by author name
4. Browse categories instead

🎯 *Try These:*
• `/books python` (instead of 'pythn')
• `/books fiction` (broad category)
• `/categories` (browse all)

📤 *Request This Book:*
Can't find what you need? Request it in our group!
            """
            
            keyboard = [[
                InlineKeyboardButton(
                    f"{self.config.get_emoji('fire')} Request Book", 
                    url=f"https://t.me/{self.config.REQUEST_GROUP.lstrip('@')}"
                )
            ]]
            
            await searching_msg.edit_text(
                no_results,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        # ✅ FOUND RESULTS
        found_msg = f"""
{self.config.get_emoji('trophy')} *SEARCH RESULTS* {self.config.get_emoji('trophy')}

🔍 *Query:* `{query}`
📚 *Found:* {len(books)} books
⏱️ *Time:* {datetime.now().strftime('%H:%M:%S')}

📖 *Top Results:*
        """
        
        # 📋 LIST BOOKS
        for i, book in enumerate(books[:5], 1):
            emoji = self.config.get_emoji('star') if book.get('is_premium') else self.config.get_emoji('book')
            found_msg += f"\n{i}. {emoji} *{book['title'][:30]}*"
            found_msg += f"\n   👤 {book['author'][:20]} | 📦 {self._format_size(book.get('file_size', 0))}"
        
        if len(books) > 5:
            found_msg += f"\n\n📄 *+ {len(books) - 5} more books...*"
        
        # 🎨 CREATE KEYBOARD
        keyboard = []
        for book in books[:5]:
            title = book['title'][:25] + "..." if len(book['title']) > 25 else book['title']
            emoji = self.config.get_emoji('star') if book.get('is_premium') else self.config.get_emoji('book')
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {title}",
                    callback_data=f"book_{book['book_id']}"
                )
            ])
        
        # 🔄 PAGINATION
        keyboard.append([
            InlineKeyboardButton(f"{self.config.get_emoji('prev')} Previous", callback_data="prev"),
            InlineKeyboardButton(f"1/{max(1, len(books)//5)}", callback_data="page"),
            InlineKeyboardButton(f"Next {self.config.get_emoji('next')}", callback_data="next")
        ])
        
        keyboard.append([
            InlineKeyboardButton(f"{self.config.get_emoji('search')} New Search", callback_data="new_search"),
            InlineKeyboardButton(f"{self.config.get_emoji('home')} Main Menu", callback_data="main_menu")
        ])
        
        # 📨 SEND RESULTS
        await searching_msg.edit_text(
            found_msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        # ✨ ADD SUCCESS REACTION
        await self.reaction_manager.add_reaction(update.message, context.bot, "success")
        
        logger.info(f"🔍 Search: {user.id} - '{query}' - {len(books)} results")
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """📊 Premium Statistics Display"""
        user = update.effective_user
        
        # ⏳ CALCULATING ANIMATION
        stats_msg = await update.message.reply_text(
            f"{self.config.get_emoji('stats')} *Calculating statistics...*\n"
            f"{'▰' * 15}",
            parse_mode='Markdown'
        )
        
        # 📈 GET STATS
        stats = self.db.get_stats()
        
        # 🎨 FORMAT STATS
        stats_text = f"""
{self.config.get_emoji('trophy')} *BOT STATISTICS* {self.config.get_emoji('trophy')}

📊 *Overall Statistics:*
• 📚 Total Books: *{stats.get('total_books', 0):,}*
• 👥 Total Users: *{stats.get('total_users', 0):,}*
• 🔍 Total Searches: *{stats.get('total_searches', 0):,}*
• 📥 Total Downloads: *{stats.get('total_downloads', 0):,}*

📈 *Today's Activity:*
• 🔍 Searches: *{stats.get('today_searches', 0):,}*
• 📥 Downloads: *{stats.get('today_downloads', 0):,}*
• 👤 New Users: *{stats.get('today_new_users', 0):,}*

🏆 *Top Performers:*
        """
        
        # 🥇 TOP BOOKS
        if stats.get('top_books'):
            stats_text += f"\n{self.config.get_emoji('book')} *Popular Books:*"
            for i, book in enumerate(stats['top_books'][:3], 1):
                stats_text += f"\n{i}. {book['title'][:20]} ({book['downloads']} 📥)"
        
        # 👑 TOP USERS
        if stats.get('top_users'):
            stats_text += f"\n\n{self.config.get_emoji('crown')} *Active Users:*"
            for i, user_data in enumerate(stats['top_users'][:3], 1):
                stats_text += f"\n{i}. {user_data['username']} ({user_data['searches']}🔍/{user_data['downloads']}📥)"
        
        # ⏰ UPDATE TIME
        stats_text += f"\n\n{self.config.get_emoji('time')} *Last Updated:* {datetime.now().strftime('%H:%M:%S')}"
        stats_text += f"\n{self.config.get_emoji('calendar')} *Date:* {datetime.now().strftime('%Y-%m-%d')}"
        
        # 📨 SEND STATS
        await stats_msg.edit_text(stats_text, parse_mode='Markdown')
        
        logger.info(f"📊 Stats viewed by: {user.id}")
    
    async def categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """🏷️ Beautiful Categories Display"""
        categories_text = f"""
{self.config.get_emoji('category')} *BOOK CATEGORIES* {self.config.get_emoji('category')}

📚 Browse books by category:
        """
        
        # 🎨 CATEGORY KEYBOARD
        categories = [
            ("📚 Fiction", "fiction"),
            ("🔬 Science", "science"),
            ("💻 Technology", "technology"),
            ("📈 Business", "business"),
            ("🏥 Health", "health"),
            ("🎨 Arts", "arts"),
            ("📖 Education", "education"),
            ("🌍 Travel", "travel"),
            ("🍳 Cooking", "cooking"),
            ("🏋️ Fitness", "fitness"),
            ("🧘 Wellness", "wellness"),
            ("💰 Finance", "finance")
        ]
        
        keyboard = []
        row = []
        for i, (name, callback) in enumerate(categories, 1):
            row.append(InlineKeyboardButton(name, callback_data=f"cat_{callback}"))
            if i % 2 == 0:
                keyboard.append(row)
                row = []
        
        if row:
            keyboard.append(row)
        
        keyboard.append([
            InlineKeyboardButton(f"{self.config.get_emoji('home')} Main Menu", callback_data="main_menu"),
            InlineKeyboardButton(f"{self.config.get_emoji('search')} Search", callback_data="search")
        ])
        
        await update.message.reply_text(
            categories_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ℹ️ Premium Help Guide"""
        help_text = f"""
{self.config.get_emoji('info')} *PREMIUM BOOK BOT HELP GUIDE* {self.config.get_emoji('info')}

🎯 *Basic Commands:*
• /start - Start the bot
• /books <query> - Search books
• /categories - Browse categories
• /stats - View statistics
• /help - This help guide

🔍 *Advanced Search:*
• /books python programming
• /books author:rowling
• /books category:fiction
• /books harry potter pdf

👑 *Admin Commands:* (Owner only)
• /admin - Admin panel
• /addbook - Add new book
• /broadcast - Send announcement
• /lock - Lock the bot
• /unlock - Unlock the bot

🎨 *Features:*
• Beautiful UI with emojis
• Fast search results
• Direct downloads
• Reading statistics
• Category browsing
• Premium content

💡 *Pro Tips:*
1. Use specific keywords
2. Include author names
3. Try different categories
4. Check spelling
5. Request missing books

📞 *Support:*
For help, contact {self.config.OWNER_USERNAME}

✨ *Enjoy reading!* 📚
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """📖 About the Bot"""
        about_text = f"""
{self.config.get_emoji('gem')} *ABOUT PREMIUM BOOK BOT* {self.config.get_emoji('gem')}

🚀 *Version:* 2.0.0 Premium
📅 *Launched:* 2024
👨‍💻 *Developer:* {self.config.OWNER_USERNAME}
🤖 *Bot:* {self.config.BOT_USERNAME}

🌟 *Mission:*
To provide instant access to knowledge through books, making learning accessible to everyone.

📚 *Features:*
• Instant book search
• Thousands of titles
• Beautiful interface
• Fast downloads
• User statistics

🔧 *Technology:*
• Python 3.11
• Telegram Bot API
• SQLite Database
• Flask Web Server

🌐 *Website:* Coming Soon
📞 *Support:* {self.config.OWNER_USERNAME}

✨ *Thank you for using Premium Book Bot!*
        """
        
        await update.message.reply_text(about_text, parse_mode='Markdown')
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """💬 Handle regular text messages"""
        # Random reactions
        if random.random() < 0.4:
            await self.reaction_manager.add_reaction(update.message, context.bot, "random")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """🔘 Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "main_menu":
            await self.start(update, context)
        elif data == "search":
            await query.edit_message_text(
                f"{self.config.get_emoji('search')} *Search Books*\n\n"
                "Send me what you're looking for!\n\n"
                "Example: `python programming books`",
                parse_mode='Markdown'
            )
        elif data == "help":
            await self.help(update, context)
        elif data == "stats":
            await self.stats(update, context)
    
    def _format_size(self, size_bytes):
        """Format file size"""
        if not size_bytes:
            return "Unknown"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

# 🎯 SETUP FUNCTION
def setup_handlers(app, db, reaction_manager):
    """Setup all handlers"""
    handlers = PremiumHandlers(db, reaction_manager)
    handlers.register(app)
