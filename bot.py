#!/usr/bin/env python3
"""
Database setup script
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "book_bot")

def setup_database():
    print("📦 Setting up Book Bot database...")
    
    try:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB")
        
        # Create collections if they don't exist
        collections = db.list_collection_names()
        
        if 'books' not in collections:
            db.create_collection('books')
            print("✅ Created 'books' collection")
        
        if 'users' not in collections:
            db.create_collection('users')
            print("✅ Created 'users' collection")
        
        if 'stats' not in collections:
            db.create_collection('stats')
            print("✅ Created 'stats' collection")
        
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
            {"key": "total_downloads", "value": 0}
        ]
        
        for stat in default_stats:
            db.stats.update_one(
                {"key": stat["key"]},
                {"$setOnInsert": stat},
                upsert=True
            )
        
        print("✅ Added default statistics")
        print("\n🎉 Database setup completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    setup_database()