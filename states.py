from aiogram.fsm.state import State, StatesGroup


class TransferStates(StatesGroup):
    waiting_account_number = State()
    waiting_amount = State()
    waiting_confirm = State()


class TopupStates(StatesGroup):
    waiting_amount = State()
    waiting_screenshot = State()


class AdminMessageStates(StatesGroup):
    waiting_message = State()
