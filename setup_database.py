#!/usr/bin/env python3
"""
Database setup script - Simplified version
"""

import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "book_bot")

def setup_database():
    """Create database indexes"""
    
    print("📦 Setting up Book Bot database...")
    
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB")
        
        db = client[DATABASE_NAME]
        
        # Create collections if they don't exist
        collections = db.list_collection_names()
        
        # Books collection
        if 'books' not in collections:
            db.create_collection('books')
            print("✅ Created 'books' collection")
        
        # Create text index for books
        db.books.create_index([("title", "text"), ("author", "text"), ("category", "text")])
        db.books.create_index([("id", 1)], unique=True)
        print("✅ Created indexes for 'books'")
        
        # Users collection
        if 'users' not in collections:
            db.create_collection('users')
            print("✅ Created 'users' collection")
        
        db.users.create_index([("id", 1)], unique=True)
        print("✅ Created indexes for 'users'")
        
        # Stats collection
        if 'stats' not in collections:
            db.create_collection('stats')
            print("✅ Created 'stats' collection")
        
        db.stats.create_index([("key", 1)], unique=True)
        
        # Insert default stats
        default_stats = [
            {"key": "total_books", "value": 0},
            {"key": "total_users", "value": 0},
            {"key": "total_searches", "value": 0},
            {"key": "total_downloads", "value": 0},
            {"key": "active_users_today", "value": 0}
        ]
        
        for stat in default_stats:
            db.stats.update_one(
                {"key": stat["key"]},
                {"$setOnInsert": stat},
                upsert=True
            )
        
        print("✅ Added default statistics")
        
        print(f"\n🎉 Database setup completed successfully!")
        print(f"📊 Database: {DATABASE_NAME}")
        print(f"📁 Collections: books, users, stats")
        
        # Show sample data
        print(f"\n📚 Sample stats:")
        for stat in default_stats:
            doc = db.stats.find_one({"key": stat["key"]})
            print(f"  • {stat['key']}: {doc.get('value', 0)}")
        
    except ConnectionFailure as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("\n💡 Please check:")
        print("1. MONGO_URI in .env file")
        print("2. MongoDB server is running")
        print("3. Network connectivity")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()
