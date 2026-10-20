"""Admin panel uchun FSM holatlari."""
from aiogram.fsm.state import State, StatesGroup


class AdminState(StatesGroup):
    """Admin panel holatlari."""
    editing_card = State()
    editing_amount = State()
    editing_card_owner = State()
    adding_district = State()
    editing_district = State()
    adding_group = State()
    editing_group_name = State()
    editing_group_id = State()
    editing_group_link = State()
    broadcasting = State()
    broadcast_target = State()
