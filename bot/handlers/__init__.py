from aiogram import Router

from bot.handlers.start import router as start_router
from bot.handlers.customer import router as customer_router
from bot.handlers.driver import router as driver_router
from bot.handlers.orders import router as orders_router
from bot.handlers.admin import router as admin_router

def get_handlers_router() -> Router:
    router = Router()
    router.include_router(start_router)
    router.include_router(customer_router)
    router.include_router(driver_router)
    router.include_router(orders_router)
    router.include_router(admin_router)
    return router
