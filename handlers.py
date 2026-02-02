import logging
import random
from datetime import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from config import Config
from keyboards import create_main_menu, create_search_results_keyboard, create_book_details_keyboard
from utils import ReactionManager, format_book_info, format_search_results

logger = logging.getLogger(__name__)

def setup_handlers(app, db, reaction_manager):
    """Setup all bot handlers"""
    
    # 🎯 START COMMAND
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        # Add user to database
        db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Welcome message
        welcome_text = f"""
{Config.get_emoji('crown')} *WELCOME TO PREMIUM BOOK BOT!* {Config.get_emoji('crown')}

👋 *Hello {user.first_name}!* I'm your personal library assistant.

{Config.get_emoji('book')} *What I Offer:*
• 🔍 *Smart Search* - Find any book instantly
• 📚 *Vast Collection* - Thousands of books
• 🚀 *Fast Downloads* - Direct from Telegram
• ⭐ *Premium Content* - Exclusive books
• 📊 *Reading Stats* - Track your journey

{Config.get_emoji('rocket')} *Get Started:*
1. Use `/books <query>` to search
2. Browse `/categories` by genre
3. Check `/stats` for bot insights
4. Use `/help` for guidance

{Config.get_emoji('sparkle')} *Pro Tips:*
• Use specific keywords
• Include author names
• Try different categories
• Request missing books

📞 *Support:* {Config.OWNER_USERNAME}
        """
        
        # Create keyboard
        keyboard = create_main_menu(user.id == Config.OWNER_ID)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        # Add reaction
        await reaction_manager.add_reaction(update.message, context.bot, "welcome")
        
        logger.info(f"👤 User started: {user.id} - {user.username}")
    
    # 🔍 BOOKS COMMAND
    async def books(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if Config.BOT_LOCKED:
            await update.message.reply_text(
                f"{Config.get_emoji('lock')} *Bot is currently under maintenance.*\n"
                f"Please try again later.\n\n"
                f"📞 Contact: {Config.OWNER_USERNAME}",
                parse_mode='Markdown'
            )
            return
        
        user = update.effective_user
        
        if not context.args:
            await update.message.reply_text(
                f"{Config.get_emoji('search')} *Book Search*\n\n"
                "Please specify what you're looking for:\n"
                "Example: `/books python programming`\n"
                "Or: `/books harry potter`\n\n"
                "💡 *Tips:*\n"
                "• Use keywords\n"
                "• Specify author\n"
                "• Use category names",
                parse_mode='Markdown'
            )
            return
        
        query = " ".join(context.args)
        
        # Show typing indicator
        await context.bot.send_chat_action(update.effective_chat.id, 'typing')
        
        # Search books
        books = db.search_books(query, limit=Config.MAX_RESULTS)
        
        # Update user stats
        db.update_user_stats(user.id, 'search')
        
        if not books:
            await update.message.reply_text(
                f"{Config.get_emoji('warning')} *No books found!*\n\n"
                f"Couldn't find books for: `{query}`\n\n"
                "💡 *Suggestions:*\n"
                "• Check spelling\n"
                "• Try different keywords\n"
                "• Request the book using /request",
                parse_mode='Markdown'
            )
            await reaction_manager.add_reaction(update.message, context.bot, "error")
            return
        
        # Format results
        text = format_search_results(books, query)
        
        # Create keyboard
        keyboard = create_search_results_keyboard(books[:5], page=0, total_pages=1)
        
        await update.message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        await reaction_manager.add_reaction(update.message, context.bot, "success")
        
        logger.info(f"🔍 Search: {user.id} - '{query}' - {len(books)} results")
    
    # 📊 STATS COMMAND
    async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
        stats = db.get_stats()
        
        text = f"""
{Config.get_emoji('stats')} *Bot Statistics* {Config.get_emoji('stats')}

📊 *Overall:*
• 📚 Total Books: *{stats['total_books']:,}*
• 👥 Total Users: *{stats['total_users']:,}*
• 🔍 Total Searches: *{stats['total_searches']:,}*
• 📥 Total Downloads: *{stats['total_downloads']:,}*

{Config.get_emoji('time')} *Last Updated:* {datetime.now().strftime('%H:%M:%S')}
{Config.get_emoji('calendar')} *Date:* {datetime.now().strftime('%Y-%m-%d')}
        """
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    # ℹ️ HELP COMMAND
    async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = f"""
{Config.get_emoji('info')} *Premium Book Bot Help Guide* {Config.get_emoji('info')}

🎯 *Basic Commands:*
• /start - Start the bot
• /books <query> - Search books
• /help - Show this help
• /stats - View statistics

🔍 *Search Examples:*
• `/books python programming`
• `/books harry potter`
• `/books self help`

👑 *Admin Commands:* (Owner only)
• /addbook - Add new book
• /broadcast - Send announcement
• /lock - Lock the bot
• /unlock - Unlock the bot

📞 *Support:* {Config.OWNER_USERNAME}

✨ *Enjoy reading!* 📚
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    # 📚 CATEGORIES COMMAND
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
        
        keyboard.append([
            InlineKeyboardButton(f"{Config.get_emoji('home')} Main Menu", callback_data="main_menu"),
            InlineKeyboardButton(f"{Config.get_emoji('search')} Search", callback_data="search")
        ])
        
        await update.message.reply_text(
            f"{Config.get_emoji('category')} *Book Categories*\n\n"
            "Select a category to browse books:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # 👑 ADMIN COMMAND
    async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        if user.id != Config.OWNER_ID:
            await update.message.reply_text(f"{Config.get_emoji('error')} Admin access required!")
            return
        
        keyboard = [
            [InlineKeyboardButton(f"{Config.get_emoji('stats')} System Stats", callback_data="admin_stats")],
            [InlineKeyboardButton(f"{Config.get_emoji('book')} Add Book", callback_data="admin_add_book")],
            [InlineKeyboardButton(f"{Config.get_emoji('user')} User Management", callback_data="admin_users")],
            [InlineKeyboardButton(f"{Config.get_emoji('settings')} Bot Settings", callback_data="admin_settings")],
            [InlineKeyboardButton(f"{Config.get_emoji('home')} Main Menu", callback_data="main_menu")]
        ]
        
        await update.message.reply_text(
            f"{Config.get_emoji('crown')} *Admin Panel*\n\n"
            "Manage your bot and books:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # 📤 ADDBOOK COMMAND
    async def addbook(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        if user.id != Config.OWNER_ID:
            await update.message.reply_text(f"{Config.get_emoji('error')} Admin only command!")
            return
        
        if not update.message.reply_to_message or not update.message.reply_to_message.document:
            await update.message.reply_text(
                f"{Config.get_emoji('book')} *Add Book*\n\n"
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
        
        # Parse command arguments
        args = context.args
        if args:
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
            'category': 'General'
        }
        
        if db.add_book(book_data):
            await update.message.reply_text(f"✅ Book added: *{title}*", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Failed to add book")
    
    # 💬 HANDLE TEXT MESSAGES
    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Random reactions
        if random.random() < 0.4:
            await reaction_manager.add_reaction(update.message, context.bot, "random")
    
    # 🔘 HANDLE CALLBACK QUERIES
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "main_menu":
            keyboard = create_main_menu(update.effective_user.id == Config.OWNER_ID)
            await query.edit_message_text(
                f"{Config.get_emoji('home')} *Main Menu*\n\n"
                "Select an option:",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        
        elif data == "search":
            await query.edit_message_text(
                f"{Config.get_emoji('search')} *Search Books*\n\n"
                "Send me what you're looking for!\n\n"
                "Example: `python programming books`",
                parse_mode='Markdown'
            )
        
        elif data.startswith("book_"):
            book_id = data[5:]
            book = db.get_book(book_id)
            
            if book:
                text = format_book_info(book)
                keyboard = create_book_details_keyboard(book_id, update.effective_user.id == Config.OWNER_ID)
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                await query.answer("Book not found!", show_alert=True)
        
        elif data.startswith("download_"):
            book_id = data[9:]
            book = db.get_book(book_id)
            
            if book:
                # Update stats
                db.update_user_stats(update.effective_user.id, 'download')
                
                # Send file
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=book['file_id'],
                    caption=f"📚 *{book['title']}*\n👤 {book['author']}\n\nEnjoy reading! 📖"
                )
                
                await query.answer("✅ Book sent!", show_alert=True)
                await reaction_manager.add_reaction(query.message, context.bot, "download")
            else:
                await query.answer("❌ Book not available!", show_alert=True)
    
    # Register all handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("books", books))
    app.add_handler(CommandHandler("search", books))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("categories", categories))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("addbook", addbook))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    logger.info("✅ All handlers registered")