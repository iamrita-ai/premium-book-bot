import logging
import asyncio
from datetime import datetime
from typing import Optional

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from config import Config
from .database import DatabaseManager
from .keyboards import KeyboardBuilder
from .utils import ReactionManager, MessageFormatter, ProgressIndicator

logger = logging.getLogger(__name__)

class BotHandlers:
    """Premium bot handlers with all features"""
    
    def __init__(self, db: DatabaseManager, reaction_manager: ReactionManager):
        self.config = Config()
        self.db = db
        self.reaction_manager = reaction_manager
        self.active_searches = {}
        
    def register_handlers(self, app: Application):
        """Register all bot handlers"""
        
        # Command handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("help", self.help))
        app.add_handler(CommandHandler("books", self.search_books))
        app.add_handler(CommandHandler("search", self.search_books))
        app.add_handler(CommandHandler("stats", self.stats))
        app.add_handler(CommandHandler("categories", self.categories))
        
        # Admin commands
        app.add_handler(CommandHandler("admin", self.admin_panel))
        app.add_handler(CommandHandler("addbook", self.add_book))
        app.add_handler(CommandHandler("broadcast", self.broadcast))
        app.add_handler(CommandHandler("lock", self.lock_bot))
        app.add_handler(CommandHandler("unlock", self.unlock_bot))
        
        # Message handlers
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        app.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        
        # Callback query handlers
        app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        logger.info("✅ Handlers registered successfully")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        chat = update.effective_chat
        
        # Add user to database
        self.db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            is_admin=(user.id == self.config.OWNER_ID)
        )
        
        # Check force subscription
        if self.config.FORCE_SUB_CHANNEL and chat.type == 'private':
            try:
                channel = self.config.FORCE_SUB_CHANNEL.lstrip('@')
                member = await context.bot.get_chat_member(f"@{channel}", user.id)
                if member.status not in ['member', 'administrator', 'creator']:
                    keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{channel}")]]
                    await update.message.reply_text(
                        "📚 *Welcome to Premium Book Bot!*\n\n"
                        "Please join our channel to access all features:\n"
                        f"👉 @{channel}",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
                    return
            except Exception as e:
                logger.error(f"Subscription check error: {e}")
        
        # Send welcome message
        welcome_text = f"""
🌟 *Welcome {user.first_name}!* 🌟

📚 *Premium Book Bot* is your personal library assistant!

✨ **Features:**
• 🔍 Smart book search
• 📚 Thousands of books
• 🚀 Fast downloads
• ⭐ Premium content
• 📊 Reading statistics

🎯 **Get Started:**
1. Use `/books <query>` to search
2. Browse `/categories`
3. Check `/stats`

📖 Happy reading! 😊
"""
        
        keyboard = KeyboardBuilder.main_menu(
            user_id=user.id,
            is_admin=(user.id == self.config.OWNER_ID)
        )
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        # Add welcome reaction
        await self.reaction_manager.add_reaction(update.message, context.bot, "welcome")
        
        logger.info(f"User started: {user.id} - {user.username}")
    
    async def search_books(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /books command"""
        if self.config.BOT_LOCKED:
            await update.message.reply_text("🔒 Bot is currently under maintenance. Please try again later.")
            return
        
        user = update.effective_user
        
        if not context.args:
            await update.message.reply_text(
                "🔍 *Book Search*\n\n"
                "Please specify what you're looking for:\n"
                "Example: `/books python programming`\n"
                "Or: `/books author:rowling`\n\n"
                "💡 *Tips:*\n"
                "• Use keywords\n"
                "• Specify author\n"
                "• Use category names",
                parse_mode='Markdown'
            )
            return
        
        query = " ".join(context.args)
        
        # Show typing indicator
        await ProgressIndicator.typing_indicator(update.effective_chat.id, context.bot)
        
        # Show progress
        progress_msg = await ProgressIndicator.show_progress(
            update.message, context.bot, "🔍 Searching"
        )
        
        # Search books
        books = self.db.search_books(query, limit=10)
        
        # Update user stats
        self.db.update_user_stats(user.id, 'search')
        
        if not books:
            await progress_msg.edit_text(
                "❌ *No books found!*\n\n"
                f"Couldn't find books for: `{query}`\n\n"
                "💡 *Suggestions:*\n"
                "• Check spelling\n"
                "• Try different keywords\n"
                "• Request the book using /request",
                parse_mode='Markdown'
            )
            await self.reaction_manager.add_reaction(update.message, context.bot, "error")
            return
        
        # Store search results
        search_id = f"{user.id}_{int(datetime.now().timestamp())}"
        self.active_searches[search_id] = {
            'books': books,
            'query': query,
            'page': 0
        }
        
        # Format results
        text = f"🔍 *Search Results for:* `{query}`\n\n"
        text += f"📚 *Found {len(books)} books*\n\n"
        
        for i, book in enumerate(books[:5], 1):
            emoji = "⭐" if book.get('is_premium') else "📖"
            text += f"{i}. {emoji} *{book['title'][:30]}*\n"
            text += f"   👤 {book['author'][:20]}\n\n"
        
        if len(books) > 5:
            text += f"*+ {len(books) - 5} more books...*\n"
        
        # Create keyboard
        total_pages = (len(books) + 4) // 5  # 5 books per page
        keyboard = KeyboardBuilder.search_results(
            results=books[:5],
            page=0,
            total_pages=total_pages
        )
        
        await progress_msg.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await self.reaction_manager.add_reaction(update.message, context.bot, "search")
        
        logger.info(f"Search: {user.id} - {query} - {len(books)} results")
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user = update.effective_user
        
        # Show progress
        progress_msg = await ProgressIndicator.show_progress(
            update.message, context.bot, "📊 Calculating"
        )
        
        # Get stats
        stats = self.db.get_stats()
        
        # Format stats
        text = MessageFormatter.format_stats(stats)
        
        await progress_msg.edit_text(text, parse_mode='Markdown')
    
    async def categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /categories command"""
        keyboard = KeyboardBuilder.categories()
        
        await update.message.reply_text(
            "📚 *Browse Categories*\n\n"
            "Select a category to browse books:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command"""
        user = update.effective_user
        
        if user.id != self.config.OWNER_ID:
            await update.message.reply_text("❌ Admin access required!")
            return
        
        keyboard = KeyboardBuilder.admin_panel()
        
        await update.message.reply_text(
            "👑 *Admin Panel*\n\n"
            "Manage your bot and books:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user = update.effective_user
        
        logger.info(f"Callback: {user.id} - {data}")
        
        # Handle different callbacks
        if data == "main_menu":
            keyboard = KeyboardBuilder.main_menu(
                user_id=user.id,
                is_admin=(user.id == self.config.OWNER_ID)
            )
            await query.edit_message_text(
                "🏠 *Main Menu*\n\n"
                "Select an option:",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        
        elif data == "search":
            await query.edit_message_text(
                "🔍 *Search Books*\n\n"
                "Send me what you're looking for!\n\n"
                "Example:\n"
                "• `python programming`\n"
                "• `harry potter`\n"
                "• `self help books`",
                parse_mode='Markdown'
            )
        
        elif data == "categories":
            keyboard = KeyboardBuilder.categories()
            await query.edit_message_text(
                "📚 *Browse Categories*",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        
        elif data.startswith("book_"):
            book_id = data[5:]
            book = self.db.get_book(book_id)
            
            if book:
                text = MessageFormatter.format_book(book)
                keyboard = KeyboardBuilder.book_details(
                    book_id=book_id,
                    is_owner=(user.id == self.config.OWNER_ID)
                )
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                await query.answer("Book not found!", show_alert=True)
        
        elif data.startswith("download_"):
            book_id = data[9:]
            book = self.db.get_book(book_id)
            
            if book:
                # Update download count
                self.db.update_user_stats(user.id, 'download')
                
                # Send file
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=book['file_id'],
                    caption=f"📚 *{book['title']}*\n👤 {book['author']}\n\nEnjoy reading! 📖"
                )
                
                await query.answer("✅ Book sent!", show_alert=True)
                await self.reaction_manager.add_reaction(query.message, context.bot, "download")
            else:
                await query.answer("❌ Book not available!", show_alert=True)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        # Random reactions
        await self.reaction_manager.add_reaction(update.message, context.bot, "random")
    
    async def add_book(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /addbook command - Admin only"""
        user = update.effective_user
        
        if user.id != self.config.OWNER_ID:
            await update.message.reply_text("❌ Admin only command!")
            return
        
        if not update.message.reply_to_message or not update.message.reply_to_message.document:
            await update.message.reply_text(
                "📤 *Add Book*\n\n"
                "Reply to a document with:\n"
                "`/addbook Title by Author`\n\n"
                "Example:\n"
                "Reply to PDF → `/addbook Python Guide by John Doe`",
                parse_mode='Markdown'
            )
            return
        
        reply = update.message.reply_to_message
        document = reply.document
        
        # Extract metadata
        title = document.file_name or "Unknown"
        
        # Parse command arguments for title and author
        args = context.args
        if args:
            # Try to parse "Title by Author" format
            import re
            full_text = " ".join(args)
            match = re.match(r'(.+?)\s+by\s+(.+)', full_text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                author = match.group(2).strip()
            else:
                title = full_text
                author = "Unknown"
        else:
            author = "Unknown"
        
        # Add to database
        book_data = {
            'title': title,
            'author': author,
            'file_id': document.file_id,
            'file_type': document.mime_type or 'document',
            'file_size': document.file_size,
            'added_by': user.id
        }
        
        if self.db.add_book(book_data):
            await update.message.reply_text(f"✅ Book added: *{title}*", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Failed to add book (might already exist)")
    
    async def broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /broadcast command - Admin only"""
        user = update.effective_user
        
        if user.id != self.config.OWNER_ID:
            await update.message.reply_text("❌ Admin only command!")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: `/broadcast Your message here`", parse_mode='Markdown')
            return
        
        message = " ".join(context.args)
        
        # Get all users
        # Implementation would go here
        await update.message.reply_text("📢 Broadcast feature coming soon!")
    
    async def lock_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lock the bot - Admin only"""
        user = update.effective_user
        
        if user.id != self.config.OWNER_ID:
            await update.message.reply_text("❌ Admin only command!")
            return
        
        self.config.BOT_LOCKED = True
        await update.message.reply_text("🔒 Bot locked successfully!")
    
    async def unlock_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unlock the bot - Admin only"""
        user = update.effective_user
        
        if user.id != self.config.OWNER_ID:
            await update.message.reply_text("❌ Admin only command!")
            return
        
        self.config.BOT_LOCKED = False
        await update.message.reply_text("🔓 Bot unlocked successfully!")
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📖 *Premium Book Bot Help Guide*

🎯 *Basic Commands:*
• `/start` - Start the bot
• `/books <query>` - Search for books
• `/categories` - Browse by category
• `/stats` - View bot statistics
• `/help` - This help message

🔍 *Search Examples:*
• `/books python programming`
• `/books harry potter`
• `/books self help`
• `/books author:rowling`

👑 *Admin Commands:* (Owner only)
• `/admin` - Admin panel
• `/addbook` - Add new book
• `/broadcast` - Send announcement
• `/lock` - Lock the bot
• `/unlock` - Unlock the bot

📱 *Interactive Features:*
• Inline keyboards for navigation
• Book previews with details
• Download with one click
• Reading statistics

💡 *Tips:*
• Use specific keywords
• Check spelling
• Use author names
• Browse categories for inspiration

📞 *Support:* Contact @{owner} for help
""".format(owner=self.config.OWNER_USERNAME or "the admin")
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
