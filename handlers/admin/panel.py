import logging
import asyncio
import os
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from loader import bot, db
from config.config import Config
from states.states import AdminStates
from keyboards.reply.keyboards import get_admin_menu_keyboard, get_main_menu_keyboard, get_back_keyboard
from utils.excel_export import export_statistics_report, export_users_list


router = Router()
logger = logging.getLogger("EduMasterBot.handlers.admin.panel")

# Helper check for admin
def is_admin_user(telegram_id: int) -> bool:
    return db.is_admin(telegram_id, Config.ADMIN_ID)

@router.message(Command("admin"))
async def admin_panel_start(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id
    
    if not is_admin_user(telegram_id):
        await message.answer("⚠️ <b>Kechirasiz, siz admin emassiz!</b>\nBu bo'lim faqat tizim administratorlari uchun.")
        return
        
    await message.answer(
        "👨‍💻 <b>ADMINISTRATOR PANELIGA XUSH KELIBSIZ!</b>\n\n"
        "Quyidagi boshqaruv tugmalaridan foydalaning:",
        reply_markup=get_admin_menu_keyboard()
    )

# --- 📊 STATISTIKALAR ---
@router.message(F.text == "📊 Statistikalar")
async def show_admin_stats(message: Message):
    if not is_admin_user(message.from_user.id):
        return
        
    stats = db.get_statistics()
    
    stats_text = (
        "📊 <b>EDU MASTER BOT TIZIM STATISTIKASI</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {stats['total_users']} ta\n"
        f"🏃‍♂️ <b>Aktiv foydalanuvchilar:</b> {stats['active_users']} ta\n"
        f"📝 <b>Jami topshirilgan testlar:</b> {stats['total_results']} ta\n"
        f"📜 <b>Berilgan sertifikatlar:</b> {stats['certificates_count']} ta\n\n"
        f"🥇 <b>Eng yuqori ball:</b> {stats['highest_score']}%\n"
        f"🥈 <b>Eng past ball:</b> {stats['lowest_score']}%\n"
        f"📈 <b>O'rtacha o'zlashtirish:</b> {stats['average_score']}%"
    )
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📥 Excel hisobot", callback_data="export_stats:excel")
    kb.button(text="📥 PDF hisobot", callback_data="export_stats:pdf")
    kb.adjust(2)
    
    await message.answer(stats_text, reply_markup=kb.as_markup())

# --- 👥 FOYDALANUVCHILAR ---
@router.message(F.text == "👥 Foydalanuvchilar")
async def list_bot_users(message: Message):
    if not is_admin_user(message.from_user.id):
        return
        
    users = db.get_all_users()
    if not users:
        await message.answer("👥 Foydalanuvchilar ro'yxati bo'sh!")
        return
        
    text = f"👥 <b>JAMI RO'YXATDAN O'TGAN FOYDALANUVCHILAR ({len(users)} ta):</b>\n\n"
    # Show the last 15 users to prevent telegram message length limits
    recent_users = users[-15:]
    for idx, u in enumerate(reversed(recent_users), 1):
        text += f"{idx}. <b>{u['full_name']}</b> | Sinf: {u['class_name']} | Tel: {u['phone']} | ID: <code>{u['telegram_id']}</code>\n"
        
    if len(users) > 15:
        text += f"\n<i>...va yana {len(users) - 15} ta foydalanuvchi bor. To'liq ro'yxatni yuklab olishingiz mumkin.</i>"
        
    kb = InlineKeyboardBuilder()
    kb.button(text="📥 Excel ro'yxat", callback_data="export_users:excel")
    kb.button(text="📥 PDF ro'yxat", callback_data="export_users:pdf")
    kb.adjust(2)
    
    await message.answer(text, reply_markup=kb.as_markup())

# --- EXPORT CALLBACKS ---
@router.callback_query(F.data.startswith("export_stats:"))
async def handle_export_stats(callback: CallbackQuery):
    if not is_admin_user(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return
        
    format_type = callback.data.split(":")[1]
    await callback.answer("⏳ Hisobot tayyorlanmoqda...", show_alert=False)
    
    try:
        stats = db.get_statistics()
        file_path = export_statistics_report(stats, format_type)
        if os.path.exists(file_path):
            doc = FSInputFile(file_path)
            await callback.message.reply_document(
                doc,
                caption=f"📊 Edu Master Bot tizim statistikasi ({format_type.upper()})"
            )
        else:
            await callback.message.answer("⚠️ Hisobot fayli topilmadi.")
    except Exception as e:
        logger.error(f"Error exporting stats: {e}")
        await callback.message.answer(f"⚠️ Xatolik yuz berdi: {e}")

@router.callback_query(F.data.startswith("export_users:"))
async def handle_export_users(callback: CallbackQuery):
    if not is_admin_user(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return
        
    format_type = callback.data.split(":")[1]
    await callback.answer("⏳ Ro'yxat tayyorlanmoqda...", show_alert=False)
    
    try:
        users = db.get_all_users()
        file_path = export_users_list(users, format_type)
        if os.path.exists(file_path):
            doc = FSInputFile(file_path)
            await callback.message.reply_document(
                doc,
                caption=f"👥 Edu Master Bot foydalanuvchilar ro'yxati ({format_type.upper()})"
            )
        else:
            await callback.message.answer("⚠️ Ro'yxat fayli topilmadi.")
    except Exception as e:
        logger.error(f"Error exporting users list: {e}")
        await callback.message.answer(f"⚠️ Xatolik yuz berdi: {e}")

# --- 📢 XABAR YUBORISH (BROADCAST) ---
@router.message(F.text == "📢 Xabar yuborish")
async def start_broadcast(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        return
        
    await message.answer(
        "📢 <b>Barcha foydalanuvchilarga yuboriladigan xabar matnini yuboring:</b>\n\n"
        "Xabar rasm, video, hujjat ko'rinishida yoki oddiy matn bo'lishi mumkin.",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_broadcast_msg)

@router.message(AdminStates.waiting_for_broadcast_msg)
async def process_broadcast_message(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        await state.clear()
        return
        
    if message.text in ["🏠 Bosh menuga qaytish", "↩️ Ortga qaytish"]:
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_admin_menu_keyboard())
        return

        
    users = db.get_all_users()
    if not users:
        await message.answer("⚠️ Botda hech qanday foydalanuvchi yo'q!", reply_markup=get_admin_menu_keyboard())
        await state.clear()
        return
        
    status_msg = await message.answer(f"⏳ <b>Xabar yuborish boshlandi. Jami qabul qiluvchilar: {len(users)} ta...</b>")
    await state.clear()
    
    success_count = 0
    fail_count = 0
    
    for u in users:
        try:
            # Send duplicate copy of message to users
            await message.copy_to(chat_id=u["telegram_id"])
            success_count += 1
            # Add anti-flood delay (approx 30 messages per second maximum, so 0.05s sleep is extremely safe)
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.warning(f"Failed to send broadcast to user {u['telegram_id']}: {e}")
            fail_count += 1
            
    await status_msg.delete()
    await message.answer(
        "✅ <b>Xabar tarqatish muvaffaqiyatli yakunlandi!</b>\n\n"
        f"📥 Yetkazildi: <b>{success_count} ta</b> foydalanuvchiga\n"
        f"❌ Yetkazilmadi (bloklanganlar): <b>{fail_count} ta</b>",
        reply_markup=get_admin_menu_keyboard()
    )

# --- 🔐 ADMINLAR BOSHQARUVI (ADMIN MANAGEMENT) ---
@router.message(F.text == "🔐 Adminlar")
async def manage_admins_menu(message: Message):
    if not is_admin_user(message.from_user.id):
        return
        
    # Get current admins
    admins = db.get_all_admins()
    
    text = (
        "🔐 <b>ADMINISTRATORLARNI BOSHQARISH BO'LIMI</b>\n\n"
        f"👑 <b>Asosiy Yaratuvchi (Owner):</b> <code>{Config.ADMIN_ID}</code>\n\n"
        "👤 <b>Tizimdagi qo'shimcha adminlar ro'yxati:</b>\n"
    )
    
    if admins:
        for idx, adm in enumerate(admins, 1):
            text += f"▪️ {idx}. ID: <code>{adm['telegram_id']}</code> (Qo'shilgan: <i>{adm['added_date']}</i>)\n"
    else:
        text += "<i>Hozircha qo'shimcha adminlar yo'q.</i>\n"
        
    # Inline buttons
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Yangi admin qo'shish", callback_data="manage_admin_add")
    kb.button(text="❌ Adminni o'chirish", callback_data="manage_admin_del")
    kb.adjust(1)
    
    await message.answer(text, reply_markup=kb.as_markup())

# Callback: Admin add trigger
@router.callback_query(F.data == "manage_admin_add")
async def callback_admin_add_trigger(callback: CallbackQuery, state: FSMContext):
    if not is_admin_user(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return
        
    await callback.message.delete()
    await callback.message.answer(
        "🔐 <b>Yangi administrator qo'shish</b>\n\n"
        "Iltimos, yangi adminning <b>Telegram ID</b> raqamini yuboring:\n"
        "<i>(Masalan: <code>12345678</code>)</i>",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_new_admin_id)
    await callback.answer()

# Process new admin ID input
@router.message(AdminStates.waiting_for_new_admin_id)
async def process_new_admin_id(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        await state.clear()
        return
        
    input_text = message.text.strip()
    if input_text in ["🏠 Bosh menuga qaytish", "↩️ Ortga qaytish"]:
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_admin_menu_keyboard())
        return
        
    if not input_text.isdigit():
        await message.answer(
            "⚠️ <b>Xatolik!</b>\n\nTelegram ID faqat raqamlardan iborat bo'lishi kerak. Iltimos raqam ko'rinishida yuboring:",
            reply_markup=get_back_keyboard()
        )
        return
        
    new_admin_id = int(input_text)

    
    # Check if already admin
    if db.is_admin(new_admin_id, Config.ADMIN_ID):
        await message.answer("⚠️ Ushbu foydalanuvchi allaqachon administrator ro'yxatida bor! Boshqa ID yuboring:")
        return
        
    # Add to DB
    db.add_admin(new_admin_id)
    await state.clear()
    
    await message.answer(
        f"✅ <b>Telegram ID <code>{new_admin_id}</code> muvaffaqiyatli administrator qilib qo'shildi!</b>",
        reply_markup=get_admin_menu_keyboard()
    )

# Callback: Admin delete list trigger
@router.callback_query(F.data == "manage_admin_del")
async def callback_admin_del_trigger(callback: CallbackQuery):
    if not is_admin_user(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return
        
    admins = db.get_all_admins()
    if not admins:
        await callback.answer("⚠️ O'chirish uchun qo'shimcha administratorlar mavjud emas!", show_alert=True)
        return
        
    kb = InlineKeyboardBuilder()
    for adm in admins:
        # Check user details if exists
        user_info = db.get_user(adm["telegram_id"])
        name_str = f" - {user_info['full_name']}" if user_info else ""
        kb.button(
            text=f"❌ O'chirish (ID: {adm['telegram_id']}{name_str})", 
            callback_data=f"del_admin_id:{adm['telegram_id']}"
        )
    kb.button(text="↩️ Bekor qilish", callback_data="manage_admin_cancel")
    kb.adjust(1)
    
    await callback.message.edit_text(
        "❌ <b>O'chirmoqchi bo'lgan administratoringizni tanlang:</b>",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

# Callback: Delete specific admin ID
@router.callback_query(F.data.startswith("del_admin_id:"))
async def callback_delete_admin_id(callback: CallbackQuery):
    if not is_admin_user(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return
        
    target_id = int(callback.data.split(":")[1])
    
    # Remove from database
    db.remove_admin(target_id)
    
    await callback.answer("✅ Administrator muvaffaqiyatli o'chirildi!", show_alert=True)
    await callback.message.delete()
    
    # Resend updated list
    # Emulate message wrapper to reuse manage_admins_menu
    class FakeMessage:
        def __init__(self, from_user, chat):
            self.from_user = from_user
            self.chat = chat
        async def answer(self, text, reply_markup=None):
            return await callback.message.answer(text, reply_markup=reply_markup)
            
    fake_msg = FakeMessage(callback.from_user, callback.message.chat)
    await manage_admins_menu(fake_msg)

# Callback: Cancel action
@router.callback_query(F.data == "manage_admin_cancel")
async def callback_manage_admin_cancel(callback: CallbackQuery):
    await callback.message.delete()
    
    # Resend updated list
    class FakeMessage:
        def __init__(self, from_user, chat):
            self.from_user = from_user
            self.chat = chat
        async def answer(self, text, reply_markup=None):
            return await callback.message.answer(text, reply_markup=reply_markup)
            
    fake_msg = FakeMessage(callback.from_user, callback.message.chat)
    await manage_admins_menu(fake_msg)
    await callback.answer()

# --- ⚙️ MAJBURIY KANALLAR ---
@router.message(F.text == "⚙️ Majburiy kanallar")
async def manage_channels(message: Message):
    if not is_admin_user(message.from_user.id):
        return
        
    channels = db.get_all_channels()
    
    text = "⚙️ <b>Majburiy a'zolik kanallarini boshqarish</b>\n\n"
    if channels:
        for idx, ch in enumerate(channels, 1):
            text += f"{idx}. <b>ID:</b> {ch['channel_id']} \n   <b>URL:</b> {ch['url']}\n"
    else:
        text += "<i>Hozircha hech qanday kanal qo'shilmagan.</i>\n"
        
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Kanal qo'shish", callback_data="add_channel")
    kb.button(text="❌ Kanal o'chirish", callback_data="del_channel_list")
    kb.adjust(2)
    
    await message.answer(text, reply_markup=kb.as_markup(), disable_web_page_preview=True)

@router.callback_query(F.data == "add_channel")
async def add_channel_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin_user(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    
    await callback.message.delete()
    await callback.message.answer(
        "➕ <b>Yangi kanal qo'shish</b>\n\n"
        "Kanalning username yoki ID sini kiriting (masalan: @edumaster_channel yoki -100123456789):",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_channel_id)

@router.message(AdminStates.waiting_for_channel_id)
async def add_channel_id(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        return
        
    text = message.text.strip()
    if text in ["🏠 Bosh menuga qaytish", "↩️ Ortga qaytish"]:
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_admin_menu_keyboard())
        return
        
    await state.update_data(channel_id=text)
    await message.answer(
        "Kanalning taklif havolasini (URL) yuboring (masalan: https://t.me/edumaster_channel):",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_channel_url)

@router.message(AdminStates.waiting_for_channel_url)
async def add_channel_url(message: Message, state: FSMContext):
    if not is_admin_user(message.from_user.id):
        return
        
    text = message.text.strip()
    if text in ["🏠 Bosh menuga qaytish", "↩️ Ortga qaytish"]:
        await state.clear()
        await message.answer("🏠 Bosh menyuga qaytildi.", reply_markup=get_admin_menu_keyboard())
        return
        
    data = await state.get_data()
    channel_id = data['channel_id']
    url = text
    
    # Professional check: verify if the bot is admin in the channel
    try:
        from loader import bot
        # Format channel_id properly
        check_id = channel_id
        if not check_id.startswith("@") and not check_id.startswith("-"):
            check_id = f"@{check_id}"
            
        bot_member = await bot.get_chat_member(chat_id=check_id, user_id=bot.id)
        if bot_member.status not in ["administrator", "creator"]:
            await message.answer(
                "⚠️ <b>Xatolik!</b>\n"
                "Bot ushbu kanalda administrator emas. Iltimos, avval botni kanalga administrator qilib qo'shing va qayta urinib ko'ring.",
                reply_markup=get_admin_menu_keyboard()
            )
            await state.clear()
            return
    except Exception as e:
        logger.error(f"Error verifying channel: {e}")
        await message.answer(
            "⚠️ <b>Xatolik!</b>\n"
            "Kanalni topib bo'lmadi yoki botning kanalga kirish huquqi yo'q. "
            "Kanal ID si (yoki username) to'g'riligini va bot kanalda admin ekanligini tekshiring.",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.clear()
        return

    db.add_channel(channel_id, url)
    await state.clear()
    
    await message.answer(f"✅ Kanal muvaffaqiyatli qo'shildi va tekshirildi:\n<b>{channel_id}</b>", reply_markup=get_admin_menu_keyboard())

@router.callback_query(F.data == "del_channel_list")
async def del_channel_list(callback: CallbackQuery):
    if not is_admin_user(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
        
    channels = db.get_all_channels()
    if not channels:
        await callback.answer("Kanal yo'q!", show_alert=True)
        return
        
    kb = InlineKeyboardBuilder()
    for ch in channels:
        kb.button(text=f"❌ {ch['channel_id']}", callback_data=f"del_channel:{ch['channel_id']}")
    kb.button(text="↩️ Bekor qilish", callback_data="manage_admin_cancel")
    kb.adjust(1)
    
    await callback.message.edit_text("❌ <b>O'chirmoqchi bo'lgan kanalni tanlang:</b>", reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("del_channel:"))
async def del_channel_callback(callback: CallbackQuery):
    if not is_admin_user(callback.from_user.id):
        return
    channel_id = callback.data.split(":", 1)[1]
    db.remove_channel(channel_id)
    await callback.answer("Kanal o'chirildi", show_alert=True)
    await callback.message.delete()
    
    fake_msg = type("FakeMessage", (), {"from_user": callback.from_user, "answer": callback.message.answer})()
    await manage_channels(fake_msg)
