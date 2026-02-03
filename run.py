#!/usr/bin/env python3
"""
RUN.PY - Main entry point for Render deployment
This file ensures the bot runs continuously
"""

import os
import sys
import asyncio
import logging

print("=" * 50)
print("🚀 TELEGRAM BOOK BOT - RENDER DEPLOYMENT")
print("=" * 50)
print("📦 Initializing...")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Check environment variables
required_vars = [
    "BOT_TOKEN",
    "API_ID", 
    "API_HASH",
    "MONGO_URI",
    "DATABASE_CHANNEL_ID"
]

missing_vars = []
for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)

if missing_vars:
    print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
    print("💡 Please add them in Render dashboard")
    sys.exit(1)

print("✅ Environment variables checked")

try:
    # Import and run the bot
    print("🤖 Importing bot module...")
    from bot import main
    
    # Run the bot
    print("▶️ Starting bot main loop...")
    asyncio.run(main())
    
except KeyboardInterrupt:
    print("\n👋 Bot stopped by user")
    sys.exit(0)
except Exception as e:
    print(f"❌ Bot error: {str(e)}")
    sys.exit(1)
