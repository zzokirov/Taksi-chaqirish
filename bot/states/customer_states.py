"""Mijoz buyurtma berish uchun FSM holatlari."""
from aiogram.fsm.state import State, StatesGroup


class CustomerOrderState(StatesGroup):
    """Mijoz buyurtma berish jarayoni."""
    choosing_direction = State()
    choosing_district = State()
    choosing_destination_district = State()
    entering_from = State()
    entering_to = State()
    choosing_passengers = State()
    entering_price = State()
    confirmation = State()
    waiting_for_support_message = State()
