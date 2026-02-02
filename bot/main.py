#!/usr/bin/env python3
"""
🎯 PREMIUM BOOK BOT - MAIN ENTRY POINT
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

from telegram.ext import Application

from config import Config
from bot.database import DatabaseManager
from bot.handlers import setup_handlers
from bot.utils import ReactionManager

# 🎨 COLORED LOGGING
class ColorFormatter(logging.Formatter):
    """Color formatter for logs"""
    COLORS = {
        'DEBUG': '\033[36m',     # CYAN
        'INFO': '\033[32m',      # GREEN
        'WARNING': '\033[33m',   # YELLOW
        'ERROR': '\033[31m',     # RED
        'CRITICAL': '\033[41m',  # RED BG
        'RESET': '\033[0m'       # RESET
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        message = super().format(record)
        return f"{color}{message}{self.COLORS['RESET']}"

def setup_logging():
    """Setup beautiful logging"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Console handler with colors
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(ColorFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(console)
    
    # File handler
    file_handler = logging.FileHandler('/tmp/bot.log')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

class PremiumBookBot:
    """🎯 Premium Book Bot Class"""
    
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        self.reaction_manager = ReactionManager()
        self.app = None
    
    async def initialize(self):
        """Initialize the bot with style"""
        try:
            # 🎯 SHOW BANNER
            print("\n" + "="*60)
            print(self.config.BANNER)
            print("="*60)
            print(f"🚀 Initializing Premium Book Bot...")
            print(f"👤 Bot: {self.config.BOT_USERNAME}")
            print(f"👑 Owner: {self.config.OWNER_USERNAME}")
            print("="*60 + "\n")
            
            # 🔑 CHECK BOT TOKEN
            if not self.config.BOT_TOKEN:
                logger.error("❌ CRITICAL: BOT_TOKEN not found in environment!")
                logger.error("💡 Please set BOT_TOKEN in Render Environment Variables")
                return False
            
            logger.info("✅ Bot token verified")
            
            # 💾 INITIALIZE DATABASE
            logger.info("💾 Initializing database...")
            self.db.initialize()
            logger.info("✅ Database ready")
            
            # 🤖 CREATE BOT APPLICATION
            logger.info("🤖 Building bot application...")
            self.app = Application.builder().token(self.config.BOT_TOKEN).build()
            
            # 🎮 SETUP HANDLERS
            logger.info("🎮 Setting up handlers...")
            setup_handlers(self.app, self.db, self.reaction_manager)
            logger.info("✅ Handlers configured")
            
            logger.info("✨ Bot initialization complete!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def start(self):
        """Start the bot"""
        if not await self.initialize():
            logger.error("❌ Cannot start bot due to initialization errors")
            return
        
        try:
            # 🚀 START BOT
            logger.info("🚀 Starting bot...")
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            
            # 🎉 STARTUP SUCCESS
            success_msg = f"""
            ╔══════════════════════════════════╗
            ║   🎉 BOT STARTED SUCCESSFULLY!   ║
            ╚══════════════════════════════════╝
            
            📊 Bot Information:
            • 🤖 Name: {self.config.BOT_NAME}
            • 👤 Username: {self.config.BOT_USERNAME}
            • 👑 Owner: {self.config.OWNER_USERNAME}
            • 🕐 Time: {datetime.now().strftime('%H:%M:%S')}
            • 📍 Status: {'🔓 ACTIVE' if not self.config.BOT_LOCKED else '🔒 LOCKED'}
            • 💬 DM Mode: {'✅ ENABLED' if self.config.DM_ENABLED else '❌ DISABLED'}
            
            🌐 Health Check: /health endpoint active
            📚 Books Ready: {self.db.get_stats().get('total_books', 0)}
            👥 Users: {self.db.get_stats().get('total_users', 0)}
            """
            
            logger.info(success_msg)
            
            # 📨 SEND STARTUP NOTIFICATION TO OWNER
            if self.config.OWNER_ID:
                try:
                    await self.app.bot.send_message(
                        chat_id=self.config.OWNER_ID,
                        text=f"""
✨ *Bot Deployment Successful!* ✨

🤖 *Bot:* {self.config.BOT_NAME}
🆔 *Username:* {self.config.BOT_USERNAME}
🕐 *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📍 *Status:* ✅ ACTIVE
📊 *Database:* {self.db.get_stats().get('total_books', 0)} books loaded

🚀 *Bot is now LIVE and ready to serve!*
📚 Users can start searching for books immediately.

🎯 *Next Steps:*
1. Add books using /addbook command
2. Check /stats for bot statistics
3. Test search with /books python

🔧 *Support:* Contact if any issues arise.
                        """,
                        parse_mode='Markdown'
                    )
                    logger.info("✅ Startup notification sent to owner")
                except Exception as e:
                    logger.warning(f"⚠️ Could not send startup notification: {e}")
            
            # ♾️ KEEP BOT RUNNING
            logger.info("⏳ Bot is now running and waiting for commands...")
            await asyncio.Event().wait()
            
        except Exception as e:
            logger.error(f"❌ Bot crashed: {e}")
            raise
    
    async def stop(self):
        """Stop the bot gracefully"""
        if self.app:
            logger.info("🛑 Stopping bot gracefully...")
            await self.app.stop()
            await self.app.shutdown()
            logger.info("✅ Bot stopped")

async def main():
    """Main entry point"""
    bot = PremiumBookBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Received interrupt signal")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
