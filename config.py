import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 🔑 REQUIRED - Set in Render Environment
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    # 👑 ADMIN
    OWNER_ID = int(os.getenv("OWNER_ID", 0))
    OWNER_USERNAME = os.getenv("OWNER_USERNAME", "@Admin")
    
    # 📚 BOT INFO
    BOT_USERNAME = os.getenv("BOT_USERNAME", "@PremiumBookBot")
    BOT_NAME = "📚 Premium Book Bot"
    
    # 🏪 CHANNELS & GROUPS
    DATABASE_CHANNEL_ID = int(os.getenv("DATABASE_CHANNEL_ID", 0))
    REQUEST_GROUP = os.getenv("REQUEST_GROUP", "@BookRequests")
    LOG_CHANNEL = os.getenv("LOG_CHANNEL", "")
    FORCE_SUB_CHANNEL = os.getenv("FORCE_SUB_CHANNEL", "")
    
    # ⚙️ BOT SETTINGS
    BOT_LOCKED = False
    DM_ENABLED = True
    MAINTENANCE = False
    
    # 💾 DATABASE
    DB_PATH = "/tmp/book_bot.db"
    
    # 🔍 SEARCH
    RESULTS_PER_PAGE = 8
    MAX_RESULTS = 100
    
    # 🎨 UI DESIGN
    BANNER = """
    ╔══════════════════════════════╗
    ║   📚 PREMIUM BOOK BOT   ║
    ║   🚀 Knowledge Power   ║
    ╚══════════════════════════════╝
    """
    
    # ✨ EMOJIS & SYMBOLS
    EMOJIS = {
        "book": "📚",
        "search": "🔍",
        "download": "📥",
        "star": "⭐",
        "fire": "🔥",
        "heart": "❤️",
        "rocket": "🚀",
        "crown": "👑",
        "trophy": "🏆",
        "gem": "💎",
        "sparkle": "✨",
        "check": "✅",
        "warning": "⚠️",
        "error": "❌",
        "info": "ℹ️",
        "lock": "🔒",
        "unlock": "🔓",
        "user": "👤",
        "group": "👥",
        "time": "🕐",
        "calendar": "📅",
        "stats": "📊",
        "settings": "⚙️",
        "home": "🏠",
        "back": "🔙",
        "next": "➡️",
        "prev": "⬅️",
        "up": "⬆️",
        "down": "⬇️",
        "page": "📄",
        "category": "🏷️",
        "author": "✍️",
        "size": "📦",
        "format": "📄",
        "rating": "⭐",
        "views": "👁️",
        "downloads": "📥"
    }
    
    # 🎯 REACTIONS
    REACTIONS = ["🔥", "⭐", "🎯", "⚡", "❤️", "👍", "👏", "📚", "✨", "💫", "🚀", "💯"]
    
    @classmethod
    def get_emoji(cls, key):
        return cls.EMOJIS.get(key, "📚")
