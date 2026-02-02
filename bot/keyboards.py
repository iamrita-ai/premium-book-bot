from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional

class KeyboardBuilder:
    """Premium keyboard builder with modern design"""
    
    @staticmethod
    def main_menu(user_id: int = None, is_admin: bool = False):
        """Main menu keyboard"""
        buttons = [
            [InlineKeyboardButton("🔍 Search Books", callback_data="search")],
            [InlineKeyboardButton("📚 Browse Categories", callback_data="categories")],
            [InlineKeyboardButton("⭐ Top Books", callback_data="top_books")],
            [InlineKeyboardButton("📤 Request Book", callback_data="request_book")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help"),
             InlineKeyboardButton("📊 Stats", callback_data="stats")]
        ]
        
        if is_admin:
            buttons.append([
                InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")
            ])
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def search_results(results: List[dict], page: int = 0, total_pages: int = 1):
        """Search results pagination keyboard"""
        keyboard = []
        
        # Add book buttons
        for book in results:
            title = book.get('title', 'Unknown')[:30]
            emoji = "⭐" if book.get('is_premium') else "📖"
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {title}",
                    callback_data=f"book_{book.get('book_id')}"
                )
            ])
        
        # Pagination buttons
        pagination = []
        if page > 0:
            pagination.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"page_{page-1}"))
        
        pagination.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="current_page"))
        
        if page < total_pages - 1:
            pagination.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_{page+1}"))
        
        if pagination:
            keyboard.append(pagination)
        
        # Navigation buttons
        keyboard.append([
            InlineKeyboardButton("🔍 New Search", callback_data="new_search"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def book_details(book_id: str, is_owner: bool = False):
        """Book details action keyboard"""
        buttons = [
            [
                InlineKeyboardButton("📥 Download", callback_data=f"download_{book_id}"),
                InlineKeyboardButton("🔍 Similar", callback_data=f"similar_{book_id}")
            ],
            [
                InlineKeyboardButton("❤️ Save", callback_data=f"save_{book_id}"),
                InlineKeyboardButton("📤 Share", callback_data=f"share_{book_id}")
            ],
            [InlineKeyboardButton("🔙 Back to Results", callback_data="back_results")]
        ]
        
        if is_owner:
            buttons.append([
                InlineKeyboardButton("✏️ Edit", callback_data=f"edit_{book_id}"),
                InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{book_id}")
            ])
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def categories():
        """Book categories keyboard"""
        categories = [
            "📚 Fiction", "🔬 Science", "💻 Technology", "📈 Business",
            "🏥 Health", "🎨 Arts", "📖 Education", "🌍 Travel",
            "🍳 Cooking", "🏋️ Fitness", "🧘 Wellness", "💰 Finance"
        ]
        
        keyboard = []
        row = []
        for i, category in enumerate(categories, 1):
            row.append(InlineKeyboardButton(category, callback_data=f"cat_{category[2:]}"))
            if i % 2 == 0:
                keyboard.append(row)
                row = []
        
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_panel():
        """Admin panel keyboard"""
        buttons = [
            [InlineKeyboardButton("📊 System Stats", callback_data="admin_stats")],
            [InlineKeyboardButton("📦 Add Book", callback_data="admin_add_book")],
            [InlineKeyboardButton("👥 User Management", callback_data="admin_users")],
            [InlineKeyboardButton("⚙️ Bot Settings", callback_data="admin_settings")],
            [InlineKeyboardButton("💾 Database Backup", callback_data="admin_backup")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def confirmation(action: str, item_id: str):
        """Confirmation dialog keyboard"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Yes", callback_data=f"confirm_{action}_{item_id}"),
                InlineKeyboardButton("❌ No", callback_data=f"cancel_{action}_{item_id}")
            ]
        ])
