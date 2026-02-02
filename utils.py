import random
import asyncio
import logging
from datetime import datetime

from telegram import Bot, Message
from config import Config

logger = logging.getLogger(__name__)

class ReactionManager:
    """Manage reactions on messages"""
    
    def __init__(self):
        self.config = Config()
    
    async def add_reaction(self, message: Message, bot: Bot, reaction_type: str = "random"):
        """Add reaction to message"""
        try:
            if reaction_type == "random":
                if random.random() < 0.4:  # 40% chance
                    emoji = random.choice(self.config.REACTIONS)
                    await self._send_reaction(message, bot, emoji)
            
            elif reaction_type == "welcome":
                emojis = ["👋", "🌟", "🎉", "✨"]
                for emoji in emojis:
                    await self._send_reaction(message, bot, emoji)
                    await asyncio.sleep(0.3)
            
            elif reaction_type == "success":
                emojis = ["✅", "🎯", "🚀"]
                for emoji in emojis:
                    await self._send_reaction(message, bot, emoji)
                    await asyncio.sleep(0.4)
            
            elif reaction_type == "error":
                await self._send_reaction(message, bot, "⚠️")
            
            elif reaction_type == "download":
                emojis = ["📥", "📖", "🎉"]
                for emoji in emojis:
                    await self._send_reaction(message, bot, emoji)
                    await asyncio.sleep(0.4)
        
        except Exception as e:
            logger.debug(f"Reaction skipped: {e}")
    
    async def _send_reaction(self, message: Message, bot: Bot, emoji: str):
        """Send reaction to message"""
        try:
            await bot.set_message_reaction(
                chat_id=message.chat_id,
                message_id=message.message_id,
                reaction=[{"type": "emoji", "emoji": emoji}],
                is_big=True
            )
        except:
            # Reaction API not available
            pass

def format_book_info(book):
    """Format book information for display"""
    title = book.get('title', 'Unknown Title')
    author = book.get('author', 'Unknown Author')
    description = book.get('description', 'No description available.')
    file_size = book.get('file_size', 0)
    category = book.get('category', 'General')
    downloads = book.get('download_count', 0)
    
    # Format file size
    size_str = _format_size(file_size)
    
    text = f"""
📚 *{title}*

👤 *Author:* {author}
📦 *Size:* {size_str}
🏷️ *Category:* {category}
📥 *Downloads:* {downloads:,}

📝 *Description:*
{description[:200]}{'...' if len(description) > 200 else ''}

✨ *Features:*
• Instant download
• High quality
• Mobile friendly
• Searchable text
    """
    
    if book.get('is_premium'):
        text += "\n\n⭐ *PREMIUM CONTENT* - Exclusive access!"
    
    return text

def format_search_results(books, query):
    """Format search results for display"""
    text = f"""
🔍 *Search Results for:* `{query}`

📚 *Found {len(books)} books*

📖 *Top Results:*
    """
    
    for i, book in enumerate(books[:5], 1):
        emoji = Config.get_emoji('star') if book.get('is_premium') else Config.get_emoji('book')
        text += f"\n{i}. {emoji} *{book['title'][:30]}*"
        text += f"\n   👤 {book['author'][:20]} | 📦 {_format_size(book.get('file_size', 0))}"
    
    if len(books) > 5:
        text += f"\n\n📄 *+ {len(books) - 5} more books...*"
    
    text += f"\n\n{Config.get_emoji('time')} *Search Time:* {datetime.now().strftime('%H:%M:%S')}"
    
    return text

def _format_size(size_bytes):
    """Format file size in human readable format"""
    if not size_bytes:
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"