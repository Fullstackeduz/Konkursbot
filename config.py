import os
from typing import List

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# Admin Configuration
ADMIN_IDS: List[int] = [
    5997189940,  # Main admin
]

# Database Configuration
DATABASE_PATH = 'bot_database.db'

# Bot Messages
MESSAGES = {
    'start_welcome': """👋 Salom! Konkursga xush kelibsiz!

🚀 Loyihada ishtirok etish uchun quyidagi kanallarga azo boʼling.
Keyin ✅ А'zo bo'ldim tugmasini bosing.
⚠️ Yopiq kanallarga ulanish soʼrovini yuborishingiz kifoya.""",
    
    'not_subscribed': """❌ Siz hali barcha kanallarga obuna bo'lmagansiz!

🚀 Loyihada ishtirok etish uchun quyidagi kanallarga azo boʼling.
Keyin ✅ А'zo bo'ldim tugmasini bosing.
⚠️ Yopiq kanallarga ulanish soʼrovini yuborishingiz kifoya.""",
    
    'phone_request': """📱 Iltimos, telefon raqamingizni yuboring.
Faqat +998 bilan boshlanadigan raqamlar qabul qilinadi.

Masalan: +998901234567""",
    
    'invalid_phone': """❌ Kechirasiz, faqat O'zbekiston raqamlarini qabul qilamiz.
Iltimos, +998 bilan boshlanadigan raqam kiriting.""",
    
    'registration_success': """✅ Tabriklaymiz! Siz muvaffaqiyatli ro'yxatdan o'tdingiz!
🎁 Sizga 2 ball berildi!

Endi botning barcha imkoniyatlaridan foydalanishingiz mumkin.""",
    
    'main_menu': """🏠 Bosh menyu

Quyidagi tugmalardan birini tanlang:""",
    
    'contest_info': """🔴 Konkurs haqida ma'lumot

Bu matn admin panelidan tahrirlash mumkin.""",
    
    'referral_info': """👆 Referal havolangiz:
{referral_link}

Har bir do'stingiz ushbu havola orqali ro'yxatdan o'tsa, sizga 2 ball qo'shiladi!
🎁 Ball toplang va g'olib bo'ling!""",
    
    'gifts_info': """🎁 Sovg'alar

Bu matn admin panelidan tahrirlash mumkin.""",
    
    'terms_info': """💡 Konkurs shartlari

Bu matn admin panelidan tahrirlash mumkin.""",
    
    'user_balance': """👤 Sizning ballaringiz: {balance} ball
📊 Sizning o'rningiz: {rank}-chi""",
    
    'rating_header': """📊 TOP 20 REYTING

🏆 Eng faol foydalanuvchilar:""",
    
    'admin_panel': """🗄 Admin paneli

Boshqaruv paneliga xush kelibsiz!""",
    
    'admin_not_allowed': """❌ Sizda admin huquqlari yo'q!""",
}

# Default admin panel texts
DEFAULT_TEXTS = {
    'contest_info': """🔴 **Konkurs haqida**

🎯 Maqsad: Eng ko'p ball to'plash
⏰ Muddat: Aniqlanmagan
🏆 Mukofotlar: Tez orada e'lon qilinadi

📝 Qoidalar:
• Referal orqali do'st taklif qiling (+2 ball)
• Faol bo'ling va g'olib bo'ling!""",
    
    'gifts_info': """🎁 **Sovg'alar ro'yxati**

🥇 1-o'rin: 1,000,000 so'm
🥈 2-o'rin: 500,000 so'm  
🥉 3-o'rin: 250,000 so'm

🎯 4-10 o'rin: 100,000 so'm
🎁 11-20 o'rin: 50,000 so'm""",
    
    'terms_info': """💡 **Konkurs shartlari**

✅ Ro'yxatdan o'tish majburiy
✅ Faqat +998 raqamlar qabul qilinadi
✅ Har bir referal uchun +2 ball
✅ Soxta account yaratish taqiqlanadi
✅ Adminlar qarorida e'tiroz bildirib bo'lmaydi

⚠️ Qoidabuzarlik aniqlansa, diskvalifikatsiya qilinadi."""
}

# Registration bonus
REGISTRATION_BONUS = 2
REFERRAL_BONUS = 2

# Subscription check settings
CHECK_SUBSCRIPTIONS = True
SUBSCRIPTION_CHECK_INTERVAL = 300  # 5 minutes

# Rate limiting
MAX_MESSAGES_PER_MINUTE = 30

# Excel export settings
EXCEL_MAX_ROWS = 100000

# Pagination settings
USERS_PER_PAGE = 20
RATING_TOP_COUNT = 20

# Channel subscription messages
SUBSCRIPTION_MESSAGES = {
    'check_button': '✅ А\'zo bo\'ldim',
    'join_channel': '📢 Kanalga qo\'shilish',
    'join_group': '👥 Guruhga qo\'shilish'
}