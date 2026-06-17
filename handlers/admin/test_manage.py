import os
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from loader import bot, db
from config.config import Config
from states.states import AdminStates
from keyboards.reply.keyboards import get_admin_menu_keyboard, get_back_keyboard
from handlers.user.test import parse_user_answers

router = Router()
logger = logging.getLogger("EduMasterBot.handlers.admin.test_manage")

def is_admin_user(telegram_id: int) -> bool:
    return db.is_admin(telegram_id, Config.ADMIN_ID)

# --- ➕ TEST CREATION FLOW ---
@router.message(F.text == "➕ Test qo'shish")
async def start_add_test(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        return
        
    await state.update_data(is_gift=0)
    await message.answer(
        "📝 <b>Yangi test kodini kiriting:</b>\n"
        "<i>(Masalan: PM-21)</i>",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_code)

@router.message(F.text == "🎁 Sovg'ali test qo'shish")
async def start_add_gift_test(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        return
        
    await state.update_data(is_gift=1)
    await message.answer(
        "🎁 <b>Yangi SOVG'ALI test kodini kiriting:</b>\n"
        "<i>(Masalan: GIFT-01)</i>",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_code)

@router.message(AdminStates.waiting_for_code)
async def process_code(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        await state.clear()
        return
        
    input_text = message.text.strip()
    if input_text == "↩️ Ortga qaytish":
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_admin_menu_keyboard())
        return
        
    code = input_text.upper()
    if not code.isalnum() and "-" not in code:
        await message.answer("⚠️ Test kodida faqat harflar, raqamlar va '-' belgisi qatnashishi mumkin. Qaytadan kiriting:", reply_markup=get_back_keyboard())
        return
        
    # Check if test code exists
    existing = db.get_test(code)
    if existing:
        await message.answer("⚠️ Ziddiyat! Ushbu kodga ega test allaqachon bazada bor. Iltimos boshqa kod yozing:", reply_markup=get_back_keyboard())
        return
        
    await state.update_data(code=code)
    await message.answer("📚 <b>Test topshiriladigan fanning nomini kiriting:</b>\n<i>(Masalan: Matematika)</i>", reply_markup=get_back_keyboard())
    await state.set_state(AdminStates.waiting_for_subject)

@router.message(AdminStates.waiting_for_subject)
async def process_subject(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        await state.clear()
        return
        
    input_text = message.text.strip()
    if input_text == "↩️ Ortga qaytish":
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_admin_menu_keyboard())
        return
        
    await state.update_data(subject=input_text)
    await message.answer("📄 <b>Test savollari yozilgan PDF faylni yuboring (yuklang):</b>", reply_markup=get_back_keyboard())
    await state.set_state(AdminStates.waiting_for_pdf)

@router.message(AdminStates.waiting_for_pdf, F.text == "↩️ Ortga qaytish")
async def cancel_pdf_upload(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_admin_menu_keyboard())

@router.message(AdminStates.waiting_for_pdf, F.document)
async def process_pdf(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        await state.clear()
        return
        
    doc = message.document
    if not doc.file_name.lower().endswith(".pdf"):
        await message.answer("⚠️ Xatolik! Iltimos, faqat PDF formatidagi fayl yuklang:", reply_markup=get_back_keyboard())
        return
        
    data = await state.get_data()
    test_code = data["code"]
    
    # Download file securely
    file_info = await bot.get_file(doc.file_id)
    pdf_filename = f"{test_code}.pdf"
    pdf_filepath = Config.PDF_DIR / pdf_filename
    
    Config.PDF_DIR.mkdir(parents=True, exist_ok=True)
    await bot.download_file(file_info.file_path, destination=pdf_filepath)
    
    await state.update_data(pdf_path=str(pdf_filepath))
    await message.answer("🎯 <b>To'g'ri javoblarni bir qator qilib yuboring:</b>\n<i>(Masalan: ABCDABCDABCD)</i>", reply_markup=get_back_keyboard())
    await state.set_state(AdminStates.waiting_for_answers)

@router.message(AdminStates.waiting_for_answers)
async def process_answers(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        await state.clear()
        return
        
    input_text = message.text.strip()
    if input_text == "↩️ Ortga qaytish":
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_admin_menu_keyboard())
        return
        
    parsed_answers = parse_user_answers(input_text)
    if not parsed_answers:
        await message.answer(
            "⚠️ <b>Javoblar aniqlanmadi!</b>\n\n"
            "Iltimos, to'g'ri javoblarni quyidagi to'g'ri formatlardan birida yuboring:\n"
            "👉 Ketma-ket: <code>ABCDABCD</code>\n"
            "👉 Vergul bilan: <code>1.a, 2.b, 3.c</code>\n"
            "👉 Tire bilan: <code>1-a 2-b 3-c</code>",
            reply_markup=get_back_keyboard()
        )
        return
        
    await state.update_data(answers=parsed_answers)

    await message.answer("⏳ <b>Test ishlash vaqtini daqiqalarda kiriting:</b>\n<i>(Masalan: 30)</i>", reply_markup=get_back_keyboard())
    await state.set_state(AdminStates.waiting_for_duration)

@router.message(AdminStates.waiting_for_duration)
async def process_duration(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        await state.clear()
        return
        
    input_text = message.text.strip()
    if input_text == "↩️ Ortga qaytish":
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_admin_menu_keyboard())
        return
        
    if not input_text.isdigit():
        await message.answer("⚠️ Vaqt faqat raqamda bo'lishi kerak. Masalan: 30 (daqiqa):", reply_markup=get_back_keyboard())
        return
        
    duration = int(input_text)
    await state.update_data(duration=duration)
    await message.answer(
        "📅 <b>Test boshlanish vaqtini kiriting:</b>\n"
        "Format: <code>DD.MM.YYYY HH:MM</code>\n"
        "<i>Masalan: 20.05.2026 10:00</i>",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_start)

@router.message(AdminStates.waiting_for_start)
async def process_start_time(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        await state.clear()
        return
        
    input_text = message.text.strip()
    if input_text == "↩️ Ortga qaytish":
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_admin_menu_keyboard())
        return
        
    try:
        # Validate date format
        datetime.strptime(input_text, "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer(
            "⚠️ Vaqt formati noto'g'ri! Iltimos quyidagi formatda kiriting:\n"
            "<code>DD.MM.YYYY HH:MM</code> (Masalan: 20.05.2026 10:00):",
            reply_markup=get_back_keyboard()
        )
        return
        
    await state.update_data(start_time=input_text)
    await message.answer(
        "📅 <b>Test tugash vaqtini kiriting:</b>\n"
        "Format: <code>DD.MM.YYYY HH:MM</code>\n"
        "<i>Masalan: 20.05.2026 12:00</i>",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_end)

@router.message(AdminStates.waiting_for_end)
async def process_end_time(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        await state.clear()
        return
        
    input_text = message.text.strip()
    if input_text == "↩️ Ortga qaytish":
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_admin_menu_keyboard())
        return
        
    try:
        # Validate date format
        datetime.strptime(input_text, "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer(
            "⚠️ Vaqt formati noto'g'ri! Iltimos quyidagi formatda kiriting:\n"
            "<code>DD.MM.YYYY HH:MM</code> (Masalan: 20.05.2026 12:00):",
            reply_markup=get_back_keyboard()
        )
        return
        
    data = await state.get_data()
    
    # Verify end time is after start time
    start_dt = datetime.strptime(data["start_time"], "%d.%m.%Y %H:%M")
    end_dt = datetime.strptime(input_text, "%d.%m.%Y %H:%M")
    
    if end_dt <= start_dt:
        await message.answer("⚠️ Xatolik! Test tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak. Qaytadan kiriting:", reply_markup=get_back_keyboard())
        return
        
    # Save to SQLite
    is_gift = data.get("is_gift", 0)
    db.add_test(
        code=data["code"],
        subject=data["subject"],
        pdf_path=data["pdf_path"],
        correct_answers=data["answers"],
        duration=data["duration"],
        start_time=data["start_time"],
        end_time=input_text,
        is_gift=is_gift
    )
    
    await state.clear()
    
    gift_prefix = "🎁 SOVG'ALI " if is_gift else "✅ "
    confirm_msg = (
        f"{gift_prefix}<b>TEST MUVAFFAQIYATLI QO'SHILDI!</b>\n\n"
        f"📄 Test kodi: <b>{data['code']}</b>\n"
        f"📚 Fan: <b>{data['subject']}</b>\n"
        f"🎯 Javoblar soni: <b>{len(data['answers'])} ta</b>\n"
        f"⏳ Ishlash vaqti: <b>{data['duration']} daqiqa</b>\n"
        f"📅 Muddati: <b>{data['start_time']}</b> dan <b>{input_text}</b> gacha"
    )
    
    await message.answer(confirm_msg, reply_markup=get_admin_menu_keyboard())

    # Generate Promotional Advertisement Post with 4 text links
    promo_text = (
        f"📢 <b>YANGI TEST E'LON QILINDI!</b>\n\n"
        f"📚 <b>Fan:</b> {data['subject']}\n"
        f"🔑 <b>Test kodi:</b> <code>{data['code']}</code>\n"
        f"⏳ <b>Ishlash vaqti:</b> {data['duration']} daqiqa\n"
        f"📅 <b>Boshlanish:</b> {data['start_time']}\n"
        f"📅 <b>Tugash:</b> {input_text}\n\n"
        f"💡 <i>Ushbu testni ishlash uchun quyidagi bot havolalaridan biri orqali botga o'ting va test kodini kiriting:</i>\n\n"
        f"👉 @Edu_master2_bot\n"
        f"👉 @Edu_master2_bot\n"
        f"👉 @Edu_master2_bot\n"
        f"👉 @Edu_master2_bot"
    )
    
    await message.answer("👇 <b>Kanal yoki guruhlarga tarqatish (forward) uchun tayyor reklama posti:</b>")
    await message.answer(promo_text)

# --- ❌ TESTNI O'CHIRISH ---
@router.message(F.text == "❌ Testni o'chirish")
async def start_delete_test(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        return
        
    tests = db.get_all_tests()
    if not tests:
        await message.answer("❌ Bazada hech qanday test mavjud emas!")
        return
        
    text = "📝 <b>Bazada mavjud testlar ro'yxati:</b>\n\n"
    for t in tests:
        text += f"▪️ Kodi: <code>{t['code']}</code> | Fan: {t['subject']}\n"
        
    text += "\n❌ <b>O'chirmoqchi bo'lgan test kodini yuboring:</b>"
    
    await message.answer(text, reply_markup=get_back_keyboard())
    await state.set_state(AdminStates.waiting_for_delete_code)

@router.message(AdminStates.waiting_for_delete_code)
async def process_delete_test(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        await state.clear()
        return
        
    input_text = message.text.strip()
    if input_text == "↩️ Ortga qaytish":
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_admin_menu_keyboard())
        return
        
    code = input_text.upper()
    test = db.get_test(code)
    
    if not test:
        await message.answer(
            "⚠️ Bunday kodli test topilmadi! Qaytadan kiriting:\n"
            "<i>(Ortga qaytish uchun: '↩️ Ortga qaytish' tugmasini bosing)</i>",
            reply_markup=get_back_keyboard()
        )
        return
        
    # Delete test file if exists
    if test["pdf_path"] and os.path.exists(test["pdf_path"]):
        try:
            os.remove(test["pdf_path"])
        except Exception as e:
            logger.error(f"Error removing PDF file: {e}")
            
    # Delete from DB
    db.delete_test(code)
    await state.clear()
    
    await message.answer(
        f"✅ <b>'{code}' kodli test va unga tegishli barcha natijalar, sertifikatlar tizimdan butunlay o'chirildi!</b>",
        reply_markup=get_admin_menu_keyboard()
    )

# --- ✏️ TESTNI TAHRIRLASH ---
@router.message(F.text == "✏️ Testni tahrirlash")
async def start_edit_test(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        return
        
    tests = db.get_all_tests()
    if not tests:
        await message.answer("❌ Bazada hech qanday test mavjud emas!")
        return
        
    text = "📝 <b>Bazada mavjud testlar ro'yxati:</b>\n\n"
    for t in tests:
        status = "Faol ✅" if t["is_active"] else "To'xtatilgan ❌"
        text += f"▪️ Kodi: <code>{t['code']}</code> | Fan: {t['subject']} | Holati: {status}\n"
        
    text += "\n✏️ <b>Tahrirlamoqchi bo'lgan test kodini yuboring:</b>"
    
    await message.answer(text, reply_markup=get_back_keyboard())
    await state.set_state(AdminStates.waiting_for_edit_code)

@router.message(AdminStates.waiting_for_edit_code)
async def process_edit_test_code(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        await state.clear()
        return
        
    input_text = message.text.strip()
    if input_text == "↩️ Ortga qaytish":
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_admin_menu_keyboard())
        return
        
    code = input_text.upper()
    test = db.get_test(code)
    
    if not test:
        await message.answer(
            "⚠️ Bunday kodli test topilmadi! Qaytadan kiriting:\n"
            "<i>(Ortga qaytish uchun: '↩️ Ortga qaytish' tugmasini bosing)</i>",
            reply_markup=get_back_keyboard()
        )
        return
        
    await state.update_data(edit_code=code)
    
    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    kb = ReplyKeyboardBuilder()
    kb.button(text="⏱ Vaqtni tahrirlash")
    kb.button(text="🎯 Javoblarni tahrirlash")
    kb.button(text="🔄 Holatini o'zgartirish (Faol/To'xtatish)")
    kb.button(text="↩️ Ortga qaytish")
    kb.adjust(1)
    
    await message.answer(
        f"✏️ <b>{code}</b> kodli test uchun nimani tahrirlamoqchisiz?",
        reply_markup=kb.as_markup(resize_keyboard=True)
    )
    await state.set_state(AdminStates.waiting_for_edit_field)

@router.message(AdminStates.waiting_for_edit_field)
async def process_edit_field(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        await state.clear()
        return
        
    input_text = message.text.strip()
    if input_text == "↩️ Ortga qaytish":
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_admin_menu_keyboard())
        return
        
    if input_text == "⏱ Vaqtni tahrirlash":
        await state.update_data(edit_field="duration")
        await message.answer("⏳ <b>Testning yangi vaqtini daqiqalarda kiriting:</b>\n<i>(Masalan: 45)</i>", reply_markup=get_back_keyboard())
        await state.set_state(AdminStates.waiting_for_edit_value)
    elif input_text == "🎯 Javoblarni tahrirlash":
        await state.update_data(edit_field="answers")
        await message.answer("🎯 <b>Yangi to'g'ri javoblarni bir qator qilib yuboring:</b>\n<i>(Masalan: ABCDABCDABCD)</i>", reply_markup=get_back_keyboard())
        await state.set_state(AdminStates.waiting_for_edit_value)
    elif input_text == "🔄 Holatini o'zgartirish (Faol/To'xtatish)":
        data = await state.get_data()
        test = db.get_test(data["edit_code"])
        new_status = 0 if test["is_active"] else 1
        db.update_test_status(data["edit_code"], new_status)
        status_text = "Faol" if new_status else "To'xtatilgan"
        await state.clear()
        await message.answer(f"✅ Test holati <b>{status_text}</b> holatiga o'zgartirildi!", reply_markup=get_admin_menu_keyboard())
    else:
        await message.answer("⚠️ Noto'g'ri buyruq tanlandi. Klaviaturadagi tugmalardan foydalaning.")

@router.message(AdminStates.waiting_for_edit_value)
async def process_edit_value(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        await state.clear()
        return
        
    input_text = message.text.strip()
    if input_text == "↩️ Ortga qaytish":
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_admin_menu_keyboard())
        return
        
    data = await state.get_data()
    code = data["edit_code"]
    field = data["edit_field"]
    
    if field == "duration":
        if not input_text.isdigit():
            await message.answer("⚠️ Vaqt faqat raqamda bo'lishi kerak. Masalan: 30 (daqiqa):")
            return
        db.update_test(code, duration=int(input_text))
        await message.answer(f"✅ Test ishlash vaqti <b>{input_text} daqiqa</b> qilib o'zgartirildi!", reply_markup=get_admin_menu_keyboard())
        
    elif field == "answers":
        parsed = parse_user_answers(input_text)
        if not parsed:
            await message.answer("⚠️ Javoblar aniqlanmadi! To'g'ri formatda yuboring:")
            return
        db.update_test(code, correct_answers=parsed)
        await message.answer(f"✅ Test javoblari muvaffaqiyatli yangilandi!\nJavoblar: <code>{parsed}</code>", reply_markup=get_admin_menu_keyboard())
        
    await state.clear()
