import random
import asyncio
import logging
from datetime import datetime

from telegram import Bot, Message
from config import Config

logger = logging.getLogger(__name__)

class ReactionManager:
    """✨ Premium Reaction System"""
    
    def __init__(self):
        self.config = Config()
    
    async def add_reaction(self, message: Message, bot: Bot, reaction_type: str = "random"):
        """Add beautiful reactions"""
        try:
            if reaction_type == "random":
                if random.random() < 0.4:  # 40% chance
                    emoji = random.choice(self.config.REACTIONS)
                    await self._send_reaction(message, bot, emoji)
            
            elif reaction_type == "welcome":
                sequence = ["👋", "🌟", "🎉", "✨"]
                for emoji in sequence:
                    await self._send_reaction(message, bot, emoji)
                    await asyncio.sleep(0.3)
            
            elif reaction_type == "success":
                sequence = ["✅", "🎯", "🚀"]
                for emoji in sequence:
                    await self._send_reaction(message, bot, emoji)
                    await asyncio.sleep(0.4)
            
            elif reaction_type == "search":
                sequence = ["🔍", "📚", "✅"]
                for emoji in sequence:
                    await self._send_reaction(message, bot, emoji)
                    await asyncio.sleep(0.5)
        
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
            # Fallback to text if reactions not available
            pass

def format_message(text: str) -> str:
    """Format message with current time"""
    time_str = datetime.now().strftime('%H:%M:%S')
    return f"🕐 {time_str}\n\n{text}"
