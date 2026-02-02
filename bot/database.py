import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Premium Database Manager with connection pooling"""
    
    def __init__(self, db_path: str = "/tmp/book_bot.db"):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._connection_pool = {}
        self._max_pool_size = 5
        
    def _get_connection(self):
        """Get a database connection from pool"""
        thread_id = threading.get_ident()
        
        with self._lock:
            if thread_id not in self._connection_pool:
                if len(self._connection_pool) >= self._max_pool_size:
                    # Remove oldest connection
                    oldest = min(self._connection_pool.items(), key=lambda x: x[1]['last_used'])
                    conn = self._connection_pool.pop(oldest[0])['connection']
                    conn.close()
                
                conn = sqlite3.connect(self.db_path, timeout=30.0)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.row_factory = sqlite3.Row
                
                self._connection_pool[thread_id] = {
                    'connection': conn,
                    'last_used': datetime.now()
                }
            
            conn_data = self._connection_pool[thread_id]
            conn_data['last_used'] = datetime.now()
            return conn_data['connection']
    
    def initialize(self):
        """Initialize database with all tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Books Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                author TEXT DEFAULT 'Unknown',
                description TEXT,
                file_id TEXT NOT NULL,
                file_type TEXT DEFAULT 'PDF',
                file_size INTEGER DEFAULT 0,
                category TEXT,
                tags TEXT,
                rating REAL DEFAULT 0.0,
                download_count INTEGER DEFAULT 0,
                is_premium BOOLEAN DEFAULT 0,
                is_available BOOLEAN DEFAULT 1,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP
            )
        ''')
        
        # Create indexes for fast search
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_books_title ON books(title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_books_author ON books(author)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_books_category ON books(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_books_tags ON books(tags)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_books_premium ON books(is_premium)')
        
        # Users Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT DEFAULT 'en',
                is_premium BOOLEAN DEFAULT 0,
                is_admin BOOLEAN DEFAULT 0,
                is_banned BOOLEAN DEFAULT 0,
                total_searches INTEGER DEFAULT 0,
                total_downloads INTEGER DEFAULT 0,
                total_requests INTEGER DEFAULT 0,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP,
                settings TEXT DEFAULT '{}'
            )
        ''')
        
        # Search History
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                results_count INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Download History
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS download_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                book_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (book_id) REFERENCES books (book_id)
            )
        ''')
        
        # Requested Books
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requested_books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                book_title TEXT NOT NULL,
                book_author TEXT,
                status TEXT DEFAULT 'pending',
                upvotes INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fulfilled_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Bot Statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                total_users INTEGER DEFAULT 0,
                total_searches INTEGER DEFAULT 0,
                total_downloads INTEGER DEFAULT 0,
                total_books INTEGER DEFAULT 0,
                peak_concurrent INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        logger.info("✅ Database initialized successfully")
        
        # Create initial admin if owner exists
        from config import Config
        if Config.OWNER_ID:
            self.add_user(
                user_id=Config.OWNER_ID,
                username=Config.OWNER_USERNAME,
                is_admin=True
            )
    
    def add_book(self, book_data: Dict) -> bool:
        """Add a new book to database"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO books (
                    book_id, title, author, description, file_id, file_type,
                    file_size, category, tags, added_by, added_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                book_data.get('book_id', f"book_{datetime.now().timestamp()}"),
                book_data['title'],
                book_data.get('author', 'Unknown'),
                book_data.get('description', ''),
                book_data['file_id'],
                book_data.get('file_type', 'PDF'),
                book_data.get('file_size', 0),
                book_data.get('category', 'General'),
                json.dumps(book_data.get('tags', [])),
                book_data.get('added_by', 0),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            logger.info(f"✅ Book added: {book_data['title']}")
            return True
            
        except sqlite3.IntegrityError:
            logger.warning(f"⚠️ Book already exists: {book_data['title']}")
            return False
        except Exception as e:
            logger.error(f"❌ Error adding book: {e}")
            return False
    
    def search_books(self, query: str, limit: int = 20, offset: int = 0) -> List[Dict]:
        """Search books with advanced filtering"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        search_term = f"%{query}%"
        
        cursor.execute('''
            SELECT * FROM books 
            WHERE (title LIKE ? OR author LIKE ? OR tags LIKE ? OR category LIKE ?)
            AND is_available = 1
            ORDER BY 
                CASE WHEN title LIKE ? THEN 1 ELSE 2 END,
                download_count DESC,
                added_at DESC
            LIMIT ? OFFSET ?
        ''', (
            search_term, search_term, search_term, search_term,
            f"{query}%", limit, offset
        ))
        
        results = []
        for row in cursor.fetchall():
            book = dict(row)
            if book.get('tags'):
                book['tags'] = json.loads(book['tags'])
            results.append(book)
        
        return results
    
    def get_book(self, book_id: str) -> Optional[Dict]:
        """Get book by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM books WHERE book_id = ? AND is_available = 1', (book_id,))
        row = cursor.fetchone()
        
        if row:
            book = dict(row)
            if book.get('tags'):
                book['tags'] = json.loads(book['tags'])
            return book
        
        return None
    
    def add_user(self, user_id: int, username: str = None, 
                first_name: str = None, last_name: str = None,
                is_admin: bool = False) -> bool:
        """Add or update user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users 
                (user_id, username, first_name, last_name, is_admin, last_active)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                last_active = excluded.last_active
            ''', (
                user_id, username, first_name, last_name, 
                is_admin, datetime.now().isoformat()
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def update_user_stats(self, user_id: int, action: str):
        """Update user statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        if action == 'search':
            cursor.execute('''
                UPDATE users SET 
                total_searches = total_searches + 1,
                last_active = ?
                WHERE user_id = ?
            ''', (now, user_id))
            
        elif action == 'download':
            cursor.execute('''
                UPDATE users SET 
                total_downloads = total_downloads + 1,
                last_active = ?
                WHERE user_id = ?
            ''', (now, user_id))
        
        conn.commit()
    
    def get_stats(self) -> Dict:
        """Get comprehensive bot statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total books
        cursor.execute('SELECT COUNT(*) FROM books WHERE is_available = 1')
        stats['total_books'] = cursor.fetchone()[0] or 0
        
        # Total users
        cursor.execute('SELECT COUNT(*) FROM users')
        stats['total_users'] = cursor.fetchone()[0] or 0
        
        # Today's stats
        today = datetime.now().date().isoformat()
        cursor.execute('''
            SELECT total_searches, total_downloads, total_users 
            FROM bot_stats WHERE date = ?
        ''', (today,))
        
        row = cursor.fetchone()
        if row:
            stats['today_searches'] = row[0] or 0
            stats['today_downloads'] = row[1] or 0
            stats['today_new_users'] = row[2] or 0
        else:
            stats['today_searches'] = 0
            stats['today_downloads'] = 0
            stats['today_new_users'] = 0
        
        # Most popular books
        cursor.execute('''
            SELECT title, author, download_count 
            FROM books 
            WHERE is_available = 1 
            ORDER BY download_count DESC 
            LIMIT 5
        ''')
        stats['top_books'] = [
            {"title": row[0], "author": row[1], "downloads": row[2]}
            for row in cursor.fetchall()
        ]
        
        # Most active users
        cursor.execute('''
            SELECT username, total_searches, total_downloads 
            FROM users 
            ORDER BY (total_searches + total_downloads) DESC 
            LIMIT 5
        ''')
        stats['top_users'] = [
            {"username": row[0] or "Anonymous", "searches": row[1], "downloads": row[2]}
            for row in cursor.fetchall()
        ]
        
        return stats
