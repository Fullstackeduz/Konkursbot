from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramAPIError
import re
import asyncio
from typing import List, Dict

from database import db
from config import MESSAGES, REGISTRATION_BONUS, REFERRAL_BONUS, ADMIN_IDS

# Router for user handlers
router = Router()

# FSM States
class UserStates(StatesGroup):
    waiting_phone = State()
    main_menu = State()

async def check_user_subscriptions(bot: Bot, user_id: int) -> tuple[bool, List[Dict]]:
    """Check if user is subscribed to all mandatory channels"""
    subscriptions = db.get_mandatory_subscriptions()
    not_subscribed = []
    
    for sub in subscriptions:
        try:
            if sub['is_private']:
                # For private channels, we assume user sent join request
                # This is checked separately in join request handler
                continue
            else:
                # Check public channel subscription
                if sub['channel_username']:
                    chat_id = f"@{sub['channel_username']}"
                else:
                    chat_id = sub['channel_id']
                
                try:
                    member = await bot.get_chat_member(chat_id, user_id)
                    if member.status in ['left', 'kicked', 'restricted']:
                        not_subscribed.append(sub)
                except TelegramAPIError:
                    # If we can't check, assume not subscribed
                    not_subscribed.append(sub)
                    
        except Exception as e:
            print(f"Error checking subscription for {sub['channel_id']}: {e}")
            not_subscribed.append(sub)
    
    return len(not_subscribed) == 0, not_subscribed

def create_subscription_keyboard(subscriptions: List[Dict]) -> InlineKeyboardMarkup:
    """Create keyboard with subscription links"""
    keyboard = []
    
    for sub in subscriptions:
        if sub['is_private'] and sub['invite_link']:
            # Private channel with invite link
            keyboard.append([
                InlineKeyboardButton(
                    text=f"📢 {sub['channel_title'] or 'Private Channel'}",
                    url=sub['invite_link']
                )
            ])
        elif sub['channel_username']:
            # Public channel
            keyboard.append([
                InlineKeyboardButton(
                    text=f"📢 {sub['channel_title'] or sub['channel_username']}",
                    url=f"https://t.me/{sub['channel_username']}"
                )
            ])
    
    # Add check button
    keyboard.append([
        InlineKeyboardButton(
            text="✅ А'zo bo'ldim",
            callback_data="check_subscriptions"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Create main menu keyboard"""
    keyboard = [
        [KeyboardButton(text="🔴 Konkursda qatnashish")],
        [KeyboardButton(text="👆 Referal link"), KeyboardButton(text="🎁 Sovg'alar")],
        [KeyboardButton(text="👤 Ballarim"), KeyboardButton(text="📊 Reyting")],
        [KeyboardButton(text="💡 Shartlar")]
    ]
    
    if is_admin:
        keyboard.append([KeyboardButton(text="🗄 Admin paneli")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

@router.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    """Handle /start command"""
    user_id = message.from_user.id
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    # Extract referrer ID from deep link
    referrer_id = None
    if args and args[0].startswith('ref_'):
        try:
            referrer_id = int(args[0][4:])
        except ValueError:
            pass
    
    # Check if user exists
    user = db.get_user(user_id)
    if not user:
        # Create new user
        db.add_user(
            user_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            referrer_id=referrer_id
        )
        user = db.get_user(user_id)
    
    # Check subscriptions
    is_subscribed, not_subscribed = await check_user_subscriptions(bot, user_id)
    
    if not is_subscribed:
        # Show subscription requirement
        keyboard = create_subscription_keyboard(not_subscribed)
        await message.answer(MESSAGES['start_welcome'], reply_markup=keyboard)
        return
    
    # Check if user has phone number
    if not user['phone_number']:
        await message.answer(MESSAGES['phone_request'])
        await state.set_state(UserStates.waiting_phone)
        return
    
    # User is fully registered, show main menu
    is_admin = db.is_admin(user_id)
    keyboard = create_main_menu_keyboard(is_admin)
    await message.answer(MESSAGES['main_menu'], reply_markup=keyboard)
    await state.set_state(UserStates.main_menu)

@router.callback_query(F.data == "check_subscriptions")
async def callback_check_subscriptions(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Handle subscription check callback"""
    user_id = callback.from_user.id
    
    # Check subscriptions again
    is_subscribed, not_subscribed = await check_user_subscriptions(bot, user_id)
    
    if not is_subscribed:
        # Still not subscribed
        keyboard = create_subscription_keyboard(not_subscribed)
        await callback.message.edit_text(MESSAGES['not_subscribed'], reply_markup=keyboard)
        await callback.answer("❌ Siz hali barcha kanallarga obuna bo'lmagansiz!")
        return
    
    await callback.answer("✅ Tabriklaymiz! Siz barcha kanallarga obuna bo'ldingiz!")
    
    # Check if user has phone number
    user = db.get_user(user_id)
    if not user['phone_number']:
        await callback.message.delete()
        await callback.message.answer(MESSAGES['phone_request'])
        await state.set_state(UserStates.waiting_phone)
        return
    
    # User is fully registered, show main menu
    is_admin = db.is_admin(user_id)
    keyboard = create_main_menu_keyboard(is_admin)
    await callback.message.delete()
    await callback.message.answer(MESSAGES['main_menu'], reply_markup=keyboard)
    await state.set_state(UserStates.main_menu)

@router.message(StateFilter(UserStates.waiting_phone))
async def handle_phone_input(message: Message, state: FSMContext):
    """Handle phone number input"""
    user_id = message.from_user.id
    phone = message.text.strip()
    
    # Validate Uzbekistan phone number (+998)
    if not re.match(r'^\+998\d{9}$', phone):
        await message.answer(MESSAGES['invalid_phone'])
        return
    
    # Update user phone number
    if db.update_user_phone(user_id, phone):
        # Add registration bonus
        db.add_balance(user_id, REGISTRATION_BONUS)
        
        # Add referral bonus if there's a referrer
        user = db.get_user(user_id)
        if user['referrer_id']:
            db.add_referral(user['referrer_id'], user_id)
        
        await message.answer(MESSAGES['registration_success'])
        
        # Show main menu
        is_admin = db.is_admin(user_id)
        keyboard = create_main_menu_keyboard(is_admin)
        await message.answer(MESSAGES['main_menu'], reply_markup=keyboard)
        await state.set_state(UserStates.main_menu)
        
        # Update statistics
        db.update_daily_stats(new_users=1)
    else:
        await message.answer("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

@router.message(F.text == "🔴 Konkursda qatnashish", StateFilter(UserStates.main_menu))
async def handle_contest_info(message: Message):
    """Handle contest info request"""
    contest_text = db.get_setting('contest_info', MESSAGES['contest_info'])
    await message.answer(contest_text)

@router.message(F.text == "👆 Referal link", StateFilter(UserStates.main_menu))
async def handle_referral_link(message: Message, bot: Bot):
    """Handle referral link request"""
    user_id = message.from_user.id
    bot_info = await bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    
    referral_count = db.get_referral_count(user_id)
    
    text = MESSAGES['referral_info'].format(referral_link=referral_link)
    text += f"\n\n📊 Sizning referallaringiz: {referral_count} ta"
    text += f"\n💰 Referal orqali olingan ball: {referral_count * REFERRAL_BONUS} ball"
    
    await message.answer(text)

@router.message(F.text == "🎁 Sovg'alar", StateFilter(UserStates.main_menu))
async def handle_gifts_info(message: Message):
    """Handle gifts info request"""
    gifts_text = db.get_setting('gifts_info', MESSAGES['gifts_info'])
    await message.answer(gifts_text)

@router.message(F.text == "💡 Shartlar", StateFilter(UserStates.main_menu))
async def handle_terms_info(message: Message):
    """Handle terms info request"""
    terms_text = db.get_setting('terms_info', MESSAGES['terms_info'])
    await message.answer(terms_text)

@router.message(F.text == "👤 Ballarim", StateFilter(UserStates.main_menu))
async def handle_user_balance(message: Message):
    """Handle user balance request"""
    user_id = message.from_user.id
    balance = db.get_user_balance(user_id)
    rank = db.get_user_rank(user_id)
    
    text = MESSAGES['user_balance'].format(balance=balance, rank=rank)
    await message.answer(text)

@router.message(F.text == "📊 Reyting", StateFilter(UserStates.main_menu))
async def handle_rating(message: Message):
    """Handle rating request"""
    top_users = db.get_top_users(20)
    
    if not top_users:
        await message.answer("📊 Hali reyting mavjud emas.")
        return
    
    text = MESSAGES['rating_header'] + "\n\n"
    
    for user in top_users:
        rank = user['rank']
        name = user['first_name'] or user['username'] or f"User {user['user_id']}"
        if user['last_name']:
            name += f" {user['last_name']}"
        balance = user['balance']
        
        if rank == 1:
            emoji = "🥇"
        elif rank == 2:
            emoji = "🥈"
        elif rank == 3:
            emoji = "🥉"
        else:
            emoji = f"{rank}."
        
        text += f"{emoji} {name} - {balance} ball\n"
    
    await message.answer(text)

@router.message(F.text == "🗄 Admin paneli", StateFilter(UserStates.main_menu))
async def handle_admin_panel(message: Message):
    """Handle admin panel request"""
    user_id = message.from_user.id
    
    if not db.is_admin(user_id) and user_id not in ADMIN_IDS:
        await message.answer(MESSAGES['admin_not_allowed'])
        return
    
    # Import admin panel handler dynamically to avoid circular imports
    from admin_panel import show_admin_panel
    await show_admin_panel(message)

@router.message(StateFilter(UserStates.main_menu))
async def handle_unknown_command(message: Message):
    """Handle unknown commands in main menu"""
    await message.answer("❓ Noma'lum buyruq. Iltimos, menyudan birini tanlang.")

# Chat member status handlers
@router.chat_member()
async def on_chat_member_updated(chat_member_update, bot: Bot):
    """Handle chat member updates (join/leave)"""
    try:
        user_id = chat_member_update.from_user.id
        chat_id = str(chat_member_update.chat.id)
        new_status = chat_member_update.new_chat_member.status
        
        # Check if this is a mandatory subscription channel
        subscriptions = db.get_mandatory_subscriptions()
        is_mandatory = any(sub['channel_id'] == chat_id for sub in subscriptions)
        
        if is_mandatory:
            if new_status in ['member', 'administrator', 'creator']:
                # User joined, notify them
                try:
                    await bot.send_message(
                        user_id, 
                        "✅ Sizning so'rovingiz qabul qilindi! Endi /start buyrug'ini bosing."
                    )
                except:
                    pass  # User might have blocked the bot
                    
    except Exception as e:
        print(f"Error handling chat member update: {e}")

# Error handler for this router
@router.error()
async def error_handler(event, exception):
    """Handle errors in user handlers"""
    print(f"Error in handlers: {exception}")
    try:
        if hasattr(event, 'message') and event.message:
            await event.message.answer("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
    except:
        pass