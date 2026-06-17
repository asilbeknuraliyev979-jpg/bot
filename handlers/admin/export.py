import logging
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from loader import bot, db
from config.config import Config
from utils.excel_export import export_test_results

router = Router()
logger = logging.getLogger("EduMasterBot.handlers.admin.export")

def is_admin_user(telegram_id: int) -> bool:
    return db.is_admin(telegram_id, Config.ADMIN_ID)

# --- 📥 NATIJALARNI YUKLAB OLISH (EXPORT) ---
@router.message(F.text == "📥 Natijalarni yuklab olish")
async def show_export_tests(message: Message):
    if not is_admin_user(message.from_user.id):
        return
        
    tests = db.get_all_tests()
    if not tests:
        await message.answer("❌ Bazada hech qanday test mavjud emas! Natijalarni eksport qilish uchun avval test qo'shing.")
        return
        
    kb = InlineKeyboardBuilder()
    for t in tests:
        # Show code and subject in button
        kb.button(text=f"{t['code']} - {t['subject']}", callback_data=f"exp_test:{t['code']}")
        
    kb.adjust(1)
    
    await message.answer(
        "📥 <b>Natijalarni yuklab olmoqchi bo'lgan testingizni tanlang:</b>",
        reply_markup=kb.as_markup()
    )

# Export test selected callback
@router.callback_query(F.data.startswith("exp_test:"))
async def process_export_test_select(callback: CallbackQuery):
    if not is_admin_user(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return
        
    test_code = callback.data.split(":")[1]
    test = db.get_test(test_code)
    
    if not test:
        await callback.answer("Test topilmadi!", show_alert=True)
        return
        
    # Ask format selection
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Excel (.xlsx) formatida", callback_data=f"exp_fmt:{test_code}:excel")
    kb.button(text="📝 CSV formatida", callback_data=f"exp_fmt:{test_code}:csv")
    kb.button(text="📄 PDF formatida", callback_data=f"exp_fmt:{test_code}:pdf")
    kb.adjust(1)
    
    await callback.message.edit_text(
        f"⚙️ <b>'{test_code}' ({test['subject']}) test natijalari uchun formatni tanlang:</b>",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

# Format selected callback
@router.callback_query(F.data.startswith("exp_fmt:"))
async def process_export_format_select(callback: CallbackQuery):
    if not is_admin_user(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return
        
    parts = callback.data.split(":")
    test_code = parts[1]
    fmt = parts[2]
    
    test = db.get_test(test_code)
    if not test:
        await callback.answer("Test topilmadi!", show_alert=True)
        return
        
    # Get all results for this test
    results = db.get_test_results(test_code)
    if not results:
        await callback.answer("⚠️ Ushbu test bo'yicha hali hech kim ishtirok etmagan! Eksport qilib bo'lmaydi.", show_alert=True)
        return
        
    await callback.answer("Fayl tayyorlanmoqda, iltimos kuting...", show_alert=False)
    
    try:
        # Generate the exported file
        file_path = export_test_results(results, test_code, test["subject"], fmt)
        
        if os.path.exists(file_path):
            doc = FSInputFile(file_path)
            # Send file to administrator
            caption = f"📊 <b>'{test_code}' ({test['subject']}) test natijalari</b>\nFormat: <code>{fmt.upper()}</code>\nIshtirokchilar: {len(results)} ta o'quvchi."
            await callback.message.answer_document(doc, caption=caption)
            await callback.message.delete()
        else:
            await callback.message.answer("⚠️ Fayl yaratishda xatolik yuz berdi. Iltimos qayta urinib ko'ring.")
    except Exception as e:
        logger.error(f"Error exporting results for test {test_code} in format {fmt}: {e}")
        await callback.message.answer(f"⚠️ Eksport xatoligi: {e}")
