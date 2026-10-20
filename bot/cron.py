import asyncio
import logging
from datetime import datetime
from aiogram import Bot

from bot.database.database import async_session_maker
from bot.services.driver_service import DriverService
from bot.utils.helpers import safe_send_message
from config import settings

logger = logging.getLogger(__name__)

async def subscription_checker(bot: Bot):
    """Har kuni (yoki har soat) ishlab turuvchi obunani tekshirish vazifasi."""
    while True:
        try:
            async with async_session_maker() as session:
                # 1. Muddati o'tgan haydovchilarni topish
                expired_drivers = await DriverService.get_expired_subscriptions(session)
                
                for driver in expired_drivers:
                    logger.info(f"Obuna tugagan: {driver.full_name} (ID: {driver.id})")
                    
                    # 2. Statusini EXPIRED qilish
                    driver.payment_status = "EXPIRED"
                    driver.online_status = "OFFLINE"
                    
                    # 3. Guruhdan chiqarish
                    group = driver.district.group if hasattr(driver.district, 'group') else None
                    if not group:
                        group = await DriverService.get_group_for_driver(session, driver.district_id)
                        
                    if group and group.telegram_group_id:
                        try:
                            # Guruhdan kick qilish (ban va darhol unban qilish orqali)
                            await bot.ban_chat_member(group.telegram_group_id, driver.user.telegram_id)
                            await bot.unban_chat_member(group.telegram_group_id, driver.user.telegram_id)
                        except Exception as e:
                            logger.error(f"Haydovchini guruhdan chiqarishda xatolik: {e}")
                    
                    # 4. Lichkasiga xabar yozish
                    payment_settings = await session.execute("SELECT card, amount FROM settings WHERE id=1")
                    # Settings model is not easily accessible via raw sql here without models, let's fetch using AdminService
                    
                    from bot.services.admin_service import AdminService
                    ps = await AdminService.get_payment_settings(session)
                    card = ps.get('card', settings.PAYMENT_CARD)
                    amount = ps.get('amount', 'Belgilanmagan')

                    text = (
                        "⚠️ *OBUNANGIZ TUGADI!*\n\n"
                        "Sizning oylik obuna muddatingiz o'z nihoyasiga yetdi va siz guruhdan chiqarildingiz.\n\n"
                        f"Guruhga qaytish va ishlashni davom ettirish uchun to'lovni amalga oshiring:\n"
                        f"💰 Summa: *{amount} so'm*\n"
                        f"💳 Karta: `{card}`\n\n"
                        "Menyudan *💳 Obunani uzaytirish* tugmasini bosib to'lov chekini yuboring."
                    )
                    
                    await safe_send_message(bot, driver.user.telegram_id, text, parse_mode="Markdown")
                    
                await session.commit()
                
        except Exception as e:
            logger.error(f"Cron task xatoligi (subscription_checker): {e}")
            
        # Har 1 soatda (3600 sekund) tekshiradi
        await asyncio.sleep(3600)
