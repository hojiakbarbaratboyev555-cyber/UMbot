from aiogram.fsm.state import State, StatesGroup


class TopupState(StatesGroup):
    waiting_amount = State()
    waiting_screenshot = State()


class TransferState(StatesGroup):
    waiting_card = State()
    waiting_amount = State()
    confirming = State()


class BroadcastState(StatesGroup):
    waiting_message = State()
  
