from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

def create_main_menu(is_admin=False):
    """Create main menu keyboard"""
    buttons = [
        [
            InlineKeyboardButton(f"{Config.get_emoji('search')} Search Books", callback_data="search"),
            InlineKeyboardButton(f"{Config.get_emoji('category')} Categories", callback_data="categories")
        ],
        [
            InlineKeyboardButton(f"{Config.get_emoji('stats')} Statistics", callback_data="stats"),
            InlineKeyboardButton(f"{Config.get_emoji('info')} Help", callback_data="help")
        ]
    ]
    
    if is_admin:
        buttons.append([
            InlineKeyboardButton(f"{Config.get_emoji('crown')} Admin Panel", callback_data="admin")
        ])
    
    return InlineKeyboardMarkup(buttons)

def create_search_results_keyboard(books, page=0, total_pages=1):
    """Create keyboard for search results"""
    keyboard = []
    
    # Add book buttons
    for book in books:
        title = book.get('title', 'Unknown')[:25]
        emoji = Config.get_emoji('star') if book.get('is_premium') else Config.get_emoji('book')
        keyboard.append([
            InlineKeyboardButton(
                f"{emoji} {title}",
                callback_data=f"book_{book.get('book_id')}"
            )
        ])
    
    # Add pagination if needed
    if total_pages > 1:
        pagination = []
        if page > 0:
            pagination.append(InlineKeyboardButton(f"{Config.get_emoji('prev')} Previous", callback_data=f"page_{page-1}"))
        
        pagination.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="current_page"))
        
        if page < total_pages - 1:
            pagination.append(InlineKeyboardButton(f"Next {Config.get_emoji('next')}", callback_data=f"page_{page+1}"))
        
        keyboard.append(pagination)
    
    # Add navigation buttons
    keyboard.append([
        InlineKeyboardButton(f"{Config.get_emoji('search')} New Search", callback_data="new_search"),
        InlineKeyboardButton(f"{Config.get_emoji('home')} Main Menu", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_book_details_keyboard(book_id, is_owner=False):
    """Create keyboard for book details"""
    buttons = [
        [
            InlineKeyboardButton(f"{Config.get_emoji('download')} Download", callback_data=f"download_{book_id}"),
            InlineKeyboardButton(f"{Config.get_emoji('search')} Similar", callback_data=f"similar_{book_id}")
        ],
        [
            InlineKeyboardButton(f"{Config.get_emoji('heart')} Save", callback_data=f"save_{book_id}"),
            InlineKeyboardButton(f"{Config.get_emoji('back')} Back", callback_data="back_results")
        ]
    ]
    
    if is_owner:
        buttons.append([
            InlineKeyboardButton(f"{Config.get_emoji('settings')} Edit", callback_data=f"edit_{book_id}"),
            InlineKeyboardButton(f"{Config.get_emoji('error')} Delete", callback_data=f"delete_{book_id}")
        ])
    
    return InlineKeyboardMarkup(buttons)