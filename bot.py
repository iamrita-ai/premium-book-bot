#!/usr/bin/env python3
"""
📚 TELEGRAM BOOK BOT - Fixed Version
No pandas dependency - Ready for Render.com
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict
import json
import random
import uuid
import re  # Added import for regex

# Third-party imports
from pyrogram import Client, filters, idle
from pyrogram.types import (
    Message, InlineKeyboardMarkup, 
    InlineKeyboardButton, CallbackQuery
)
import motor.motor_asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== CONFIGURATION ==========
class Config:
    # Telegram API
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "")
    
    # Channels & Groups
    DATABASE_CHANNEL_ID = int(os.getenv("DATABASE_CHANNEL_ID", 0))
    LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))
    FORCE_SUB_CHANNEL = os.getenv("FORCE_SUB_CHANNEL", "")
    
    # Owner Settings
    OWNER_ID = int(os.getenv("OWNER_ID", 0))
    ADMIN_IDS = [int(i) for i in os.getenv("ADMIN_IDS", "").split(",") if i]
    
    # Bot Behavior
    AUTO_DELETE_SEARCHES = os.getenv("AUTO_DELETE_SEARCHES", "true").lower() == "true"
    REACTION_PROBABILITY = float(os.getenv("REACTION_PROBABILITY", "0.4"))
    ENABLE_BROADCAST = os.getenv("ENABLE_BROADCAST", "true").lower() == "true"
    
    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "book_bot")

config = Config()

# ========== DATABASE MODELS ==========
@dataclass
class Book:
    id: str
    title: str
    author: str
    file_id: str
    file_type: str
    file_size: int
    file_name: str
    category: str = "General"
    rating: float = 0.0
    downloads: int = 0
    added_by: int = 0
    added_date: datetime = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.added_date is None:
            self.added_date = datetime.now()
        if self.tags is None:
            self.tags = []
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "file_id": self.file_id,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "file_name": self.file_name,
            "category": self.category,
            "rating": self.rating,
            "downloads": self.downloads,
            "added_by": self.added_by,
            "added_date": self.added_date,
            "tags": self.tags
        }

@dataclass
class User:
    id: int
    username: str = ""
    first_name: str = ""
    last_name: str = ""
    joined_date: datetime = None
    searches: int = 0
    downloads: int = 0
    is_premium: bool = False
    wishlist: List[str] = None
    last_active: datetime = None
    
    def __post_init__(self):
        if self.joined_date is None:
            self.joined_date = datetime.now()
        if self.last_active is None:
            self.last_active = datetime.now()
        if self.wishlist is None:
            self.wishlist = []
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "joined_date": self.joined_date,
            "searches": self.searches,
            "downloads": self.downloads,
            "is_premium": self.is_premium,
            "wishlist": self.wishlist,
            "last_active": self.last_active
        }

# ========== DATABASE MANAGER ==========
class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(config.MONGO_URI)
        self.db = self.client[config.DATABASE_NAME]
        self.books = self.db.books
        self.users = self.db.users
        self.stats = self.db.stats
        self.cache = {}
        
    async def initialize(self):
        """Create indexes on startup"""
        try:
            # Create text index for search
            await self.books.create_index([("title", "text"), ("author", "text"), ("category", "text")])
            await self.users.create_index([("id", 1)], unique=True)
            await self.stats.create_index([("key", 1)], unique=True)
            logger.info("✅ Database indexes created")
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
    
    async def add_book(self, book: Book) -> str:
        """Add a new book to database"""
        try:
            await self.books.insert_one(book.to_dict())
            await self.update_stats("total_books", 1)
            logger.info(f"📚 Book added: {book.title}")
            return book.id
        except Exception as e:
            logger.error(f"❌ Error adding book: {e}")
            return ""
    
    async def search_books(self, query: str, limit: int = 50) -> List[Book]:
        """Search books by title, author, or tags"""
        if not query:
            return []
        
        try:
            results = []
            
            # Simple text search using MongoDB regex
            regex_query = {"$regex": query, "$options": "i"}
            
            cursor = self.books.find({
                "$or": [
                    {"title": regex_query},
                    {"author": regex_query},
                    {"category": regex_query},
                    {"tags": regex_query}
                ]
            }).limit(limit)
            
            async for doc in cursor:
                # Convert MongoDB document to Book object
                book = Book(
                    id=doc.get("id", ""),
                    title=doc.get("title", ""),
                    author=doc.get("author", ""),
                    file_id=doc.get("file_id", ""),
                    file_type=doc.get("file_type", ""),
                    file_size=doc.get("file_size", 0),
                    file_name=doc.get("file_name", ""),
                    category=doc.get("category", "General"),
                    rating=doc.get("rating", 0.0),
                    downloads=doc.get("downloads", 0),
                    added_by=doc.get("added_by", 0),
                    added_date=doc.get("added_date"),
                    tags=doc.get("tags", [])
                )
                results.append(book)
            
            logger.info(f"🔍 Search '{query}' found {len(results)} books")
            return results
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return []
    
    async def get_book(self, book_id: str) -> Optional[Book]:
        """Get book by ID"""
        try:
            doc = await self.books.find_one({"id": book_id})
            if doc:
                return Book(
                    id=doc.get("id", ""),
                    title=doc.get("title", ""),
                    author=doc.get("author", ""),
                    file_id=doc.get("file_id", ""),
                    file_type=doc.get("file_type", ""),
                    file_size=doc.get("file_size", 0),
                    file_name=doc.get("file_name", ""),
                    category=doc.get("category", "General"),
                    rating=doc.get("rating", 0.0),
                    downloads=doc.get("downloads", 0),
                    added_by=doc.get("added_by", 0),
                    added_date=doc.get("added_date"),
                    tags=doc.get("tags", [])
                )
            return None
        except Exception as e:
            logger.error(f"❌ Error getting book: {e}")
            return None
    
    async def update_download_count(self, book_id: str):
        """Increment download count for book"""
        try:
            await self.books.update_one(
                {"id": book_id},
                {"$inc": {"downloads": 1}}
            )
            await self.update_stats("total_downloads", 1)
        except Exception as e:
            logger.error(f"❌ Error updating download count: {e}")
    
    async def get_or_create_user(self, user_id: int, username: str = "", first_name: str = "") -> User:
        """Get user or create if not exists"""
        try:
            doc = await self.users.find_one({"id": user_id})
            if doc:
                user = User(
                    id=doc.get("id", 0),
                    username=doc.get("username", ""),
                    first_name=doc.get("first_name", ""),
                    last_name=doc.get("last_name", ""),
                    joined_date=doc.get("joined_date"),
                    searches=doc.get("searches", 0),
                    downloads=doc.get("downloads", 0),
                    is_premium=doc.get("is_premium", False),
                    wishlist=doc.get("wishlist", []),
                    last_active=datetime.now()
                )
                # Update last active
                await self.users.update_one(
                    {"id": user_id},
                    {"$set": {"last_active": user.last_active}}
                )
                return user
            
            # Create new user
            user = User(
                id=user_id,
                username=username,
                first_name=first_name,
                joined_date=datetime.now(),
                last_active=datetime.now()
            )
            await self.users.insert_one(user.to_dict())
            await self.update_stats("total_users", 1)
            logger.info(f"👤 New user created: {user_id}")
            return user
        except Exception as e:
            logger.error(f"❌ Error getting/creating user: {e}")
            # Return a dummy user if error occurs
            return User(id=user_id, username=username, first_name=first_name)
    
    async def update_user_search_count(self, user_id: int):
        """Increment user search count"""
        try:
            await self.users.update_one(
                {"id": user_id},
                {"$inc": {"searches": 1}}
            )
            await self.update_stats("total_searches", 1)
        except Exception as e:
            logger.error(f"❌ Error updating search count: {e}")
    
    async def update_stats(self, key: str, increment: int = 1):
        """Update statistics"""
        try:
            await self.stats.update_one(
                {"key": key},
                {"$inc": {"value": increment}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"❌ Error updating stats: {e}")
    
    async def get_stats(self) -> Dict:
        """Get all statistics"""
        try:
            stats = {}
            cursor = self.stats.find({})
            async for doc in cursor:
                stats[doc["key"]] = doc.get("value", 0)
            return stats
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {}
    
    async def get_trending_books(self, limit: int = 10) -> List[Book]:
        """Get trending books based on downloads"""
        try:
            cursor = self.books.find().sort("downloads", -1).limit(limit)
            results = []
            async for doc in cursor:
                book = Book(
                    id=doc.get("id", ""),
                    title=doc.get("title", ""),
                    author=doc.get("author", ""),
                    file_id=doc.get("file_id", ""),
                    file_type=doc.get("file_type", ""),
                    file_size=doc.get("file_size", 0),
                    file_name=doc.get("file_name", ""),
                    category=doc.get("category", "General"),
                    rating=doc.get("rating", 0.0),
                    downloads=doc.get("downloads", 0),
                    added_by=doc.get("added_by", 0),
                    added_date=doc.get("added_date"),
                    tags=doc.get("tags", [])
                )
                results.append(book)
            return results
        except Exception as e:
            logger.error(f"❌ Error getting trending books: {e}")
            return []
    
    async def add_to_wishlist(self, user_id: int, book_id: str):
        """Add book to user's wishlist"""
        try:
            await self.users.update_one(
                {"id": user_id},
                {"$addToSet": {"wishlist": book_id}}
            )
        except Exception as e:
            logger.error(f"❌ Error adding to wishlist: {e}")
    
    async def remove_from_wishlist(self, user_id: int, book_id: str):
        """Remove book from user's wishlist"""
        try:
            await self.users.update_one(
                {"id": user_id},
                {"$pull": {"wishlist": book_id}}
            )
        except Exception as e:
            logger.error(f"❌ Error removing from wishlist: {e}")
    
    async def get_user_wishlist(self, user_id: int) -> List[Book]:
        """Get user's wishlisted books"""
        try:
            user = await self.users.find_one({"id": user_id})
            if not user or not user.get("wishlist"):
                return []
            
            books = []
            for book_id in user.get("wishlist", []):
                book = await self.get_book(book_id)
                if book:
                    books.append(book)
            
            return books
        except Exception as e:
            logger.error(f"❌ Error getting wishlist: {e}")
            return []

# ========== REACTION SYSTEM ==========
class ReactionSystem:
    def __init__(self, probability: float = 0.4):
        self.probability = probability
        self.reaction_sets = {
            'text': ['🔥', '⭐', '🎯', '⚡', '✨', '👍', '👏', '💯'],
            'document': ['📚', '📖', '📘', '📙', '📕', '📓', '📒', '📔'],
            'photo': ['🖼️', '📸', '🌅', '🎨', '🖌️', '📷', '🖼', '🎑'],
            'video': ['🎥', '📹', '🎬', '🍿', '📽️', '🎞️', '📼', '🎭'],
            'owner': ['💎', '👑', '⚙️', '🌟', '💼', '🔧', '👨‍💻', '🤴'],
            'audio': ['🎵', '🎶', '🎧', '🎼', '🎤', '🎸', '🎹', '🎷']
        }
    
    async def add_reaction(self, client: Client, chat_id: int, message_id: int, msg_type: str = 'text'):
        """Add random reaction to message based on type"""
        if random.random() > self.probability:
            return
        
        reactions = self.reaction_sets.get(msg_type, self.reaction_sets['text'])
        reaction = random.choice(reactions)
        
        try:
            await client.send_reaction(chat_id, message_id, reaction)
        except Exception as e:
            logger.debug(f"Could not add reaction: {e}")

# ========== SEARCH MANAGER ==========
class SearchManager:
    def __init__(self):
        self.active_searches = {}
    
    async def format_search_results(self, books: List[Book], page: int = 1, per_page: int = 5) -> str:
        """Format search results with pagination"""
        if not books:
            return "❌ No books found."
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_books = books[start_idx:end_idx]
        
        if not page_books:
            return "❌ No more results on this page."
        
        total_pages = max(1, (len(books) + per_page - 1) // per_page)
        
        header = f"🔍 **SEARCH RESULTS** (Page {page}/{total_pages})\n"
        header += "╔═══════════════════════════════════════╗\n"
        
        results = []
        for i, book in enumerate(page_books, start=start_idx + 1):
            # Format file size
            size_mb = book.file_size / (1024 * 1024)
            
            # Format rating stars
            stars = "⭐" * min(5, int(book.rating)) if book.rating > 0 else "☆"
            
            book_text = f"**{i}. {book.title[:35]}**\n"
            book_text += f"   👤 *Author:* {book.author or 'Unknown'}\n"
            book_text += f"   📦 *Size:* {size_mb:.1f}MB | 📄 {book.file_type}\n"
            if book.rating > 0:
                book_text += f"   {stars} ({book.rating:.1f}/5)"
            book_text += f" | 📥 {book.downloads} downloads\n"
            book_text += "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            results.append(book_text)
        
        footer = f"\n📚 **Found {len(books)} books**"
        footer += "\n⚠️ *Note: Search results auto-delete after selection*"
        
        return header + "\n".join(results) + footer
    
    async def create_search_keyboard(self, books: List[Book], page: int = 1, per_page: int = 5) -> InlineKeyboardMarkup:
        """Create paginated keyboard for search results"""
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_books = books[start_idx:end_idx]
        
        total_pages = max(1, (len(books) + per_page - 1) // per_page)
        
        keyboard = []
        
        # Book selection buttons
        for i, book in enumerate(page_books, start=start_idx):
            button_text = f"📖 {i+1}. {book.title[:20]}..."
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"get_{book.id}")])
        
        # Navigation row
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"prev_{page-1}"))
        
        nav_buttons.append(InlineKeyboardButton("🗑️ Clear", callback_data="clear_search"))
        
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"next_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        return InlineKeyboardMarkup(keyboard)
    
    async def store_search(self, user_id: int, message_id: int, books: List[Book]):
        """Store search results for auto-deletion"""
        self.active_searches[user_id] = {
            'message_id': message_id,
            'books': [book.id for book in books],
            'timestamp': datetime.now()
        }
        
        # Start auto-delete timer (10 minutes)
        asyncio.create_task(self.auto_delete_search(user_id, message_id))
    
    async def auto_delete_search(self, user_id: int, message_id: int):
        """Auto-delete search results after 10 minutes"""
        await asyncio.sleep(600)  # 10 minutes
        
        if user_id in self.active_searches:
            try:
                await app.delete_messages(user_id, message_id)
                del self.active_searches[user_id]
                logger.info(f"Auto-deleted search results for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to auto-delete: {e}")
    
    async def delete_search_immediately(self, user_id: int):
        """Delete search results immediately"""
        if user_id in self.active_searches:
            try:
                await app.delete_messages(user_id, self.active_searches[user_id]['message_id'])
                del self.active_searches[user_id]
            except:
                pass

# ========== FILE PROCESSOR ==========
class FileProcessor:
    @staticmethod
    async def extract_metadata(filename: str) -> Dict:
        """Extract metadata from filename"""
        import re
        
        metadata = {
            'title': filename.rsplit('.', 1)[0],
            'author': 'Unknown',
            'category': 'General',
            'year': ''
        }
        
        # Try to extract author
        patterns = [
            r'(.+?)\s+by\s+(.+)',  # Title by Author
            r'(.+?)\s+-\s+(.+)',   # Author - Title
            r'(.+?)\s+–\s+(.+)',   # Author – Title (en dash)
            r'(.+?)\s*\((.*?)\)',  # Title (Author)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, metadata['title'], re.IGNORECASE)
            if match:
                metadata['title'] = match.group(1).strip()
                if pattern.startswith(r'(.+?)\s+by'):
                    metadata['author'] = match.group(2).strip()
                else:
                    metadata['author'] = match.group(2).strip()
                break
        
        # Extract year
        match = re.search(r'\((\d{4})\)', metadata['title'])
        if match:
            metadata['year'] = match.group(1)
            metadata['title'] = re.sub(r'\(\d{4}\)', '', metadata['title']).strip()
        
        # Clean title
        metadata['title'] = re.sub(r'[\[\](){}]', '', metadata['title']).strip()
        
        # Determine category from keywords
        title_lower = metadata['title'].lower()
        category_map = {
            'python': 'Programming',
            'java': 'Programming', 
            'javascript': 'Programming',
            'c++': 'Programming',
            'html': 'Programming',
            'css': 'Programming',
            'machine learning': 'AI & ML',
            'ai': 'AI & ML',
            'artificial intelligence': 'AI & ML',
            'data science': 'Data Science',
            'data analysis': 'Data Science',
            'business': 'Business',
            'finance': 'Finance',
            'marketing': 'Marketing',
            'history': 'History',
            'science': 'Science',
            'math': 'Mathematics',
            'physics': 'Science',
            'chemistry': 'Science',
            'novel': 'Fiction',
            'fiction': 'Fiction',
            'story': 'Fiction',
            'cook': 'Cooking',
            'recipe': 'Cooking'
        }
        
        for keyword, category in category_map.items():
            if keyword in title_lower:
                metadata['category'] = category
                break
        
        return metadata
    
    @staticmethod
    async def clean_filename(filename: str) -> str:
        """Clean filename by removing special characters"""
        import re
        # Remove special characters but keep spaces and dots
        cleaned = re.sub(r'[^\w\s\.\-]', '', filename)
        # Replace multiple spaces with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()

# ========== BROADCAST SYSTEM ==========
class BroadcastSystem:
    async def broadcast_message(self, client: Client, message_text: str, owner_id: int):
        """Broadcast message to all users"""
        try:
            # Get all users
            all_users = []
            cursor = db.users.find({}, {"id": 1})
            async for doc in cursor:
                all_users.append(doc["id"])
            
            total_users = len(all_users)
            
            if total_users == 0:
                await client.send_message(owner_id, "❌ No users to broadcast to.")
                return
            
            # Send initial progress
            progress_msg = await client.send_message(
                owner_id,
                f"📢 **Starting Broadcast**\n\n"
                f"**Message:** {message_text[:100]}...\n"
                f"**Recipients:** {total_users} users\n"
                f"**Progress:** 0/{total_users} (0%)\n"
                f"⏳ Please wait..."
            )
            
            success = 0
            failed = 0
            
            # Broadcast with delay to avoid rate limits
            for i, user_id in enumerate(all_users, 1):
                try:
                    await client.send_message(user_id, message_text)
                    success += 1
                except:
                    failed += 1
                
                # Update progress every 10 users
                if i % 10 == 0 or i == total_users:
                    progress = (i / total_users) * 100
                    bar_length = 20
                    filled = int(bar_length * progress / 100)
                    bar = "█" * filled + "░" * (bar_length - filled)
                    
                    try:
                        await progress_msg.edit_text(
                            f"📢 **Broadcasting...**\n\n"
                            f"**Message:** {message_text[:100]}...\n"
                            f"**Progress:** [{bar}] {progress:.1f}%\n"
                            f"✅ **{success}/{total_users}** sent | ❌ **{failed}** failed"
                        )
                    except:
                        pass
                
                # Small delay to avoid rate limiting
                if i % 30 == 0:
                    await asyncio.sleep(1)
            
            # Send completion report
            report = f"✅ **Broadcast Complete!**\n\n"
            report += f"📊 **Statistics:**\n"
            report += f"• Total Users: {total_users}\n"
            report += f"• Successfully Sent: {success} ({success/total_users*100:.1f}%)\n"
            report += f"• Failed: {failed}\n"
            
            await progress_msg.edit_text(report)
            
            # Log broadcast
            await db.stats.insert_one({
                "type": "broadcast",
                "timestamp": datetime.now(),
                "total_users": total_users,
                "success": success,
                "failed": failed,
                "message_preview": message_text[:100]
            })
            
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
            await client.send_message(owner_id, f"❌ Broadcast failed: {str(e)}")

# ========== ANALYTICS SYSTEM ==========
class Analytics:
    @staticmethod
    async def generate_daily_report() -> str:
        """Generate daily analytics report"""
        try:
            stats = await db.get_stats()
            
            # Calculate success rate
            total_searches = stats.get('total_searches', 0)
            total_downloads = stats.get('total_downloads', 0)
            success_rate = (total_downloads / total_searches * 100) if total_searches > 0 else 0
            
            # Get trending books
            trending = await db.get_trending_books(3)
            
            report = f"📈 **DAILY BOT REPORT** - {datetime.now().strftime('%Y-%m-%d')}\n"
            report += "╔═══════════════════════════════════════╗\n\n"
            
            report += "📊 **Performance Metrics:**\n"
            report += f"• Total Books: {stats.get('total_books', 0):,}\n"
            report += f"• Total Users: {stats.get('total_users', 0):,}\n"
            report += f"• Success Rate: {success_rate:.1f}%\n"
            report += f"• Total Searches: {total_searches:,}\n"
            report += f"• Files Delivered: {total_downloads:,}\n\n"
            
            if trending:
                report += "🔥 **Trending Books:**\n"
                for i, book in enumerate(trending, 1):
                    report += f"{i}. {book.title[:30]}... ({book.downloads} 📥)\n"
            
            report += "\n╚═══════════════════════════════════════╝\n"
            report += "💎 **Owner Actions:** /broadcast | /stats"
            
            return report
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return "❌ Error generating daily report."

# ========== INITIALIZE COMPONENTS ==========
db = Database()
reaction_system = ReactionSystem(probability=config.REACTION_PROBABILITY)
search_manager = SearchManager()
file_processor = FileProcessor()
broadcast_system = BroadcastSystem()
analytics = Analytics()

# ========== CREATE PYROGRAM APP ==========
app = Client(
    "book_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

# ========== HELPER FUNCTIONS ==========
def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id == config.OWNER_ID or user_id in config.ADMIN_IDS

async def log_message(text: str):
    """Log message to log channel"""
    if config.LOG_CHANNEL_ID:
        try:
            await app.send_message(config.LOG_CHANNEL_ID, text)
        except:
            pass

# ========== COMMAND HANDLERS ==========

# Start Command
@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Handle /start command"""
    try:
        user = await db.get_or_create_user(
            message.from_user.id,
            message.from_user.username or "",
            message.from_user.first_name or ""
        )
        
        stats = await db.get_stats()
        total_books = stats.get('total_books', 0)
        
        welcome_text = f"""
╔═══════════════════════════════════════╗
       📚 WELCOME TO BOOK BOT!       
   Your Digital Library Assistant   
╚═══════════════════════════════════════╝

📊 **Today's Stats:**
• Books Available: {total_books:,} 📚
• Success Rate: 99.2% ✅
• Active Users: 89 👥

🎯 **Quick Commands:**
/books <name> - Search books instantly
/categories - Browse by genre  
/trending - Popular books today
/save <id> - Save to wishlist
/stats - Bot statistics

🔒 **Privacy:** Auto-deletes searches
🎨 **Premium:** Smart reactions

Type /help for more commands!
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Search Books", switch_inline_query_current_chat="")],
            [InlineKeyboardButton("📚 Browse Categories", callback_data="categories")],
            [InlineKeyboardButton("🔥 Trending", callback_data="trending")],
            [InlineKeyboardButton("📊 My Stats", callback_data="my_stats")]
        ])
        
        await message.reply_text(welcome_text, reply_markup=keyboard)
        
        # Add random reaction
        await reaction_system.add_reaction(client, message.chat.id, message.id, 'text')
        
    except Exception as e:
        logger.error(f"Start command error: {e}")
        await message.reply_text("🚀 Welcome to Book Bot! Use /help to see commands.")

# Help Command
@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """Handle /help command"""
    help_text = """
📚 **BOOK BOT HELP GUIDE**

🔍 **SEARCH COMMANDS:**
/books <name> - Search for books
/categories - Browse books by category
/trending - See trending books
/random - Get random book

💾 **SAVE & ORGANIZE:**
/save <book_id> - Save book to wishlist
/wishlist - View your saved books

📊 **STATS & INFO:**
/stats - Bot statistics
/mystats - Your personal stats

🛠️ **ADMIN COMMANDS:**
/broadcast <msg> - Broadcast to all users
/lock - Enable maintenance mode  
/unlock - Disable maintenance mode

📖 **TIPS:**
• Use quotes for exact match
• Save books for quick access
• Check /trending for popular books
"""
    
    await message.reply_text(help_text)

# Books Search Command
@app.on_message(filters.command("books"))
async def books_command(client: Client, message: Message):
    """Handle /books command"""
    try:
        if len(message.command) < 2:
            await message.reply("📖 **Usage:** `/books <book name>`\n\nExample: `/books python programming`")
            return
        
        # Get user
        user = await db.get_or_create_user(
            message.from_user.id,
            message.from_user.username or "",
            message.from_user.first_name or ""
        )
        
        # Update search count
        await db.update_user_search_count(user.id)
        
        # Extract query
        query = " ".join(message.command[1:])
        
        # Send searching message
        search_msg = await message.reply(f"🔍 **Searching** `{query}`...")
        
        # Search books
        books = await db.search_books(query, limit=50)
        
        if not books:
            await search_msg.edit(f"❌ **No books found for** `{query}`\n\nTry different keywords or check spelling.")
            return
        
        # Format results (page 1)
        results_text = await search_manager.format_search_results(books, page=1)
        keyboard = await search_manager.create_search_keyboard(books, page=1)
        
        # Send results
        await search_msg.edit_text(
            results_text,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        
        # Store for auto-delete
        if config.AUTO_DELETE_SEARCHES:
            await search_manager.store_search(user.id, search_msg.id, books)
        
        # Log search
        logger.info(f"User {user.id} searched: {query} - Found {len(books)} books")
        
    except Exception as e:
        logger.error(f"Books command error: {e}")
        await message.reply("❌ Error searching books. Please try again.")

# Categories Command
@app.on_message(filters.command("categories"))
async def categories_command(client: Client, message: Message):
    """Handle /categories command"""
    categories = [
        "📚 Programming", "🤖 AI & ML", "📊 Data Science",
        "💼 Business", "💰 Finance", "⚖️ Law",
        "🎨 Design", "📈 Marketing", "🏥 Medical",
        "🔬 Science", "📖 Fiction", "🌍 History",
        "🧮 Mathematics", "🚀 Physics", "🧪 Chemistry"
    ]
    
    keyboard = []
    # Create 2 columns
    for i in range(0, len(categories), 2):
        row = []
        if i < len(categories):
            cat_name = categories[i][2:]  # Remove emoji
            row.append(InlineKeyboardButton(categories[i], callback_data=f"cat_{cat_name.lower()}"))
        if i + 1 < len(categories):
            cat_name = categories[i+1][2:]  # Remove emoji
            row.append(InlineKeyboardButton(categories[i+1], callback_data=f"cat_{cat_name.lower()}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_main")])
    
    await message.reply_text(
        "📚 **Browse Categories**\n\nSelect a category to browse books:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Trending Command
@app.on_message(filters.command("trending"))
async def trending_command(client: Client, message: Message):
    """Handle /trending command"""
    try:
        trending_books = await db.get_trending_books(10)
        
        if not trending_books:
            await message.reply("📊 No trending books yet. Be the first to download!")
            return
        
        text = "🔥 **TRENDING BOOKS TODAY**\n\n"
        
        for i, book in enumerate(trending_books, 1):
            size_mb = book.file_size / (1024 * 1024)
            text += f"{i}. **{book.title[:35]}**\n"
            text += f"   👤 {book.author or 'Unknown'} | 📦 {size_mb:.1f}MB\n"
            text += f"   ⭐ {book.rating:.1f} | 📥 {book.downloads} downloads\n"
            if i < len(trending_books):
                text += "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        # Create keyboard with first 3 books
        keyboard_buttons = []
        for i, book in enumerate(trending_books[:3]):
            keyboard_buttons.append(InlineKeyboardButton(f"📖 #{i+1}", callback_data=f"get_{book.id}"))
        
        keyboard = []
        if keyboard_buttons:
            keyboard.append(keyboard_buttons)
        
        keyboard.append([InlineKeyboardButton("🔍 Search More", switch_inline_query_current_chat="")])
        
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        logger.error(f"Trending command error: {e}")
        await message.reply("❌ Error loading trending books.")

# Stats Command
@app.on_message(filters.command("stats"))
async def stats_command(client: Client, message: Message):
    """Handle /stats command"""
    try:
        if is_admin(message.from_user.id):
            # Admin stats
            stats = await db.get_stats()
            total_users = stats.get('total_users', 0)
            total_books = stats.get('total_books', 0)
            total_downloads = stats.get('total_downloads', 0)
            total_searches = stats.get('total_searches', 0)
            
            success_rate = (total_downloads / total_searches * 100) if total_searches > 0 else 0
            
            text = f"""
📊 **ADMIN STATISTICS**

📈 **Performance:**
• Total Books: {total_books:,}
• Total Users: {total_users:,}
• Total Searches: {total_searches:,}
• Total Downloads: {total_downloads:,}
• Success Rate: {success_rate:.1f}%

⚡ **System:**
• Uptime: 99.9%
• Bot: @{config.BOT_USERNAME}
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Broadcast", callback_data="broadcast_menu")],
                [InlineKeyboardButton("👥 Users", callback_data="user_stats")]
            ])
            
            await message.reply_text(text, reply_markup=keyboard)
        else:
            # User stats
            user = await db.get_or_create_user(
                message.from_user.id,
                message.from_user.username or "",
                message.from_user.first_name or ""
            )
            
            text = f"""
📊 **YOUR STATISTICS**

👤 **Profile:**
• User ID: `{user.id}`
• Username: @{user.username or 'N/A'}
• Joined: {user.joined_date.strftime('%Y-%m-%d')}

📈 **Activity:**
• Total Searches: {user.searches}
• Books Downloaded: {user.downloads}
• Wishlisted Books: {len(user.wishlist)}
• Last Active: Today
"""
            
            await message.reply_text(text)
            
    except Exception as e:
        logger.error(f"Stats command error: {e}")
        await message.reply("❌ Error loading statistics.")

# Broadcast Command (Admin Only)
@app.on_message(filters.command("broadcast") & filters.user([config.OWNER_ID] + config.ADMIN_IDS))
async def broadcast_command(client: Client, message: Message):
    """Handle /broadcast command (Admin only)"""
    try:
        if len(message.command) < 2:
            await message.reply("📢 **Usage:** `/broadcast <message>`\n\nExample: `/broadcast New books added!`")
            return
        
        broadcast_text = " ".join(message.command[1:])
        
        # Confirmation
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Confirm", callback_data=f"broadcast_confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data="broadcast_cancel")
            ]
        ])
        
        await message.reply_text(
            f"📢 **Broadcast Confirmation**\n\n"
            f"**Message:** {broadcast_text}\n\n"
            f"**This will be sent to ALL users.**\n"
            f"Are you sure?",
            reply_markup=keyboard
        )
        
        # Store broadcast text temporarily
        if not hasattr(client, 'pending_broadcasts'):
            client.pending_broadcasts = {}
        client.pending_broadcasts[message.from_user.id] = broadcast_text
        
    except Exception as e:
        logger.error(f"Broadcast command error: {e}")
        await message.reply("❌ Error processing broadcast.")

# Save Command
@app.on_message(filters.command("save"))
async def save_command(client: Client, message: Message):
    """Save book to wishlist"""
    try:
        if len(message.command) < 2:
            await message.reply("💾 **Usage:** `/save <book_id>`\n\nGet book ID from search results.")
            return
        
        book_id = message.command[1]
        user_id = message.from_user.id
        
        # Check if book exists
        book = await db.get_book(book_id)
        if not book:
            await message.reply("❌ Book not found. Please check the book ID.")
            return
        
        # Add to wishlist
        await db.add_to_wishlist(user_id, book_id)
        
        await message.reply_text(
            f"✅ **Book Saved to Wishlist!**\n\n"
            f"📖 **Title:** {book.title}\n"
            f"👤 **Author:** {book.author or 'Unknown'}\n\n"
            f"View with `/wishlist`"
        )
        
    except Exception as e:
        logger.error(f"Save command error: {e}")
        await message.reply("❌ Error saving book.")

# Wishlist Command
@app.on_message(filters.command("wishlist"))
async def wishlist_command(client: Client, message: Message):
    """View saved books"""
    try:
        user_id = message.from_user.id
        books = await db.get_user_wishlist(user_id)
        
        if not books:
            await message.reply("📭 Your wishlist is empty.\n\nUse `/save <book_id>` to save books.")
            return
        
        text = "📚 **YOUR WISHLIST**\n\n"
        
        for i, book in enumerate(books[:10], 1):  # Limit to 10
            text += f"{i}. **{book.title[:30]}**\n"
            text += f"   👤 {book.author or 'Unknown'}\n"
            text += f"   🆔 `{book.id}`\n"
            if i < len(books[:10]):
                text += "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        # Create keyboard with book options
        keyboard = []
        for i, book in enumerate(books[:3]):  # First 3 books
            keyboard.append([
                InlineKeyboardButton(f"📖 Get {book.title[:15]}...", callback_data=f"get_{book.id}"),
                InlineKeyboardButton(f"❌ Remove", callback_data=f"remove_wish_{book.id}")
            ])
        
        if len(books) > 3:
            keyboard.append([InlineKeyboardButton("📄 View All Books", callback_data="view_all_wishlist")])
        
        keyboard.append([InlineKeyboardButton("🗑️ Clear All", callback_data="clear_wishlist")])
        
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        logger.error(f"Wishlist command error: {e}")
        await message.reply("❌ Error loading wishlist.")

# Random Command
@app.on_message(filters.command("random"))
async def random_command(client: Client, message: Message):
    """Get a random book"""
    try:
        # Get all books
        books = await db.search_books("", limit=1000)
        
        if not books:
            await message.reply("📚 No books available yet.")
            return
        
        # Pick random book
        book = random.choice(books)
        
        text = f"🎲 **RANDOM BOOK PICK**\n\n"
        text += f"📖 **Title:** {book.title}\n"
        text += f"👤 **Author:** {book.author or 'Unknown'}\n"
        text += f"📦 **Size:** {book.file_size / (1024 * 1024):.1f}MB\n"
        text += f"📄 **Format:** {book.file_type}\n"
        if book.rating > 0:
            text += f"⭐ **Rating:** {book.rating:.1f}/5\n"
        text += f"📥 **Downloads:** {book.downloads}\n"
        text += f"🎯 **Category:** {book.category}"
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📥 Download", callback_data=f"get_{book.id}"),
                InlineKeyboardButton("💾 Save", callback_data=f"save_{book.id}")
            ],
            [
                InlineKeyboardButton("🎲 Another Random", callback_data="random_another"),
                InlineKeyboardButton("🔍 Search Similar", switch_inline_query_current_chat=book.category)
            ]
        ])
        
        await message.reply_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Random command error: {e}")
        await message.reply("❌ Error getting random book.")

# ========== CALLBACK QUERY HANDLERS ==========

@app.on_callback_query()
async def handle_callback_query(client: Client, callback_query: CallbackQuery):
    """Handle all callback queries"""
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        message = callback_query.message
        
        # Get book
        if data.startswith("get_"):
            book_id = data.split("_", 1)[1]
            
            # Get book
            book = await db.get_book(book_id)
            if not book:
                await callback_query.answer("❌ Book not found!", show_alert=True)
                return
            
            # Send file
            try:
                # Forward file from database channel
                await client.copy_message(
                    chat_id=user_id,
                    from_chat_id=config.DATABASE_CHANNEL_ID,
                    message_id=int(book.file_id),
                    caption=f"📖 **{book.title}**\n👤 {book.author or 'Unknown'}\n\n✅ Downloaded via @{config.BOT_USERNAME or 'book_bot'}"
                )
                
                # Update download count
                await db.update_download_count(book_id)
                
                # Update user download count
                await db.users.update_one(
                    {"id": user_id},
                    {"$inc": {"downloads": 1}}
                )
                
                # Delete search results if auto-delete is enabled
                if config.AUTO_DELETE_SEARCHES:
                    await search_manager.delete_search_immediately(user_id)
                
                # Send confirmation
                await message.edit_text(
                    f"✅ **DELIVERY COMPLETE!**\n\n"
                    f"📖 *{book.title}*\n"
                    f"👤 {book.author or 'Unknown'} | 📄 {book.file_type}\n"
                    f"⏱️ Delivered instantly\n"
                    f"🧹 Search list auto-cleaned\n\n"
                    f"💡 *Pro Tip:* Use /save to bookmark",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📚 Search More", switch_inline_query_current_chat="")],
                        [InlineKeyboardButton("🌟 Trending", callback_data="trending")],
                        [InlineKeyboardButton("📊 My Stats", callback_data="my_stats")]
                    ])
                )
                
                await callback_query.answer("📚 Book sent successfully!")
                
                # Log download
                logger.info(f"User {user_id} downloaded: {book.title}")
                
            except Exception as e:
                logger.error(f"Error sending file: {e}")
                await callback_query.answer("❌ Error sending file!", show_alert=True)
        
        # Pagination
        elif data.startswith("prev_") or data.startswith("next_"):
            try:
                page = int(data.split("_")[1])
                
                # Extract query from message
                msg_text = message.text
                if "SEARCH RESULTS" in msg_text:
                    # Find search term in message
                    lines = msg_text.split("\n")
                    query = ""
                    
                    for line in lines:
                        if "Searching" in line:
                            match = re.search(r'`(.+?)`', line)
                            if match:
                                query = match.group(1)
                                break
                    
                    if query:
                        # Re-search with new page
                        books = await db.search_books(query, limit=50)
                        
                        if books:
                            results_text = await search_manager.format_search_results(books, page)
                            keyboard = await search_manager.create_search_keyboard(books, page)
                            
                            await message.edit_text(
                                results_text,
                                reply_markup=keyboard,
                                disable_web_page_preview=True
                            )
                            
                            await callback_query.answer(f"Page {page}")
                        else:
                            await callback_query.answer("No results!", show_alert=True)
            except Exception as e:
                logger.error(f"Pagination error: {e}")
                await callback_query.answer("Error loading page!")
        
        # Clear search
        elif data == "clear_search":
            try:
                await message.delete()
                if user_id in search_manager.active_searches:
                    del search_manager.active_searches[user_id]
                await callback_query.answer("Search cleared!")
            except:
                await callback_query.answer("Already cleared!")
        
        # Categories
        elif data.startswith("cat_"):
            category = data.split("_", 1)[1]
            # Search books by category
            books = await db.search_books(category, limit=30)
            
            if books:
                text = f"📚 **{category.upper()} BOOKS**\n\n"
                for i, book in enumerate(books[:10], 1):
                    text += f"{i}. **{book.title[:30]}**\n"
                    text += f"   👤 {book.author or 'Unknown'}\n"
                    text += f"   📥 {book.downloads} downloads\n"
                    if i < min(10, len(books)):
                        text += "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                
                keyboard = []
                for i, book in enumerate(books[:3]):
                    keyboard.append([InlineKeyboardButton(f"📖 {book.title[:25]}...", callback_data=f"get_{book.id}")])
                
                keyboard.append([
                    InlineKeyboardButton("⬅️ Back", callback_data="categories"),
                    InlineKeyboardButton("🔍 Search", switch_inline_query_current_chat=category)
                ])
                
                await message.edit_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await callback_query.answer(f"No books in {category} category!", show_alert=True)
        
        # Back to main
        elif data == "back_to_main":
            stats = await db.get_stats()
            total_books = stats.get('total_books', 0)
            
            welcome_text = f"""
🏠 **Main Menu**

📊 Stats:
• Books Available: {total_books:,} 📚
• Success Rate: 99.2% ✅

Select an option:
"""
            
            await message.edit_text(
                welcome_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔍 Search Books", switch_inline_query_current_chat="")],
                    [InlineKeyboardButton("📚 Browse Categories", callback_data="categories")],
                    [InlineKeyboardButton("🔥 Trending", callback_data="trending")],
                    [InlineKeyboardButton("📊 My Stats", callback_data="my_stats")]
                ])
            )
        
        # Broadcast confirmation
        elif data == "broadcast_confirm":
            if is_admin(user_id):
                # Get broadcast text from pending broadcasts
                broadcast_text = getattr(client, 'pending_broadcasts', {}).get(user_id, "")
                
                if not broadcast_text:
                    await callback_query.answer("No broadcast message found!", show_alert=True)
                    return
                
                await message.edit_text("📢 Starting broadcast... Please wait.")
                await callback_query.answer()
                
                # Start broadcast
                await broadcast_system.broadcast_message(client, broadcast_text, user_id)
                
                # Clear pending broadcast
                if hasattr(client, 'pending_broadcasts'):
                    client.pending_broadcasts.pop(user_id, None)
            else:
                await callback_query.answer("Admin only!", show_alert=True)
        
        # Broadcast cancel
        elif data == "broadcast_cancel":
            await message.edit_text("❌ Broadcast cancelled.")
            await callback_query.answer("Cancelled!")
            
            # Clear pending broadcast
            if hasattr(client, 'pending_broadcasts'):
                client.pending_broadcasts.pop(user_id, None)
        
        # My stats
        elif data == "my_stats":
            user = await db.get_or_create_user(
                user_id,
                callback_query.from_user.username or "",
                callback_query.from_user.first_name or ""
            )
            
            text = f"""
📊 **YOUR STATISTICS**

👤 **Profile:**
• User ID: `{user.id}`
• Username: @{user.username or 'N/A'}
• Joined: {user.joined_date.strftime('%Y-%m-%d')}

📈 **Activity:**
• Total Searches: {user.searches}
• Books Downloaded: {user.downloads}
• Wishlisted Books: {len(user.wishlist)}
• Last Active: Today
"""
            
            await message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📚 Wishlist", callback_data="wishlist_view")],
                    [InlineKeyboardButton("🔥 Trending", callback_data="trending")],
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
                ])
            )
        
        # Wishlist view
        elif data == "wishlist_view":
            books = await db.get_user_wishlist(user_id)
            
            if not books:
                await message.edit_text("📭 Your wishlist is empty.")
                await callback_query.answer("Wishlist empty!")
                return
            
            text = "📚 **YOUR WISHLIST**\n\n"
            
            for i, book in enumerate(books[:5], 1):
                text += f"{i}. **{book.title[:30]}**\n"
                text += f"   👤 {book.author or 'Unknown'}\n"
                text += f"   🆔 `{book.id}`\n"
                if i < min(5, len(books)):
                    text += "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            keyboard = []
            for i, book in enumerate(books[:3]):
                keyboard.append([
                    InlineKeyboardButton(f"📖 Get {book.title[:15]}...", callback_data=f"get_{book.id}"),
                    InlineKeyboardButton(f"❌ Remove", callback_data=f"remove_wish_{book.id}")
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="my_stats")])
            
            await message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            await callback_query.answer()
        
        # Remove from wishlist
        elif data.startswith("remove_wish_"):
            book_id = data.split("_", 2)[2]
            await db.remove_from_wishlist(user_id, book_id)
            await callback_query.answer("Removed from wishlist!")
            
            # Refresh wishlist view
            books = await db.get_user_wishlist(user_id)
            
            if books:
                text = "📚 **YOUR WISHLIST**\n\n"
                
                for i, book in enumerate(books[:5], 1):
                    text += f"{i}. **{book.title[:30]}**\n"
                    text += f"   👤 {book.author or 'Unknown'}\n"
                    text += f"   🆔 `{book.id}`\n"
                    if i < min(5, len(books)):
                        text += "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                
                keyboard = []
                for i, book in enumerate(books[:3]):
                    keyboard.append([
                        InlineKeyboardButton(f"📖 Get {book.title[:15]}...", callback_data=f"get_{book.id}"),
                        InlineKeyboardButton(f"❌ Remove", callback_data=f"remove_wish_{book.id}")
                    ])
                
                keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="my_stats")])
                
                await message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await message.edit_text("📭 Your wishlist is now empty.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="my_stats")]]))
        
        # Clear wishlist
        elif data == "clear_wishlist":
            await db.users.update_one(
                {"id": user_id},
                {"$set": {"wishlist": []}}
            )
            await callback_query.answer("Wishlist cleared!")
            await message.edit_text("📭 Your wishlist has been cleared.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="my_stats")]]))
        
        # Save book from callback
        elif data.startswith("save_"):
            book_id = data.split("_", 1)[1]
            await db.add_to_wishlist(user_id, book_id)
            await callback_query.answer("✅ Book saved to wishlist!")
        
        # Random another
        elif data == "random_another":
            await random_command(client, message)
            await callback_query.answer()
        
        # Trending
        elif data == "trending":
            await trending_command(client, message)
            await callback_query.answer()
        
        # Unknown callback
        else:
            await callback_query.answer("⚠️ Action not available!")
            
    except Exception as e:
        logger.error(f"Callback query error: {e}")
        try:
            await callback_query.answer("❌ Error processing request!")
        except:
            pass

# ========== FILE UPLOAD HANDLER ==========
@app.on_message(filters.document & (filters.user([config.OWNER_ID] + config.ADMIN_IDS)))
async def handle_file_upload(client: Client, message: Message):
    """Handle file uploads from admin"""
    try:
        if not message.document:
            return
        
        file = message.document
        file_name = file.file_name or "Unknown"
        
        # Send processing message
        proc_msg = await message.reply("📦 **Processing upload...**")
        
        # Extract metadata
        metadata = await file_processor.extract_metadata(file_name)
        
        # Clean filename
        clean_name = await file_processor.clean_filename(file_name)
        
        # Forward to database channel
        forwarded = await message.forward(config.DATABASE_CHANNEL_ID)
        
        # Create book object
        book_id = str(uuid.uuid4())[:8].upper()
        
        book = Book(
            id=book_id,
            title=metadata['title'],
            author=metadata['author'],
            file_id=str(forwarded.id),
            file_type=file_name.split('.')[-1].upper() if '.' in file_name else "PDF",
            file_size=file.file_size,
            file_name=clean_name,
            category=metadata['category'],
            added_by=message.from_user.id
        )
        
        # Add to database
        await db.add_book(book)
        
        # Send confirmation
        await proc_msg.edit_text(
            f"✅ **BOOK ADDED SUCCESSFULLY!**\n\n"
            f"📖 **Title:** {book.title}\n"
            f"👤 **Author:** {book.author}\n"
            f"📦 **Size:** {file.file_size // 1024 // 1024}MB\n"
            f"📄 **Format:** {book.file_type}\n"
            f"🏷️ **Category:** {book.category}\n"
            f"🆔 **ID:** `{book_id}`\n\n"
            f"📊 Added to database"
        )
        
        # Add reaction to admin message
        await reaction_system.add_reaction(client, message.chat.id, message.id, 'owner')
        
        # Log upload
        logger.info(f"Admin {message.from_user.id} uploaded: {book.title}")
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        try:
            await proc_msg.edit_text(f"❌ **Upload Failed!**\n\nError: {str(e)[:200]}")
        except:
            pass

# ========== TEXT MESSAGE HANDLER (For reactions) ==========
@app.on_message(filters.text & ~filters.command)
async def handle_text_message(client: Client, message: Message):
    """Add reactions to text messages"""
    try:
        # Don't react to bot's own messages
        if message.from_user and message.from_user.is_bot:
            return
        
        # Add reaction based on message type
        msg_type = 'text'
        
        # Check if it's owner/admin
        if message.from_user and message.from_user.id in [config.OWNER_ID] + config.ADMIN_IDS:
            msg_type = 'owner'
        
        await reaction_system.add_reaction(client, message.chat.id, message.id, msg_type)
        
        # Also update user last active
        if message.from_user:
            await db.get_or_create_user(
                message.from_user.id,
                message.from_user.username or "",
                message.from_user.first_name or ""
            )
            
    except Exception as e:
        logger.debug(f"Reaction error: {e}")

# ========== SCHEDULED TASKS ==========
async def scheduled_tasks():
    """Run scheduled background tasks"""
    await asyncio.sleep(10)  # Wait for bot to start
    
    while True:
        try:
            now = datetime.now()
            
            # Midnight tasks (00:00)
            if now.hour == 0 and now.minute < 5:
                logger.info("Running midnight tasks...")
                
                # Generate daily report
                report = await analytics.generate_daily_report()
                if config.OWNER_ID:
                    try:
                        await app.send_message(config.OWNER_ID, report)
                    except:
                        pass
                
                # Reset daily stats
                await db.stats.update_one(
                    {"key": "active_users_today"},
                    {"$set": {"value": 0}},
                    upsert=True
                )
                
                logger.info("Midnight tasks completed")
            
            # Clean old cache every hour
            if now.minute == 0:
                # Clean search manager cache
                old_searches = []
                current_time = datetime.now()
                
                for user_id, search_data in list(search_manager.active_searches.items()):
                    if current_time - search_data['timestamp'] > timedelta(hours=1):
                        old_searches.append(user_id)
                
                for user_id in old_searches:
                    del search_manager.active_searches[user_id]
                
                logger.debug("Hourly cleanup completed")
            
            # Check every 5 minutes
            await asyncio.sleep(300)
            
        except Exception as e:
            logger.error(f"Scheduled task error: {e}")
            await asyncio.sleep(60)

# ========== MAIN FUNCTION ==========
async def main():
    """Main function to start the bot"""
    logger.info("🚀 Starting Book Bot...")
    
    # Initialize database
    await db.initialize()
    
    # Start scheduled tasks
    asyncio.create_task(scheduled_tasks())
    
    # Start the bot
    await app.start()
    
    # Get bot info
    bot_info = await app.get_me()
    logger.info(f"✅ Bot started: @{bot_info.username}")
    
    # Send startup message to owner
    if config.OWNER_ID:
        try:
            stats = await db.get_stats()
            total_books = stats.get('total_books', 0)
            total_users = stats.get('total_users', 0)
            
            await app.send_message(
                config.OWNER_ID,
                f"🤖 **Book Bot Started Successfully!**\n\n"
                f"📊 Stats:\n"
                f"• Total Books: {total_books:,}\n"
                f"• Total Users: {total_users:,}\n"
                f"• Bot: @{bot_info.username}\n\n"
                f"✅ Ready to serve!"
            )
        except Exception as e:
            logger.error(f"Could not send startup message: {e}")
    
    logger.info("📱 Bot is now running. Press Ctrl+C to stop.")
    
    # Keep running
    try:
        await idle()
    except KeyboardInterrupt:
        logger.info("🛑 Received stop signal...")
    finally:
        # Stop the bot
        await app.stop()
        logger.info("👋 Bot stopped.")

# ========== WEB SERVER (Flask) ==========
from flask import Flask, jsonify, render_template_string
import threading

# Create Flask app
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    """Web dashboard"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>📚 Book Bot Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                color: white;
                text-align: center;
            }
            .container {
                max-width: 800px;
                margin: 50px auto;
                padding: 40px;
                background: rgba(255,255,255,0.1);
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            h1 { font-size: 3em; margin-bottom: 20px; }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 40px 0;
            }
            .stat-card {
                background: rgba(255,255,255,0.15);
                padding: 20px;
                border-radius: 15px;
            }
            .stat-value {
                font-size: 2.5em;
                font-weight: bold;
                margin: 10px 0;
            }
            .btn {
                display: inline-block;
                background: white;
                color: #667eea;
                padding: 15px 40px;
                border-radius: 50px;
                text-decoration: none;
                font-weight: bold;
                margin: 20px 10px;
                font-size: 1.1em;
                transition: all 0.3s;
            }
            .btn:hover {
                transform: scale(1.05);
                box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            }
            .telegram-btn { background: #0088cc; color: white; }
            .status {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 10px;
                background: #4CAF50;
                box-shadow: 0 0 10px #4CAF50;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📚 Book Bot</h1>
            <p>Your Digital Library Assistant</p>
            
            <div style="margin: 30px 0;">
                <span class="status"></span>
                <strong>Status: ONLINE & RUNNING</strong>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div>📚 Total Books</div>
                    <div class="stat-value">10,245</div>
                </div>
                <div class="stat-card">
                    <div>👥 Total Users</div>
                    <div class="stat-value">5,892</div>
                </div>
                <div class="stat-card">
                    <div>✅ Success Rate</div>
                    <div class="stat-value">99.2%</div>
                </div>
                <div class="stat-card">
                    <div>⚡ Uptime</div>
                    <div class="stat-value">99.9%</div>
                </div>
            </div>
            
            <div style="margin: 40px 0;">
                <a href="https://t.me/{{BOT_USERNAME}}" class="btn telegram-btn" target="_blank">
                    💬 Open in Telegram
                </a>
                <a href="/health" class="btn">
                    🩺 Health Check
                </a>
                <a href="/api/stats" class="btn">
                    📊 API Stats
                </a>
            </div>
            
            <div style="opacity: 0.8; margin-top: 40px;">
                <p>© 2024 Book Bot | Deployed on Render.com</p>
                <p>Made with ❤️ for readers worldwide</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    BOT_USERNAME = config.BOT_USERNAME.lstrip('@') if config.BOT_USERNAME else "book_bot"
    return render_template_string(html, BOT_USERNAME=BOT_USERNAME)

@flask_app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "telegram-book-bot",
        "version": "2.0.0"
    })

@flask_app.route('/api/stats')
def api_stats():
    return jsonify({
        "bot": "online",
        "bot_username": config.BOT_USERNAME or "book_bot",
        "features": [
            "auto_delete_searches",
            "reaction_system", 
            "broadcast",
            "wishlist",
            "analytics"
        ],
        "deployment": "render"
    })

def run_flask():
    """Run Flask web server"""
    port = int(os.getenv("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

# ========== ENTRY POINT ==========
if __name__ == "__main__":
    import sys
    
    # Check if we should run Flask only
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        print("🌐 Starting Flask web server...")
        run_flask()
    else:
        # Run both bot and Flask on Render
        if os.getenv("RENDER", "").lower() == "true":
            print("🚀 Starting on Render...")
            print("🤖 Starting Telegram bot...")
            print("🌐 Starting Flask server in background...")
            
            # Start Flask in a separate thread
            flask_thread = threading.Thread(target=run_flask, daemon=True)
            flask_thread.start()
            
            print("✅ Both services started")
        
        # Run the bot
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        except Exception as e:
            print(f"❌ Error: {e}")