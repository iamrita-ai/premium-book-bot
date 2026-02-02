#!/usr/bin/env python3
"""
🤖 PREMIUM TELEGRAM BOOK BOT
With all premium features and beautiful UI
"""

import os
import sys
import logging
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Import after logging setup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Import local modules
from config import Config
from database import Database
from handlers import setup_handlers
from utils import ReactionManager

class PremiumBookBot:
    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.reaction_manager = ReactionManager()
        self.app = None
    
    async def initialize(self):
        """Initialize the bot"""
        try:
            # Validate configuration
            if not self.config.BOT_TOKEN:
                raise ValueError("BOT_TOKEN not set in environment variables")
            
            logger.info("=" * 60)
            logger.info("🚀 PREMIUM BOOK BOT - STARTING")
            logger.info("=" * 60)
            
            logger.info(f"🤖 Bot: {self.config.BOT_USERNAME}")
            logger.info(f"👑 Owner: {self.config.OWNER_ID}")
            logger.info(f"📚 Database Channel: {self.config.DATABASE_CHANNEL_ID}")
            
            # Initialize database
            self.db.initialize()
            logger.info("✅ Database initialized")
            
            # Create bot application
            self.app = Application.builder().token(self.config.BOT_TOKEN).build()
            
            # Setup handlers
            setup_handlers(self.app, self.db, self.reaction_manager)
            logger.info("✅ Handlers setup complete")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def start(self):
        """Start the bot"""
        if not await self.initialize():
            return
        
        try:
            # Start the bot
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            
            # 🎉 BOT STARTED SUCCESSFULLY
            success_msg = f"""
            ╔══════════════════════════════════╗
            ║   🎉 BOT STARTED SUCCESSFULLY!   ║
            ╚══════════════════════════════════╝
            
            📊 Bot Information:
            • 🤖 Username: {self.config.BOT_USERNAME}
            • 👑 Owner ID: {self.config.OWNER_ID}
            • 🕐 Time: {datetime.now().strftime('%H:%M:%S')}
            • 📍 Status: ACTIVE 🟢
            • 💬 DM Mode: {'✅ ENABLED' if self.config.DM_ENABLED else '❌ DISABLED'}
            • 🔓 Locked: {'❌ NO' if not self.config.BOT_LOCKED else '✅ YES'}
            
            📚 Database:
            • Books: {self.db.get_stats()['total_books']}
            • Users: {self.db.get_stats()['total_users']}
            
            🚀 Bot is now responding to commands!
            """
            
            logger.info(success_msg)
            
            # Send notification to owner
            if self.config.OWNER_ID:
                try:
                    await self.app.bot.send_message(
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
Users can use:
• `/start` - Welcome message
• `/books <query>` - Search books
• `/help` - Get help

🔧 *Environment:* Render
🌐 *Health:* https://your-app.onrender.com/health
                        """,
                        parse_mode='Markdown'
                    )
                    logger.info("✅ Startup notification sent to owner")
                except Exception as e:
                    logger.warning(f"⚠️ Could not notify owner: {e}")
            
            # Keep bot running
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
        logger.info("⚠️ Received interrupt signal")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())