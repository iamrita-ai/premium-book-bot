#!/usr/bin/env python3
"""
Main bot module - Premium Telegram Book Bot
"""

import asyncio
import logging
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram.ext import Application

from config import Config
from .database import DatabaseManager
from .handlers import BotHandlers
from .utils import ReactionManager

logger = logging.getLogger(__name__)

class PremiumBookBot:
    """Premium Book Bot Main Class"""
    
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        self.reaction_manager = ReactionManager()
        self.app = None
    
    async def initialize(self):
        """Initialize the bot"""
        try:
            # Validate configuration
            self.config.validate()
            
            logger.info("🚀 Initializing Premium Book Bot...")
            
            # Initialize database
            self.db.initialize()
            logger.info("✅ Database initialized")
            
            # Create bot application
            self.app = Application.builder().token(self.config.BOT_TOKEN).build()
            
            # Initialize handlers
            handlers = BotHandlers(self.db, self.reaction_manager)
            handlers.register_handlers(self.app)
            
            logger.info("✅ Bot initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def start(self):
        """Start the bot"""
        if not await self.initialize():
            return
        
        try:
            # Start bot
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            
            logger.info("🤖 Bot is now running!")
            logger.info(f"👤 Bot username: @{self.config.BOT_USERNAME}")
            logger.info(f"👑 Owner ID: {self.config.OWNER_ID}")
            
            # Send startup notification to owner
            if self.config.OWNER_ID and self.app.bot:
                try:
                    await self.app.bot.send_message(
                        chat_id=self.config.OWNER_ID,
                        text=f"✅ *Bot Started Successfully!*\n\n"
                             f"• Time: {self._current_time()}\n"
                             f"• Status: {'🔒 Locked' if self.config.BOT_LOCKED else '✅ Active'}\n"
                             f"• Mode: {'💬 DM Enabled' if self.config.DM_ENABLED else '👥 Groups Only'}\n"
                             f"• Books: {self.db.get_stats().get('total_books', 0)}\n"
                             f"• Users: {self.db.get_stats().get('total_users', 0)}\n\n"
                             f"✨ Premium Book Bot is LIVE!",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.warning(f"Could not send startup notification: {e}")
            
            # Keep bot running
            await asyncio.Event().wait()
            
        except Exception as e:
            logger.error(f"❌ Bot crashed: {e}")
            raise
    
    def _current_time(self):
        """Get current time string"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    async def stop(self):
        """Stop the bot gracefully"""
        if self.app:
            await self.app.stop()
            await self.app.shutdown()
        logger.info("🛑 Bot stopped")

async def main():
    """Main function"""
    # Configure logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/tmp/bot.log')
        ]
    )
    
    logger.info("=" * 60)
    logger.info("📚 PREMIUM TELEGRAM BOOK BOT")
    logger.info("=" * 60)
    
    # Create and run bot
    bot = PremiumBookBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
