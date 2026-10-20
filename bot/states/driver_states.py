"""Haydovchi ro'yxatdan o'tish va to'lov uchun FSM holatlari."""
from aiogram.fsm.state import State, StatesGroup


class DriverRegistrationState(StatesGroup):
    """Haydovchi ro'yxatdan o'tish jarayoni."""
    full_name = State()
    phone = State()
    car_model = State()
    district = State()
    waiting_receipt = State()
    waiting_renewal_receipt = State()
    confirmation = State()


class PaymentState(StatesGroup):
    """Haydovchi to'lov jarayoni."""
    waiting_receipt = State()
