import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# Import modules
from config import BOT_TOKEN, ADMIN_IDS
from database import db
from handlers import router, UserStates
from admin_panel import admin_router, AdminStates

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)

logger = logging.getLogger(__name__)

# Check for bot token
if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE' or not BOT_TOKEN:
    logger.error("❌ Bot token not found! Please set BOT_TOKEN environment variable.")
    print("❌ Bot token not found!")
    print("Please set BOT_TOKEN environment variable with your bot token from @BotFather")
    sys.exit(1)

# Initialize bot and dispatcher
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Use memory storage for FSM
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Include routers
dp.include_router(router)
dp.include_router(admin_router)

async def setup_bot_commands(bot: Bot):
    """Setup bot commands for menu"""
    from aiogram.types import BotCommand, BotCommandScopeDefault
    
    commands = [
        BotCommand(command="start", description="🚀 Botni ishga tushirish"),
        BotCommand(command="menu", description="🏠 Asosiy menyu"),
        BotCommand(command="help", description="❓ Yordam"),
    ]
    
    try:
        await bot.set_my_commands(commands, BotCommandScopeDefault())
        logger.info("✅ Bot commands setup completed")
    except Exception as e:
        logger.error(f"❌ Error setting up bot commands: {e}")

async def setup_initial_data():
    """Setup initial data in database"""
    try:
        # Add initial admin if specified in config
        if ADMIN_IDS:
            for admin_id in ADMIN_IDS:
                if not db.is_admin(admin_id):
                    db.add_admin(admin_id)
                    logger.info(f"✅ Added admin: {admin_id}")
        
        # Set default texts if not exists
        from config import DEFAULT_TEXTS
        
        if not db.get_setting('contest_info'):
            db.set_setting('contest_info', DEFAULT_TEXTS['contest_info'])
        
        if not db.get_setting('gifts_info'):
            db.set_setting('gifts_info', DEFAULT_TEXTS['gifts_info'])
        
        if not db.get_setting('terms_info'):
            db.set_setting('terms_info', DEFAULT_TEXTS['terms_info'])
        
        logger.info("✅ Initial data setup completed")
        
    except Exception as e:
        logger.error(f"❌ Error setting up initial data: {e}")

async def on_startup():
    """Actions to perform on startup"""
    logger.info("🚀 Bot is starting...")
    
    # Setup database
    logger.info("📂 Initializing database...")
    db.init_db()
    
    # Setup initial data
    await setup_initial_data()
    
    # Setup bot commands
    await setup_bot_commands(bot)
    
    # Get bot info
    try:
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot started successfully!")
        logger.info(f"📱 Bot name: {bot_info.first_name}")
        logger.info(f"🆔 Bot username: @{bot_info.username}")
        logger.info(f"🔢 Bot ID: {bot_info.id}")
        
        # Print admin info
        if ADMIN_IDS:
            logger.info(f"👑 Admins: {', '.join(map(str, ADMIN_IDS))}")
        
        print(f"\n🎉 Telegram Contest Bot is running!")
        print(f"📱 Bot: @{bot_info.username}")
        print(f"🔗 Start link: https://t.me/{bot_info.username}")
        print(f"👑 Admins: {len(ADMIN_IDS)} configured")
        print(f"📊 Database: Connected")
        print("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ Error getting bot info: {e}")
        raise

async def on_shutdown():
    """Actions to perform on shutdown"""
    logger.info("🛑 Bot is shutting down...")
    
    try:
        # Close bot session
        await bot.session.close()
        logger.info("✅ Bot session closed")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

async def main():
    """Main function to run the bot"""
    try:
        # Register startup and shutdown handlers
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        # Start polling
        logger.info("🔄 Starting polling...")
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"❌ Critical error in main: {e}")
        raise
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            logger.error("❌ Python 3.8+ required")
            sys.exit(1)
        
        # Run the bot
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)