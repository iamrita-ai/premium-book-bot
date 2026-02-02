markdown
# 📚 Telegram Book Bot

A feature-rich Telegram bot for distributing e-books with premium features, auto-delete privacy system, and admin tools.

## 🚀 Features

### ✨ Premium Features
- 🔍 **Smart Search** with pagination and filters
- 🎭 **Universal Reaction System** (context-aware emojis)
- 🗑️ **Auto-Delete Privacy** (search results auto-clean)
- 📊 **Advanced Analytics** (daily reports, user stats)
- 💾 **Wishlist System** (save books for later)
- 🔔 **Broadcast System** (send announcements to all users)
- 🛡️ **Maintenance Mode** (controlled downtime)

### 👑 Admin Features
- 📤 **Batch Upload** (process multiple files)
- 📢 **Broadcast with Progress** (real-time tracking)
- 🔒 **Lock/Unlock** (maintenance control)
- 📊 **Detailed Statistics** (user analytics)
- 🧹 **Auto-Cleanup** (cache and temp files)

### 🎨 User Experience
- 📱 **Responsive Design** (works on all devices)
- ⚡ **Fast Delivery** (optimized file sharing)
- 🎯 **Smart Recommendations** (similar books)
- 🏆 **Achievement System** (user badges)
- 🔄 **Pagination** (browse large result sets)

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Telegram Bot Token (from @BotFather)
- MongoDB Atlas account (for production)

### Local Setup

Install Dependencies

bash
pip install -r requirements.txt
Configure Environment

bash
cp .env.example .env
# Edit .env with your credentials
Run Bot

bash
python bot.py
Run Web Server (optional)

bash
python app.py
🌐 Deployment on Render.com

Step 1: Prepare Repository
Fork/Create a GitHub repository

Add all files from this project

Ensure Procfile and requirements.txt are present

Step 2: Create Render Service
Go to Render.com

Click "New +" → "Web Service"

Connect your GitHub repository

Configure settings:

Name: book-bot

Environment: Python 3

Build Command: pip install -r requirements.txt

Start Command: python bot.py & gunicorn app:app --bind 0.0.0.0:$PORT

Add environment variables from .env.example

Step 3: Configure MongoDB Atlas
Create free cluster at MongoDB Atlas

Get connection string

Add to Render environment variables:

text
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/book_bot
Step 4: Deploy


Step 4: Deploy
Click "Create Web Service"

Wait for deployment

Check logs for any errors

⚙️ Environment Variables
Variable	Description	Required
BOT_TOKEN	Telegram Bot Token from @BotFather	✅
API_ID	Telegram API ID from my.telegram.org	✅
API_HASH	Telegram API Hash from my.telegram.org	✅
DATABASE_CHANNEL_ID	Channel ID for storing files (with -100)	✅
LOG_CHANNEL_ID	Channel ID for logs (with -100)	✅
OWNER_ID	Your Telegram User ID	✅
MONGO_URI	MongoDB connection string	✅ (for production)
REACTION_PROBABILITY	Chance to add reactions (0.0-1.0)	❌
AUTO_DELETE_SEARCHES	Auto-delete search results (true/false)	❌

📖 Usage Guide
User Commands
text
/start - Start the bot
/books <name> - Search books
/books <name> -p <page> - Search with pagination
/categories - Browse by category
/trending - Popular books
/save <book_id> - Save to wishlist
/wishlist - View saved books
/random - Get random book
/stats - Your statistics
/help - Show help
Admin Commands
text
/broadcast <message> - Broadcast to all users
/lock - Enable maintenance mode
/unlock - Disable maintenance mode
/backup - Create database backup
/users - User management
/logs - View system logs
File Upload
Send any PDF/EPUB file to bot

Bot automatically extracts metadata

File is added to database

Available for search immediately

📁 Project Structure

Project Structure
text
book-bot/
├── bot.py              # Main bot file
├── app.py              # Flask web server
├── requirements.txt    # Dependencies
├── Procfile           # Render configuration
├── .env.example       # Environment template
├── README.md          # This file
└── database/          # Database models
🔧 Advanced Configuration
Customizing Reactions
Edit reaction_sets in ReactionSystem class:

python
self.reaction_sets = {
    'text': ['🔥', '⭐', '🎯'],
    'document': ['📚', '📖'],
    # Add your own sets
}
Adjusting Auto-Delete Time
Change in SearchManager class:

python
# Current: 10 minutes (600 seconds)
await asyncio.sleep(600)
# Change to 5 minutes:
await asyncio.sleep(300)
Enabling/Disabling Features

Enabling/Disabling Features
Set in .env file:

text
AUTO_DELETE_SEARCHES=false
REACTION_PROBABILITY=0.0
ENABLE_BROADCAST=false
🚨 Troubleshooting
Bot Not Starting
Check BOT_TOKEN is correct

Verify API_ID and API_HASH

Check MongoDB connection

Files Not Sending
Ensure bot is admin in database channel

Check file permissions

Verify database channel ID format (-100 prefix)

Search Not Working
Check MongoDB indexes

Verify text search is enabled

Clear cache with /cleanup (admin)

Web Dashboard Not Loading
Check PORT environment variable

Verify Flask is running

Check Render logs

📊 Monitoring

Monitoring
Health Check
text
https://your-app.onrender.com/health
Web Dashboard
text
https://your-app.onrender.com/
API Endpoints
/api/stats - Bot statistics

/health - Health check

🔒 Security
Privacy Features
Search results auto-delete

No user data sold/shared

Encrypted backups

Rate limiting

Admin Security
Owner-only commands

Maintenance mode

Activity logging

Backup encryption

Contributing
Fork the repository

Create feature branch

Commit changes

Push to branch

Create Pull Request

📄 License
MIT License - see LICENSE file

🙏 Credits
Pyrogram - Telegram MTProto API

MongoDB - Database

Render - Hosting

Flask - Web framework

📞 Support
Issues: GitHub Issues

Telegram: @YourUsername

Email: your-email@example.com

Made with ❤️ for the reading community

. Deployment Checklist
Before Deployment
Get Telegram Bot Token from @BotFather

Get API ID & Hash from my.telegram.org

Create Telegram channel for database (-100XXX)

Create MongoDB Atlas account

Set up database indexes

Test locally

Render Deployment Steps
Create New Web Service on Render

Connect GitHub Repository

Configure Settings:

Name: book-bot

Environment: Python 3

Region: Singapore (or closest to users)

Branch: main

Root Directory: (leave empty)

Set Build Command: pip install -r requirements.txt

Set Start Command: python bot.py & gunicorn app:app --bind 0.0.0.0:$PORT

Add Environment Variables: Copy from .env.example

Advanced: Add Auto-Deploy from main branch

Click Create Web Service

Post-Deployment Verification

Post-Deployment Verification
Check Logs in Render dashboard

Send /start to your bot

Test Search: /books python

Test File Upload (as admin)

Check Web Dashboard: https://your-app.onrender.com

Verify Health Check: https://your-app.onrender.com/health

