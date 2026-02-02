import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "")
    
    # Admin
    OWNER_ID = int(os.getenv("OWNER_ID", 0))
    OWNER_USERNAME = os.getenv("OWNER_USERNAME", "")
    
    # Channels & Groups
    DATABASE_CHANNEL_ID = int(os.getenv("DATABASE_CHANNEL_ID", 0))
    REQUEST_GROUP_ID = os.getenv("REQUEST_GROUP_ID", "")
    LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))
    FORCE_SUB_CHANNEL = os.getenv("FORCE_SUB_CHANNEL", "")
    
    # Bot Settings
    BOT_LOCKED = False
    DM_ENABLED = False
    MAINTENANCE = False
    
    # Database
    DB_PATH = "/tmp/book_bot.db"
    BACKUP_PATH = "/tmp/backups"
    
    # Search Settings
    RESULTS_PER_PAGE = 10
    MAX_RESULTS = 50
    SEARCH_TIMEOUT = 30
    
    # UI Settings
    REACTION_CHANCE = 0.4
    REACTION_EMOJIS = ["🔥", "⭐", "🎯", "⚡", "❤️", "👍", "👏", "📚", "✨", "💫", "🚀", "💯"]
    
    # Performance
    MAX_CONCURRENT_SEARCHES = 5
    CACHE_TTL = 300
    
    # Flask Server
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", 10000))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        missing = []
        if not cls.BOT_TOKEN:
            missing.append("BOT_TOKEN")
        if not cls.OWNER_ID:
            missing.append("OWNER_ID")
        if not cls.DATABASE_CHANNEL_ID:
            missing.append("DATABASE_CHANNEL_ID")
        
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")
        
        return True
