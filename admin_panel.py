from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramAPIError
import asyncio
from typing import List, Dict
import pandas as pd
from datetime import datetime
import os

from database import db
from config import ADMIN_IDS, DEFAULT_TEXTS
from stats import StatsManager

# Router for admin handlers
admin_router = Router()

# Admin FSM States
class AdminStates(StatesGroup):
    main_panel = State()
    user_management = State()
    statistics = State()
    messaging = State()
    message_compose = State()
    message_target = State()
    subscription_management = State()
    add_subscription = State()
    contest_management = State()
    text_editing = State()
    edit_contest_text = State()
    edit_gifts_text = State()
    edit_terms_text = State()
    user_search = State()
    add_admin = State()
    broadcast_message = State()
    single_message = State()
    single_message_target = State()

def create_admin_main_keyboard() -> InlineKeyboardMarkup:
    """Create admin main panel keyboard"""
    keyboard = [
        [InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users"),
         InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="💬 Xabar yuborish", callback_data="admin_messaging"),
         InlineKeyboardButton(text="📢 Obunalar", callback_data="admin_subscriptions")],
        [InlineKeyboardButton(text="🏆 Konkurs", callback_data="admin_contest"),
         InlineKeyboardButton(text="📝 Matnlar", callback_data="admin_texts")],
        [InlineKeyboardButton(text="🔍 Qidirish", callback_data="admin_search"),
         InlineKeyboardButton(text="⚙️ Adminlar", callback_data="admin_admins")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_user_management_keyboard() -> InlineKeyboardMarkup:
    """Create user management keyboard"""
    keyboard = [
        [InlineKeyboardButton(text="👤 Foydalanuvchi qidirish", callback_data="search_user"),
         InlineKeyboardButton(text="📋 Ro'yxat", callback_data="user_list")],
        [InlineKeyboardButton(text="📊 Faol foydalanuvchilar", callback_data="active_users"),
         InlineKeyboardButton(text="📈 Yangi foydalanuvchilar", callback_data="new_users")],
        [InlineKeyboardButton(text="📄 Excel eksport", callback_data="export_users")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_stats_keyboard() -> InlineKeyboardMarkup:
    """Create statistics keyboard"""
    keyboard = [
        [InlineKeyboardButton(text="📅 Bugun", callback_data="stats_today"),
         InlineKeyboardButton(text="📅 Hafta", callback_data="stats_week")],
        [InlineKeyboardButton(text="📅 Oy", callback_data="stats_month"),
         InlineKeyboardButton(text="📊 Umumiy", callback_data="stats_all")],
        [InlineKeyboardButton(text="👆 Top referrallar", callback_data="top_referrers"),
         InlineKeyboardButton(text="📈 O'sish dinamikasi", callback_data="growth_stats")],
        [InlineKeyboardButton(text="📄 Excel yuklab olish", callback_data="export_stats")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_messaging_keyboard() -> InlineKeyboardMarkup:
    """Create messaging keyboard"""
    keyboard = [
        [InlineKeyboardButton(text="📢 Hammaga yuborish", callback_data="broadcast_all"),
         InlineKeyboardButton(text="👤 Bitta foydalanuvchi", callback_data="message_single")],
        [InlineKeyboardButton(text="📊 Yuborilgan xabarlar", callback_data="message_stats")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_subscription_keyboard() -> InlineKeyboardMarkup:
    """Create subscription management keyboard"""
    keyboard = [
        [InlineKeyboardButton(text="📋 Obunalar ro'yxati", callback_data="subscription_list"),
         InlineKeyboardButton(text="➕ Qo'shish", callback_data="add_subscription")],
        [InlineKeyboardButton(text="🗑 O'chirish", callback_data="remove_subscription")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_contest_keyboard() -> InlineKeyboardMarkup:
    """Create contest management keyboard"""
    keyboard = [
        [InlineKeyboardButton(text="▶️ Konkursni boshlash", callback_data="start_contest"),
         InlineKeyboardButton(text="⏹ To'xtatish", callback_data="stop_contest")],
        [InlineKeyboardButton(text="🔄 Ballarni nollash", callback_data="reset_balances"),
         InlineKeyboardButton(text="🏆 Top 20 g'olib", callback_data="contest_winners")],
        [InlineKeyboardButton(text="📊 Konkurs statistikasi", callback_data="contest_stats")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_text_editing_keyboard() -> InlineKeyboardMarkup:
    """Create text editing keyboard"""
    keyboard = [
        [InlineKeyboardButton(text="🔴 Konkurs matni", callback_data="edit_contest_text"),
         InlineKeyboardButton(text="🎁 Sovg'alar matni", callback_data="edit_gifts_text")],
        [InlineKeyboardButton(text="💡 Shartlar matni", callback_data="edit_terms_text")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_admin_management_keyboard() -> InlineKeyboardMarkup:
    """Create admin management keyboard"""
    keyboard = [
        [InlineKeyboardButton(text="👥 Adminlar ro'yxati", callback_data="admin_list"),
         InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="add_admin_user")],
        [InlineKeyboardButton(text="➖ Admin o'chirish", callback_data="remove_admin_user")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def show_admin_panel(message: Message):
    """Show main admin panel"""
    if not db.is_admin(message.from_user.id) and message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Sizda admin huquqlari yo'q!")
        return
    
    text = "🗄 **ADMIN PANELI**\n\nQuyidagi bo'limlardan birini tanlang:"
    keyboard = create_admin_main_keyboard()
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

# Main admin panel handlers
@admin_router.callback_query(F.data == "admin_panel")
async def callback_admin_panel(callback: CallbackQuery, state: FSMContext):
    """Show admin panel"""
    await callback.answer()
    text = "🗄 **ADMIN PANELI**\n\nQuyidagi bo'limlardan birini tanlang:"
    keyboard = create_admin_main_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(AdminStates.main_panel)

@admin_router.callback_query(F.data == "admin_users")
async def callback_user_management(callback: CallbackQuery, state: FSMContext):
    """Show user management panel"""
    await callback.answer()
    
    total_users = db.get_total_users()
    active_today = db.get_active_users_count(1)
    active_week = db.get_active_users_count(7)
    
    text = f"👥 **FOYDALANUVCHILAR BOSHQARUVI**\n\n"
    text += f"📊 Umumiy foydalanuvchilar: {total_users}\n"
    text += f"🟢 Bugun faol: {active_today}\n"
    text += f"📅 Hafta davomida faol: {active_week}\n\n"
    text += "Quyidagi amallardan birini tanlang:"
    
    keyboard = create_user_management_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(AdminStates.user_management)

@admin_router.callback_query(F.data == "admin_stats")
async def callback_statistics(callback: CallbackQuery, state: FSMContext):
    """Show statistics panel"""
    await callback.answer()
    
    stats_manager = StatsManager()
    today_stats = stats_manager.get_daily_stats()
    week_stats = stats_manager.get_weekly_stats()
    
    text = f"📊 **STATISTIKA**\n\n"
    text += f"📅 **Bugun:**\n"
    text += f"  👤 Yangi: {today_stats['new_users']}\n"
    text += f"  🟢 Faol: {today_stats['active_users']}\n"
    text += f"  💬 Xabarlar: {today_stats['messages_sent']}\n"
    text += f"  👆 Referrallar: {today_stats['referrals_made']}\n\n"
    text += f"📅 **Bu hafta:**\n"
    text += f"  👤 Yangi: {week_stats['new_users']}\n"
    text += f"  💬 Xabarlar: {week_stats['messages_sent']}\n"
    text += f"  👆 Referrallar: {week_stats['referrals_made']}\n"
    
    keyboard = create_stats_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(AdminStates.statistics)

@admin_router.callback_query(F.data == "admin_messaging")
async def callback_messaging(callback: CallbackQuery, state: FSMContext):
    """Show messaging panel"""
    await callback.answer()
    
    text = "💬 **XABAR YUBORISH**\n\n"
    text += "Quyidagi variantlardan birini tanlang:"
    
    keyboard = create_messaging_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(AdminStates.messaging)

@admin_router.callback_query(F.data == "admin_subscriptions")
async def callback_subscriptions(callback: CallbackQuery, state: FSMContext):
    """Show subscription management panel"""
    await callback.answer()
    
    subscriptions = db.get_mandatory_subscriptions()
    
    text = f"📢 **OBUNALAR BOSHQARUVI**\n\n"
    text += f"📊 Jami majburiy obunalar: {len(subscriptions)}\n\n"
    
    if subscriptions:
        text += "**Hozirgi obunalar:**\n"
        for sub in subscriptions[:5]:  # Show only first 5
            channel_name = sub['channel_title'] or sub['channel_username'] or f"ID: {sub['channel_id']}"
            status = "🔒 Yopiq" if sub['is_private'] else "🔓 Ochiq"
            text += f"• {channel_name} ({status})\n"
        
        if len(subscriptions) > 5:
            text += f"... va yana {len(subscriptions) - 5} ta obuna\n"
    else:
        text += "❌ Hech qanday majburiy obuna yo'q\n"
    
    text += "\nQuyidagi amallardan birini tanlang:"
    
    keyboard = create_subscription_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(AdminStates.subscription_management)

@admin_router.callback_query(F.data == "admin_contest")
async def callback_contest_management(callback: CallbackQuery, state: FSMContext):
    """Show contest management panel"""
    await callback.answer()
    
    stats_manager = StatsManager()
    contest_stats = stats_manager.get_contest_statistics()
    contest_active = stats_manager.is_contest_active()
    
    text = f"🏆 **KONKURS BOSHQARUVI**\n\n"
    text += f"📊 **Hozirgi holat:**\n"
    status_text = '✅ Faol' if contest_active else '⏹ To\'xtatilgan'
    text += f"🎯 Status: {status_text}\n"
    text += f"👥 Ishtirokchilar: {contest_stats['total_participants']}\n"
    text += f"🎁 Tarqatilgan balllar: {contest_stats['total_points_distributed']}\n"
    text += f"📊 O'rtacha ball: {contest_stats['average_points']}\n\n"
    text += "Quyidagi amallardan birini tanlang:"
    
    keyboard = create_contest_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(AdminStates.contest_management)

@admin_router.callback_query(F.data == "admin_texts")
async def callback_text_editing(callback: CallbackQuery, state: FSMContext):
    """Show text editing panel"""
    await callback.answer()
    
    text = "📝 **MATNLARNI TAHRIRLASH**\n\n"
    text += "Qaysi matnni tahrirlashni xohlaysiz?"
    
    keyboard = create_text_editing_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(AdminStates.text_editing)

@admin_router.callback_query(F.data == "admin_search")
async def callback_user_search(callback: CallbackQuery, state: FSMContext):
    """Handle user search"""
    await callback.answer()
    
    text = "🔍 **FOYDALANUVCHI QIDIRISH**\n\n"
    text += "Qidirishni boshlash uchun quyidagilardan birini kiriting:\n"
    text += "• Foydalanuvchi ID raqami\n"
    text += "• Username (@username)\n"
    text += "• Ism yoki familiya\n\n"
    text += "Masalan: 123456789 yoki @username yoki Alisher"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(AdminStates.user_search)

@admin_router.callback_query(F.data == "admin_admins")
async def callback_admin_management(callback: CallbackQuery, state: FSMContext):
    """Show admin management panel"""
    await callback.answer()
    
    admins = db.get_admins()
    
    text = f"⚙️ **ADMINLAR BOSHQARUVI**\n\n"
    text += f"👥 Jami adminlar: {len(admins)}\n\n"
    
    if admins:
        text += "**Hozirgi adminlar:**\n"
        for admin in admins:
            name = admin['first_name'] or admin['username'] or f"ID: {admin['user_id']}"
            if admin['last_name']:
                name += f" {admin['last_name']}"
            text += f"• {name} (ID: {admin['user_id']})\n"
    else:
        text += "❌ Admin ro'yxati bo'sh\n"
    
    text += "\nQuyidagi amallardan birini tanlang:"
    
    keyboard = create_admin_management_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

# User management handlers
@admin_router.callback_query(F.data == "user_list")
async def callback_user_list(callback: CallbackQuery):
    """Show user list"""
    await callback.answer()
    
    users = db.get_top_users(20)
    
    text = "📋 **FOYDALANUVCHILAR RO'YXATI (TOP 20)**\n\n"
    
    if users:
        for i, user in enumerate(users, 1):
            name = user['first_name'] or user['username'] or f"User {user['user_id']}"
            if user['last_name']:
                name += f" {user['last_name']}"
            text += f"{i}. {name} - {user['balance']} ball\n"
            text += f"   ID: {user['user_id']}\n\n"
    else:
        text += "❌ Foydalanuvchilar topilmadi"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_users")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "active_users")
async def callback_active_users(callback: CallbackQuery):
    """Show active users"""
    await callback.answer()
    
    active_today = db.get_active_users_count(1)
    active_week = db.get_active_users_count(7)
    active_month = db.get_active_users_count(30)
    
    text = f"📊 **FAOL FOYDALANUVCHILAR**\n\n"
    text += f"🟢 Bugun faol: {active_today}\n"
    text += f"📅 Bu hafta faol: {active_week}\n"
    text += f"📆 Bu oy faol: {active_month}\n\n"
    text += "Bu ma'lumotlar so'nggi faollik vaqtiga asoslangan."
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_users")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "new_users")
async def callback_new_users(callback: CallbackQuery):
    """Show new users statistics"""
    await callback.answer()
    
    stats_manager = StatsManager()
    activity_stats = stats_manager.get_user_activity_stats()
    
    text = f"📈 **YANGI FOYDALANUVCHILAR**\n\n"
    text += f"📅 Bugun ro'yxatdan o'tgan: {activity_stats['today_registrations']}\n"
    text += f"📅 Bu hafta ro'yxatdan o'tgan: {activity_stats['week_registrations']}\n"
    text += f"📅 Bu oy ro'yxatdan o'tgan: {activity_stats['month_registrations']}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_users")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

# Statistics handlers
@admin_router.callback_query(F.data == "stats_today")
async def callback_stats_today(callback: CallbackQuery):
    """Show today's statistics"""
    await callback.answer()
    
    stats_manager = StatsManager()
    stats = stats_manager.get_daily_stats()
    
    text = f"📅 **BUGUNGI STATISTIKA**\n\n"
    text += f"📊 Sana: {stats['date']}\n\n"
    text += f"👤 Yangi foydalanuvchilar: {stats['new_users']}\n"
    text += f"🟢 Faol foydalanuvchilar: {stats['active_users']}\n"
    text += f"💬 Yuborilgan xabarlar: {stats['messages_sent']}\n"
    text += f"👆 Yangi referrallar: {stats['referrals_made']}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_stats")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "stats_week")
async def callback_stats_week(callback: CallbackQuery):
    """Show weekly statistics"""
    await callback.answer()
    
    stats_manager = StatsManager()
    stats = stats_manager.get_weekly_stats()
    
    text = f"📅 **BU HAFTA STATISTIKASI**\n\n"
    text += f"👤 Yangi foydalanuvchilar: {stats['new_users']}\n"
    text += f"🟢 O'rtacha faol foydalanuvchilar: {stats['avg_active_users']}\n"
    text += f"💬 Yuborilgan xabarlar: {stats['messages_sent']}\n"
    text += f"👆 Yangi referrallar: {stats['referrals_made']}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_stats")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "stats_month")
async def callback_stats_month(callback: CallbackQuery):
    """Show monthly statistics"""
    await callback.answer()
    
    stats_manager = StatsManager()
    stats = stats_manager.get_monthly_stats()
    
    text = f"📅 **BU OY STATISTIKASI**\n\n"
    text += f"👤 Yangi foydalanuvchilar: {stats['new_users']}\n"
    text += f"🟢 O'rtacha faol foydalanuvchilar: {stats['avg_active_users']}\n"
    text += f"💬 Yuborilgan xabarlar: {stats['messages_sent']}\n"
    text += f"👆 Yangi referrallar: {stats['referrals_made']}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_stats")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "stats_all")
async def callback_stats_all(callback: CallbackQuery):
    """Show all-time statistics"""
    await callback.answer()
    
    stats_manager = StatsManager()
    stats = stats_manager.get_all_time_stats()
    
    text = f"📊 **UMUMIY STATISTIKA**\n\n"
    text += f"👥 Jami foydalanuvchilar: {stats['total_users']}\n"
    text += f"🟢 Bugun faol: {stats['active_today']}\n"
    text += f"📅 Bu hafta faol: {stats['active_week']}\n"
    text += f"📆 Bu oy faol: {stats['active_month']}\n"
    text += f"👆 Jami referrallar: {stats['total_referrals']}\n"
    text += f"💬 Jami xabarlar: {stats['total_messages']}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_stats")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "top_referrers")
async def callback_top_referrers(callback: CallbackQuery):
    """Show top referrers"""
    await callback.answer()
    
    top_referrers = db.get_top_referrers(10)
    
    text = "👆 **TOP REFERRALLAR**\n\n"
    
    if top_referrers:
        for i, referrer in enumerate(top_referrers, 1):
            name = referrer['first_name'] or referrer['username'] or f"User {referrer['user_id']}"
            if referrer['last_name']:
                name += f" {referrer['last_name']}"
            text += f"{i}. {name} - {referrer['referral_count']} ta referal\n"
    else:
        text += "❌ Referrallar topilmadi"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_stats")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "growth_stats")
async def callback_growth_stats(callback: CallbackQuery):
    """Show growth statistics"""
    await callback.answer()
    
    stats_manager = StatsManager()
    growth_data = stats_manager.get_growth_dynamics(7)  # Last 7 days
    
    text = "📈 **O'SISH DINAMIKASI (So'nggi 7 kun)**\n\n"
    
    if growth_data:
        total_new = sum(day['new_users'] for day in growth_data)
        text += f"📊 Jami yangi foydalanuvchilar: {total_new}\n\n"
        
        for day_data in growth_data[-5:]:  # Show last 5 days
            text += f"📅 {day_data['date']}: +{day_data['new_users']} yangi\n"
    else:
        text += "❌ Ma'lumotlar topilmadi"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_stats")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "export_stats")
async def callback_export_stats(callback: CallbackQuery, bot: Bot):
    """Export statistics to Excel"""
    await callback.answer("📄 Statistika fayli tayyorlanmoqda...")
    
    try:
        stats_manager = StatsManager()
        file_path = await stats_manager.export_statistics_to_excel()
        
        with open(file_path, 'rb') as file:
            await bot.send_document(
                callback.from_user.id,
                document=file,
                caption="📊 Statistika hisoboti\n📅 Sanasi: " + datetime.now().strftime("%d.%m.%Y %H:%M")
            )
        
        await callback.message.answer("✅ Statistika fayli muvaffaqiyatli yuborildi!")
        
    except Exception as e:
        print(f"Error exporting statistics: {e}")
        await callback.message.answer("❌ Statistika faylini yaratishda xatolik yuz berdi.")

# Subscription management handlers
@admin_router.callback_query(F.data == "subscription_list")
async def callback_subscription_list(callback: CallbackQuery):
    """Show subscription list"""
    await callback.answer()
    
    subscriptions = db.get_mandatory_subscriptions()
    
    text = "📋 **MAJBURIY OBUNALAR RO'YXATI**\n\n"
    
    if subscriptions:
        for i, sub in enumerate(subscriptions, 1):
            title = sub['channel_title'] or sub['channel_username'] or f"ID: {sub['channel_id']}"
            type_text = "🔒 Yopiq kanal" if sub['is_private'] else "🔓 Ochiq kanal"
            text += f"{i}. {title}\n"
            text += f"   {type_text}\n"
            if sub['channel_username']:
                text += f"   @{sub['channel_username']}\n"
            text += f"   ID: {sub['id']}\n\n"
    else:
        text += "❌ Hech qanday majburiy obuna yo'q"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_subscriptions")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "add_subscription")
async def callback_add_subscription(callback: CallbackQuery, state: FSMContext):
    """Add subscription prompt"""
    await callback.answer()
    
    text = "➕ **MAJBURIY OBUNA QO'SHISH**\n\n"
    text += "Kanal yoki guruh ma'lumotlarini quyidagi formatda yuboring:\n\n"
    text += "**Ochiq kanal uchun:**\n"
    text += "Kanal username: @kanalusername\n"
    text += "Kanal nomi: Kanal nomi\n\n"
    text += "**Yopiq kanal uchun:**\n"
    text += "Invite link: https://t.me/+ABC123...\n"
    text += "Kanal nomi: Kanal nomi\n\n"
    text += "Misol: @myofficial My Official Channel"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_subscriptions")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(AdminStates.add_subscription)

@admin_router.callback_query(F.data == "remove_subscription")
async def callback_remove_subscription(callback: CallbackQuery):
    """Remove subscription"""
    await callback.answer()
    
    subscriptions = db.get_mandatory_subscriptions()
    
    if not subscriptions:
        text = "❌ O'chirish uchun obuna yo'q!"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_subscriptions")]
        ])
    else:
        text = "🗑 **OBUNANI O'CHIRISH**\n\n"
        text += "O'chirish uchun obunani tanlang:\n\n"
        
        keyboard = []
        for sub in subscriptions:
            title = sub['channel_title'] or sub['channel_username'] or f"ID: {sub['channel_id']}"
            keyboard.append([InlineKeyboardButton(
                text=f"🗑 {title[:30]}...",
                callback_data=f"delete_sub_{sub['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_subscriptions")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

# Contest management handlers
@admin_router.callback_query(F.data == "start_contest")
async def callback_start_contest(callback: CallbackQuery):
    """Start contest"""
    await callback.answer()
    
    db.set_setting('contest_active', 'true')
    
    text = "▶️ **KONKURS BOSHLANDI!**\n\n"
    text += "✅ Konkurs faol holga o'tkazildi.\n"
    text += "Foydalanuvchilar endi to'liq ishtirok eta olishadi!"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Konkurs menyusi", callback_data="admin_contest")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "stop_contest")
async def callback_stop_contest(callback: CallbackQuery):
    """Stop contest"""
    await callback.answer()
    
    db.set_setting('contest_active', 'false')
    
    text = "⏹ **KONKURS TO'XTATILDI!**\n\n"
    text += "✅ Konkurs to'xtatildi.\n"
    text += "Foydalanuvchilar balllarini ko'rishlari mumkin, lekin yangi ball to'play olmaydilar."
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Konkurs menyusi", callback_data="admin_contest")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "contest_winners")
async def callback_contest_winners(callback: CallbackQuery):
    """Show contest winners"""
    await callback.answer()
    
    winners = db.get_top_users(20)
    
    text = "🏆 **KONKURS G'OLIBLARI (TOP 20)**\n\n"
    
    if winners:
        for i, winner in enumerate(winners, 1):
            name = winner['first_name'] or winner['username'] or f"User {winner['user_id']}"
            if winner['last_name']:
                name += f" {winner['last_name']}"
                
            if i == 1:
                emoji = "🥇"
            elif i == 2:
                emoji = "🥈"
            elif i == 3:
                emoji = "🥉"
            else:
                emoji = f"{i}."
                
            text += f"{emoji} {name} - {winner['balance']} ball\n"
    else:
        text += "❌ G'oliblar topilmadi"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Konkurs menyusi", callback_data="admin_contest")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "contest_stats")
async def callback_contest_stats(callback: CallbackQuery):
    """Show contest statistics"""
    await callback.answer()
    
    stats_manager = StatsManager()
    contest_stats = stats_manager.get_contest_statistics()
    
    text = f"📊 **KONKURS STATISTIKASI**\n\n"
    text += f"👥 Jami ishtirokchilar: {contest_stats['total_participants']}\n"
    text += f"🎁 Tarqatilgan balllar: {contest_stats['total_points_distributed']}\n"
    text += f"📊 O'rtacha ball: {contest_stats['average_points']}\n"
    contest_status = '✅ Faol' if contest_stats['contest_active'] else '⏹ To\'xtatilgan'
    text += f"🎯 Status: {contest_status}\n\n"
    
    if contest_stats['top_20_users']:
        text += "🏆 **Top 5 foydalanuvchi:**\n"
        for i, user in enumerate(contest_stats['top_20_users'][:5], 1):
            name = user['first_name'] or user['username'] or f"User {user['user_id']}"
            text += f"{i}. {name} - {user['balance']} ball\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Konkurs menyusi", callback_data="admin_contest")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

# Admin management handlers
@admin_router.callback_query(F.data == "admin_list")
async def callback_admin_list(callback: CallbackQuery):
    """Show admin list"""
    await callback.answer()
    
    admins = db.get_admins()
    
    text = "👥 **ADMINLAR RO'YXATI**\n\n"
    
    if admins:
        for i, admin in enumerate(admins, 1):
            name = admin['first_name'] or admin['username'] or f"User {admin['user_id']}"
            if admin['last_name']:
                name += f" {admin['last_name']}"
            text += f"{i}. {name}\n"
            text += f"   ID: {admin['user_id']}\n"
            added_date = admin['added_date'][:10] if admin['added_date'] else 'Noma\'lum'
            text += f"   Qo'shilgan: {added_date}\n\n"
    else:
        text += "❌ Admin ro'yxati bo'sh"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_admins")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "add_admin_user")
async def callback_add_admin_user(callback: CallbackQuery, state: FSMContext):
    """Add admin user"""
    await callback.answer()
    
    text = "➕ **ADMIN QO'SHISH**\n\n"
    text += "Admin qilmoqchi bo'lgan foydalanuvchining ID raqamini yuboring.\n\n"
    text += "Misol: 123456789\n\n"
    text += "⚠️ ID raqami to'g'ri ekanligiga ishonch hosil qiling!"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_admins")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(AdminStates.add_admin)

@admin_router.callback_query(F.data == "remove_admin_user")
async def callback_remove_admin_user(callback: CallbackQuery):
    """Remove admin user"""
    await callback.answer()
    
    admins = db.get_admins()
    current_admin_id = callback.from_user.id
    
    # Filter out current admin (can't remove themselves)
    removable_admins = [admin for admin in admins if admin['user_id'] != current_admin_id]
    
    if not removable_admins:
        text = "❌ O'chirish uchun admin yo'q yoki siz faqat adminni o'zingiz o'chira olmaysiz!"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_admins")]
        ])
    else:
        text = "➖ **ADMINNI O'CHIRISH**\n\n"
        text += "O'chirish uchun adminni tanlang:\n\n"
        
        keyboard = []
        for admin in removable_admins:
            name = admin['first_name'] or admin['username'] or f"User {admin['user_id']}"
            keyboard.append([InlineKeyboardButton(
                text=f"➖ {name}",
                callback_data=f"remove_admin_{admin['user_id']}"
            )])
        
        keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_admins")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

# Continue existing handlers from original admin_panel.py
@admin_router.callback_query(F.data == "broadcast_all")
async def callback_broadcast_all(callback: CallbackQuery, state: FSMContext):
    """Handle broadcast message to all users"""
    await callback.answer()
    
    text = "📢 **HAMMAGA XABAR YUBORISH**\n\n"
    text += "Yubormoqchi bo'lgan xabaringizni yozing:"
    text += "\n\n⚠️ Bu xabar barcha foydalanuvchilarga yuboriladi!"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_messaging")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(AdminStates.broadcast_message)

@admin_router.callback_query(F.data == "message_single")
async def callback_message_single(callback: CallbackQuery, state: FSMContext):
    """Handle single user message"""
    await callback.answer()
    
    text = "👤 **BITTA FOYDALANUVCHIGA XABAR**\n\n"
    text += "Foydalanuvchi ID sini kiriting:"
    text += "\n\nMasalan: 123456789"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_messaging")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(AdminStates.single_message_target)

@admin_router.callback_query(F.data == "message_stats")
async def callback_message_stats(callback: CallbackQuery):
    """Show message statistics"""
    await callback.answer()
    
    stats_manager = StatsManager()
    all_stats = stats_manager.get_all_time_stats()
    
    text = f"📊 **XABAR STATISTIKASI**\n\n"
    text += f"💬 Jami yuborilgan xabarlar: {all_stats['total_messages']}\n"
    text += f"👥 Jami foydalanuvchilar: {all_stats['total_users']}\n"
    text += f"📈 O'rtacha: {all_stats['total_messages'] // max(all_stats['total_users'], 1)} xabar/foydalanuvchi\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_messaging")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "export_users")
async def callback_export_users(callback: CallbackQuery, bot: Bot):
    """Export users to Excel"""
    await callback.answer("📄 Excel fayl tayyorlanmoqda...")
    
    try:
        stats_manager = StatsManager()
        file_path = await stats_manager.export_users_to_excel()
        
        with open(file_path, 'rb') as file:
            await bot.send_document(
                callback.from_user.id,
                document=file,
                caption="📄 Foydalanuvchilar ro'yxati\n📅 Sanasi: " + datetime.now().strftime("%d.%m.%Y %H:%M")
            )
        
        await callback.message.answer("✅ Excel fayl muvaffaqiyatli yuborildi!")
        
    except Exception as e:
        print(f"Error exporting users: {e}")
        await callback.message.answer("❌ Excel fayl yaratishda xatolik yuz berdi.")

@admin_router.callback_query(F.data == "reset_balances")
async def callback_reset_balances(callback: CallbackQuery):
    """Reset all user balances"""
    await callback.answer()
    
    text = "⚠️ **BALLARNI NOLLASH**\n\n"
    text += "Haqiqatan ham barcha foydalanuvchilarning ballarini nollamoqchimisiz?\n\n"
    text += "❗️ Bu amal qaytarib bo'lmaydi!"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, nollash", callback_data="confirm_reset_balances"),
         InlineKeyboardButton(text="❌ Yo'q", callback_data="admin_contest")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "confirm_reset_balances")
async def callback_confirm_reset_balances(callback: CallbackQuery):
    """Confirm reset balances"""
    await callback.answer()
    
    try:
        success = db.reset_all_balances()
        if success:
            text = "✅ Barcha foydalanuvchilarning ballari nollandi!"
        else:
            text = "❌ Ballarni nollashda xatolik yuz berdi."
    except Exception as e:
        print(f"Error resetting balances: {e}")
        text = "❌ Ballarni nollashda xatolik yuz berdi."
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Konkurs menyusi", callback_data="admin_contest")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

# Handle text messages in broadcast state
@admin_router.message(AdminStates.broadcast_message)
async def handle_broadcast_message(message: Message, state: FSMContext, bot: Bot):
    """Handle broadcast message text"""
    text = message.text
    
    # Get all users
    all_users_data = db.get_users_for_export()
    user_ids = [user['user_id'] for user in all_users_data]
    
    sent_count = 0
    failed_count = 0
    
    progress_msg = await message.answer(f"📤 Xabar yuborilmoqda...\n\n📊 Jami: {len(user_ids)}\n✅ Yuborildi: 0\n❌ Xatolik: 0")
    
    # Send message to all users
    for i, user_id in enumerate(user_ids):
        try:
            await bot.send_message(user_id, text)
            sent_count += 1
            
            # Update progress every 50 messages
            if (i + 1) % 50 == 0:
                try:
                    await progress_msg.edit_text(
                        f"📤 Xabar yuborilmoqda...\n\n"
                        f"📊 Jami: {len(user_ids)}\n"
                        f"✅ Yuborildi: {sent_count}\n"
                        f"❌ Xatolik: {failed_count}\n"
                        f"📈 Jarayon: {((i+1)/len(user_ids)*100):.1f}%"
                    )
                except:
                    pass
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.05)
            
        except Exception as e:
            failed_count += 1
            print(f"Failed to send message to {user_id}: {e}")
    
    # Final result
    final_text = (
        f"✅ **XABAR YUBORISH YAKUNLANDI**\n\n"
        f"📊 Jami foydalanuvchilar: {len(user_ids)}\n"
        f"✅ Muvaffaqiyatli yuborildi: {sent_count}\n"
        f"❌ Xatolik: {failed_count}\n"
        f"📈 Muvaffaqiyat: {(sent_count/len(user_ids)*100):.1f}%"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
    ])
    
    await progress_msg.edit_text(final_text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(AdminStates.main_panel)

# Text editing handlers
@admin_router.callback_query(F.data.startswith("edit_"))
async def callback_edit_text(callback: CallbackQuery, state: FSMContext):
    """Handle text editing"""
    await callback.answer()
    
    edit_type = callback.data.split("_", 1)[1]  # Remove "edit_" prefix
    
    current_text = ""
    if edit_type == "contest_text":
        current_text = db.get_setting('contest_info', DEFAULT_TEXTS['contest_info'])
        state_to_set = AdminStates.edit_contest_text
        title = "🔴 KONKURS MATNI"
    elif edit_type == "gifts_text":
        current_text = db.get_setting('gifts_info', DEFAULT_TEXTS['gifts_info'])
        state_to_set = AdminStates.edit_gifts_text
        title = "🎁 SOVG'ALAR MATNI"
    elif edit_type == "terms_text":
        current_text = db.get_setting('terms_info', DEFAULT_TEXTS['terms_info'])
        state_to_set = AdminStates.edit_terms_text
        title = "💡 SHARTLAR MATNI"
    
    text = f"📝 **{title} TAHRIRLASH**\n\n"
    text += f"**Hozirgi matn:**\n{current_text[:500]}{'...' if len(current_text) > 500 else ''}\n\n"
    text += "**Yangi matnni yozing:**"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_texts")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(state_to_set)

# Text editing message handlers
@admin_router.message(AdminStates.edit_contest_text)
async def handle_edit_contest_text(message: Message, state: FSMContext):
    """Handle contest text editing"""
    new_text = message.text
    db.set_setting('contest_info', new_text)
    
    await message.answer("✅ Konkurs matni muvaffaqiyatli yangilandi!")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
    ])
    await message.answer("Admin panelga qaytish:", reply_markup=keyboard)
    await state.set_state(AdminStates.main_panel)

@admin_router.message(AdminStates.edit_gifts_text)
async def handle_edit_gifts_text(message: Message, state: FSMContext):
    """Handle gifts text editing"""
    new_text = message.text
    db.set_setting('gifts_info', new_text)
    
    await message.answer("✅ Sovg'alar matni muvaffaqiyatli yangilandi!")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
    ])
    await message.answer("Admin panelga qaytish:", reply_markup=keyboard)
    await state.set_state(AdminStates.main_panel)

@admin_router.message(AdminStates.edit_terms_text)
async def handle_edit_terms_text(message: Message, state: FSMContext):
    """Handle terms text editing"""
    new_text = message.text
    db.set_setting('terms_info', new_text)
    
    await message.answer("✅ Shartlar matni muvaffaqiyatli yangilandi!")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
    ])
    await message.answer("Admin panelga qaytish:", reply_markup=keyboard)
    await state.set_state(AdminStates.main_panel)

# User search handler
@admin_router.message(AdminStates.user_search)
async def handle_user_search(message: Message, state: FSMContext):
    """Handle user search"""
    search_term = message.text.strip()
    
    try:
        users = db.search_user(search_term)
        
        if users:
            text = f"🔍 **QIDIRUV NATIJALARI: '{search_term}'**\n\n"
            
            for user in users[:10]:  # Show first 10 results
                name = user['first_name'] or user['username'] or f"User {user['user_id']}"
                if user['last_name']:
                    name += f" {user['last_name']}"
                    
                text += f"👤 **{name}**\n"
                text += f"   ID: {user['user_id']}\n"
                if user['username']:
                    text += f"   Username: @{user['username']}\n"
                text += f"   Ball: {user['balance']}\n"
                reg_date = user['registration_date'][:10] if user['registration_date'] else 'Noma\'lum'
                text += f"   Ro'yxatdan o'tgan: {reg_date}\n\n"
            
            if len(users) > 10:
                text += f"... va yana {len(users) - 10} ta natija\n"
        else:
            text = f"❌ '{search_term}' bo'yicha hech narsa topilmadi."
            
    except Exception as e:
        text = f"❌ Qidirishda xatolik: {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Qayta qidirish", callback_data="admin_search"),
         InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(AdminStates.main_panel)

# Add admin handler
@admin_router.message(AdminStates.add_admin)
async def handle_add_admin(message: Message, state: FSMContext):
    """Handle add admin"""
    try:
        user_id = int(message.text.strip())
        
        # Check if already admin
        if db.is_admin(user_id):
            text = f"❌ ID: {user_id} allaqachon admin!"
        else:
            # Try to add admin
            success = db.add_admin(user_id, message.from_user.id)
            if success:
                text = f"✅ ID: {user_id} muvaffaqiyatli admin qilib qo'shildi!"
            else:
                text = f"❌ ID: {user_id} adminni qo'shishda xatolik yuz berdi."
                
    except ValueError:
        text = "❌ Noto'g'ri ID format! Faqat raqamlar kiriting."
    except Exception as e:
        text = f"❌ Xatolik: {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_panel")]
    ])
    
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(AdminStates.main_panel)

# Handle subscription addition
@admin_router.message(AdminStates.add_subscription)
async def handle_add_subscription(message: Message, state: FSMContext):
    """Handle subscription addition"""
    try:
        parts = message.text.strip().split(None, 1)
        
        if len(parts) < 2:
            text = "❌ Noto'g'ri format! Misol: @channel Channel Name yoki https://t.me/+link Channel Name"
        else:
            channel_input = parts[0]
            channel_title = parts[1]
            
            is_private = False
            channel_username = None
            invite_link = None
            
            if channel_input.startswith('@'):
                # Public channel
                channel_username = channel_input[1:]  # Remove @
                channel_id = f"@{channel_username}"
            elif channel_input.startswith('https://t.me/+'):
                # Private channel
                is_private = True
                invite_link = channel_input
                channel_id = channel_input  # Use link as ID for private channels
            else:
                text = "❌ Noto'g'ri format! @ bilan boshlaning yoki https://t.me/+ havola ishlating."
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_subscriptions")]
                ])
                await message.answer(text, reply_markup=keyboard)
                return
            
            # Add subscription
            success = db.add_mandatory_subscription(
                channel_id=channel_id,
                channel_username=channel_username,
                channel_title=channel_title,
                is_private=is_private,
                invite_link=invite_link
            )
            
            if success:
                text = f"✅ Majburiy obuna muvaffaqiyatli qo'shildi!\n\n"
                text += f"📢 Kanal: {channel_title}\n"
                text += f"🔗 ID: {channel_id}\n"
                text += f"🔒 Turi: {'Yopiq' if is_private else 'Ochiq'}"
            else:
                text = "❌ Obunani qo'shishda xatolik yuz berdi."
                
    except Exception as e:
        text = f"❌ Xatolik: {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Obunalar", callback_data="admin_subscriptions")]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(AdminStates.subscription_management)

# Handle subscription deletion
@admin_router.callback_query(F.data.startswith("delete_sub_"))
async def callback_delete_subscription(callback: CallbackQuery):
    """Delete subscription"""
    await callback.answer()
    
    sub_id = int(callback.data.split("_")[-1])
    
    success = db.remove_mandatory_subscription(sub_id)
    
    if success:
        text = "✅ Majburiy obuna muvaffaqiyatli o'chirildi!"
    else:
        text = "❌ Obunani o'chirishda xatolik yuz berdi."
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Obunalar", callback_data="admin_subscriptions")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)

# Handle admin removal
@admin_router.callback_query(F.data.startswith("remove_admin_"))
async def callback_remove_admin(callback: CallbackQuery):
    """Remove admin"""
    await callback.answer()
    
    admin_id = int(callback.data.split("_")[-1])
    
    success = db.remove_admin(admin_id)
    
    if success:
        text = f"✅ Admin (ID: {admin_id}) muvaffaqiyatli o'chirildi!"
    else:
        text = f"❌ Admin (ID: {admin_id}) ni o'chirishda xatolik yuz berdi."
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Adminlar", callback_data="admin_admins")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)

@admin_router.callback_query(F.data == "back_to_menu")
async def callback_back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Go back to main menu"""
    await callback.answer()
    await callback.message.delete()
    await state.clear()
    
    # Import to avoid circular imports
    from handlers import create_main_menu_keyboard
    keyboard = create_main_menu_keyboard(True)
    await callback.message.answer("🏠 Bosh menyu", reply_markup=keyboard)

# Error handler for admin router
@admin_router.error()
async def admin_error_handler(event, exception):
    """Handle errors in admin handlers"""
    print(f"Error in admin panel: {exception}")
    try:
        if hasattr(event, 'callback_query') and event.callback_query:
            await event.callback_query.message.answer("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
        elif hasattr(event, 'message') and event.message:
            await event.message.answer("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
    except:
        pass