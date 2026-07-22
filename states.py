from aiogram.fsm.state import State, StatesGroup


class TransferStates(StatesGroup):
    waiting_account_number = State()
    waiting_amount = State()
    waiting_confirm = State()


class AdminMessageStates(StatesGroup):
    waiting_message = State()