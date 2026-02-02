import sqlite3
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path="/tmp/book_bot.db"):
        self.db_path = db_path
    
    def initialize(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Books table
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
                category TEXT DEFAULT 'General',
                tags TEXT,
                is_premium BOOLEAN DEFAULT 0,
                is_available BOOLEAN DEFAULT 1,
                download_count INTEGER DEFAULT 0,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                total_searches INTEGER DEFAULT 0,
                total_downloads INTEGER DEFAULT 0,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON books(title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_author ON books(author)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON books(category)')
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Database tables created")
        
        # Add sample books for testing
        self._add_sample_books()
    
    def _add_sample_books(self):
        """Add sample books for testing"""
        sample_books = [
            {
                'title': 'Python Programming Guide',
                'author': 'John Doe',
                'description': 'Complete guide to Python programming',
                'file_id': 'sample1',
                'file_type': 'PDF',
                'file_size': 2500000,
                'category': 'Programming',
                'tags': ['python', 'programming', 'guide']
            },
            {
                'title': 'Advanced Python Techniques',
                'author': 'Jane Smith',
                'description': 'Advanced Python programming concepts',
                'file_id': 'sample2',
                'file_type': 'PDF',
                'file_size': 3100000,
                'category': 'Programming',
                'tags': ['python', 'advanced', 'techniques']
            },
            {
                'title': 'Web Development with Django',
                'author': 'Mike Johnson',
                'description': 'Build web applications with Django',
                'file_id': 'sample3', 
                'file_type': 'PDF',
                'file_size': 4200000,
                'category': 'Web Development',
                'tags': ['django', 'web', 'python']
            }
        ]
        
        for book in sample_books:
            self.add_book(book)
    
    def add_book(self, book_data):
        """Add a book to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        import time
        book_id = f"book_{int(time.time())}"
        
        cursor.execute('''
            INSERT OR IGNORE INTO books 
            (book_id, title, author, description, file_id, file_type, 
             file_size, category, tags, added_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            book_id,
            book_data.get('title', 'Unknown'),
            book_data.get('author', 'Unknown'),
            book_data.get('description', ''),
            book_data.get('file_id', ''),
            book_data.get('file_type', 'PDF'),
            book_data.get('file_size', 0),
            book_data.get('category', 'General'),
            json.dumps(book_data.get('tags', [])),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"📚 Book added: {book_data.get('title')}")
        return True
    
    def search_books(self, query, limit=10):
        """Search books in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        search_term = f"%{query}%"
        
        cursor.execute('''
            SELECT * FROM books 
            WHERE (title LIKE ? OR author LIKE ? OR category LIKE ?)
            AND is_available = 1
            ORDER BY download_count DESC
            LIMIT ?
        ''', (search_term, search_term, search_term, limit))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            book = dict(zip(columns, row))
            if book.get('tags'):
                try:
                    book['tags'] = json.loads(book['tags'])
                except:
                    book['tags'] = []
            results.append(book)
        
        conn.close()
        return results
    
    def get_book(self, book_id):
        """Get book by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM books WHERE book_id = ? AND is_available = 1', (book_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            book = dict(zip(columns, row))
            if book.get('tags'):
                try:
                    book['tags'] = json.loads(book['tags'])
                except:
                    book['tags'] = []
            conn.close()
            return book
        
        conn.close()
        return None
    
    def add_user(self, user_id, username=None, first_name=None, last_name=None):
        """Add or update user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, last_name, last_active)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            last_active = excluded.last_active
        ''', (user_id, username, first_name, last_name, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True
    
    def update_user_stats(self, user_id, action):
        """Update user statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if action == 'search':
            cursor.execute('''
                UPDATE users SET 
                total_searches = total_searches + 1,
                last_active = ?
                WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_id))
        elif action == 'download':
            cursor.execute('''
                UPDATE users SET 
                total_downloads = total_downloads + 1,
                last_active = ?
                WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
    
    def get_stats(self):
        """Get bot statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total books
        cursor.execute('SELECT COUNT(*) FROM books WHERE is_available = 1')
        total_books = cursor.fetchone()[0] or 0
        
        # Total users
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0] or 0
        
        # Total searches
        cursor.execute('SELECT SUM(total_searches) FROM users')
        total_searches = cursor.fetchone()[0] or 0
        
        # Total downloads
        cursor.execute('SELECT SUM(total_downloads) FROM users')
        total_downloads = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_books': total_books,
            'total_users': total_users,
            'total_searches': total_searches,
            'total_downloads': total_downloads
        }