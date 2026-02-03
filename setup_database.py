#!/usr/bin/env python3
"""
SETUP_DATABASE.PY - One-time database setup
Run this manually or during first deployment
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
    """Create database indexes and collections"""
    
    print("=" * 50)
    print("📦 DATABASE SETUP FOR BOOK BOT")
    print("=" * 50)
    
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
        else:
            print("📚 'books' collection already exists")
        
        # Users collection
        if 'users' not in collections:
            db.create_collection('users')
            print("✅ Created 'users' collection")
        else:
            print("👥 'users' collection already exists")
        
        # Stats collection
        if 'stats' not in collections:
            db.create_collection('stats')
            print("✅ Created 'stats' collection")
        else:
            print("📈 'stats' collection already exists")
        
        # Create indexes
        db.books.create_index([("title", "text"), ("author", "text"), ("category", "text")])
        db.books.create_index([("id", 1)], unique=True)
        db.users.create_index([("id", 1)], unique=True)
        db.stats.create_index([("key", 1)], unique=True)
        
        print("✅ Created indexes")
        
        # Add default stats
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
        
        # Show summary
        print("\n" + "=" * 50)
        print("📊 DATABASE SUMMARY")
        print("=" * 50)
        
        total_books = db.books.count_documents({})
        total_users = db.users.count_documents({})
        
        print(f"📚 Total Books: {total_books}")
        print(f"👥 Total Users: {total_users}")
        
        # Show sample stats
        print("\n📈 Current Statistics:")
        for stat in default_stats:
            doc = db.stats.find_one({"key": stat["key"]})
            value = doc.get("value", 0) if doc else 0
            print(f"  • {stat['key']}: {value}")
        
        print("\n" + "=" * 50)
        print("🎉 DATABASE SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        
    except ConnectionFailure as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("\n💡 TROUBLESHOOTING:")
        print("1. Check MONGO_URI in .env file")
        print("2. Ensure MongoDB server is running")
        print("3. For MongoDB Atlas, check network access")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()
