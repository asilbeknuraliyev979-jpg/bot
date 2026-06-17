from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_class = State()

class ProfileStates(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_new_class = State()
    waiting_for_new_phone = State()

class TestStates(StatesGroup):
    waiting_for_code = State()
    solving = State()  # Timer running, solving questions
    waiting_for_answers = State()  # User clicked "Ishlab bo'ldim" and is now sending their answers

class AdminStates(StatesGroup):
    # Test creation flow
    waiting_for_code = State()
    waiting_for_subject = State()
    waiting_for_pdf = State()
    waiting_for_answers = State()
    waiting_for_duration = State()
    waiting_for_start = State()
    waiting_for_end = State()
    
    # Broadcast message
    waiting_for_broadcast_msg = State()
    
    # Delete test
    waiting_for_delete_code = State()
    
    # Admin management
    waiting_for_new_admin_id = State()
    waiting_for_del_admin_id = State()
    
    # Test editing flow
    waiting_for_edit_code = State()
    waiting_for_edit_field = State()
    waiting_for_edit_value = State()
    
    # Channel management
    waiting_for_channel_id = State()
    waiting_for_channel_url = State()
    waiting_for_del_channel = State()

class RatingStates(StatesGroup):
    waiting_for_test_code = State()
