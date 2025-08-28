from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

class UserStates(StatesGroup):
    MAIN_MENU = State()
    SEND_PHOTO = State()
    BUY_CREDITS = State()
    CHOOSE_PAYMENT = State()