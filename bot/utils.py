import random
import asyncio
import logging
from datetime import datetime
from typing import Optional
from telegram import Bot, Message, Update
from config import Config

logger = logging.getLogger(__name__)

class ReactionManager:
    """Premium Reaction System with animations"""
    
    def __init__(self):
        self.config = Config()
        self.reaction_history = {}
    
    async def add_reaction(self, message: Message, bot: Bot, reaction_type: str = "random"):
        """Add animated reaction to message"""
        try:
            if reaction_type == "random":
                if random.random() < self.config.REACTION_CHANCE:
                    emoji = random.choice(self.config.REACTION_EMOJIS)
                    await self._send_reaction(message, bot, emoji)
            
            elif reaction_type == "welcome":
                emojis = ["👋", "🌟", "🎉"]
                for emoji in emojis:
                    await self._send_reaction(message, bot, emoji)
                    await asyncio.sleep(0.3)
            
            elif reaction_type == "search":
                sequence = ["🔍", "📚", "✅"]
                for emoji in sequence:
                    await self._send_reaction(message, bot, emoji)
                    await asyncio.sleep(0.5)
            
            elif reaction_type == "download":
                sequence = ["📥", "📖", "🎉"]
                for emoji in sequence:
                    await self._send_reaction(message, bot, emoji)
                    await asyncio.sleep(0.4)
            
            elif reaction_type == "error":
                await self._send_reaction(message, bot, "⚠️")
            
        except Exception as e:
            logger.error(f"Reaction error: {e}")
    
    async def _send_reaction(self, message: Message, bot: Bot, emoji: str):
        """Send reaction to message"""
        try:
            await bot.set_message_reaction(
                chat_id=message.chat_id,
                message_id=message.message_id,
                reaction=[{"type": "emoji", "emoji": emoji}],
                is_big=True
            )
        except Exception as e:
            # Fallback to text reaction if reaction API not available
            if "not enough rights" not in str(e):
                logger.warning(f"Could not add reaction: {e}")

class MessageFormatter:
    """Premium message formatting with emojis and styling"""
    
    @staticmethod
    def format_book(book: dict) -> str:
        """Format book information beautifully"""
        title = book.get('title', 'Unknown Title')
        author = book.get('author', 'Unknown Author')
        file_size = book.get('file_size', 0)
        rating = book.get('rating', 0.0)
        downloads = book.get('download_count', 0)
        
        # Format file size
        size_str = MessageFormatter._format_size(file_size)
        
        # Create stars for rating
        stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
        
        text = f"""
📚 *{title}*

👤 **Author:** {author}
📦 **Size:** {size_str}
⭐ **Rating:** {stars} ({rating}/5)
📥 **Downloads:** {downloads:,}

"""
        
        if book.get('description'):
            text += f"📝 *Description:*\n{book['description'][:200]}...\n\n"
        
        if book.get('category'):
            text += f"🏷️ **Category:** {book['category']}\n"
        
        if book.get('tags'):
            tags = book['tags'] if isinstance(book['tags'], list) else []
            if tags:
                text += f"🔖 **Tags:** {', '.join(tags[:5])}\n"
        
        if book.get('is_premium'):
            text += "\n🌟 *PREMIUM CONTENT*"
        
        return text
    
    @staticmethod
    def format_stats(stats: dict) -> str:
        """Format bot statistics"""
        text = f"""
📊 *Bot Statistics*

📚 **Total Books:** {stats.get('total_books', 0):,}
👥 **Total Users:** {stats.get('total_users', 0):,}

📈 **Today:**
   🔍 Searches: {stats.get('today_searches', 0):,}
   📥 Downloads: {stats.get('today_downloads', 0):,}
   👤 New Users: {stats.get('today_new_users', 0):,}

🏆 **Top Books:**
"""
        
        for i, book in enumerate(stats.get('top_books', [])[:3], 1):
            text += f"{i}. {book['title'][:20]} ({book['downloads']} 📥)\n"
        
        text += "\n👑 **Top Users:**\n"
        for i, user in enumerate(stats.get('top_users', [])[:3], 1):
            text += f"{i}. {user['username']} ({user['searches']}🔍/{user['downloads']}📥)\n"
        
        text += f"\n🕐 Last Updated: {datetime.now().strftime('%H:%M:%S')}"
        
        return text
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB']
        size = float(size_bytes)
        
        for unit in units:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        
        return f"{size:.1f} TB"

class ProgressIndicator:
    """Animated progress indicators"""
    
    @staticmethod
    async def show_progress(message: Message, bot: Bot, text: str = "Processing"):
        """Show animated progress"""
        progress_chars = ["▰", "▱"]
        frames = 6
        
        status_msg = await message.reply_text(f"{text}...")
        
        for i in range(frames):
            progress = progress_chars[0] * (i + 1) + progress_chars[1] * (frames - i - 1)
            try:
                await status_msg.edit_text(f"{text} {progress}")
            except:
                pass
            await asyncio.sleep(0.3)
        
        return status_msg
    
    @staticmethod
    async def typing_indicator(chat_id: int, bot: Bot, duration: float = 1.0):
        """Show typing indicator"""
        await bot.send_chat_action(chat_id, 'typing')
        await asyncio.sleep(duration)
