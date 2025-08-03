
import os
import json
import shutil
from datetime import datetime, timedelta
import os
import json
import shutil
from datetime import datetime
import pytz

def get_iran_time():
    iran_tz = pytz.timezone('Asia/Tehran')
    return datetime.now(iran_tz)

def save_user_data(user_id, username, user_data, user_dir='users_data', backup_dir='backups'):
    os.makedirs(user_dir, exist_ok=True)
    os.makedirs(backup_dir, exist_ok=True)

    filename = f"{username or user_id}.json"
    file_path = os.path.join(user_dir, filename)

    # ذخیره فایل اصلی
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)

    # ساخت بکاپ
    iran_time = get_iran_time().strftime("%Y-%m-%d_%H-%M-%S")
    backup_name = f"{username or user_id}_{iran_time}.json"
    backup_path = os.path.join(backup_dir, backup_name)

    shutil.copy(file_path, backup_path)

def load_user_data(user_id, username, user_dir='users_data'):
    filename = f"{username or user_id}.json"
    file_path = os.path.join(user_dir, filename)
    if not os.path.exists(file_path):
        return {"traders": {}, "username": username or ""}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_iran_time():
    utc_time = datetime.utcnow()
    iran_time = utc_time + timedelta(hours=3, minutes=30)  # ساعت ایران
    return iran_time

def save_data_with_backup(data, file_path='data/data.json', backup_dir='backups'):
    # ذخیره داده‌ها در فایل اصلی
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    # ساخت پوشه بکاپ اگر نبود
    os.makedirs(backup_dir, exist_ok=True)

    # ثبت زمان به وقت ایران
    iran_time = get_iran_time().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = os.path.join(backup_dir, f"backup_{iran_time}.json")

    # کپی فایل اصلی به بکاپ
    shutil.copy(file_path, backup_file)
import os
import json
from datetime import datetime

DATA_FILE = "data/data.json"
BACKUP_DIR = "backups"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user_data(user_id, username, data):
    # ذخیره فایل اصلی
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # ساخت پوشه بکاپ (اگه وجود نداره)
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    # ساخت اسم فایل بکاپ با تاریخ روز
    date_str = datetime.now().strftime("%Y-%m-%d")
    backup_file = os.path.join(BACKUP_DIR, f"backup_{date_str}.json")

    # ذخیره نسخه پشتیبان
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

import os
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
def split_text(text, max_length=4000):
    chunks = []
    while len(text) > max_length:
        split_index = text.rfind('\n', 0, max_length)
        if split_index == -1:
            split_index = max_length
        chunks.append(text[:split_index])
        text = text[split_index:].lstrip('\n')
    chunks.append(text)
    return chunks
# ========== پیکربندی ==========
API_TOKEN = '7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ'
ADMIN_ID = 805989529  # عددی

# ========== ساختار فایل ==========
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
DATA_FILE = os.path.join(DATA_DIR, "users.json")

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user_data(user_id, username, data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_user_data(data, user_id, username=""):
    if user_id not in data:
        data[user_id] = {
            "traders": {},
            "alert_value": 100000,
            "username": username or "نداره"
        }
    else:
        data[user_id]["username"] = username or "نداره"
    return data

# ========== وضعیت‌ها ==========
class AddTrader(StatesGroup):
    waiting_for_address = State()
    waiting_for_nickname = State()
    waiting_for_alert_value = State()

class DeleteTrader(StatesGroup):
    waiting_for_delete_address = State()

# ========== راه‌اندازی ربات ==========
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ========== منوی اصلی ==========
main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add("➕ افزودن تریدر", "🗑️ حذف تریدر")
main_menu.add("📋 لیست تریدرها", "📊 پروفایل")

# ========== start ==========
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer("سلام 👋 یکی از گزینه‌های زیر رو انتخاب کن:", reply_markup=main_menu)

# ========== افزودن تریدر ==========
# مراحل جدید برای افزودن تریدر

class AddTrader(StatesGroup):
    waiting_for_address = State()
    waiting_for_nickname = State()
    waiting_for_alert_value = State()

@dp.message_handler(lambda msg: msg.text == "➕ افزودن تریدر")
async def add_trader_step1(message: types.Message):
    await AddTrader.waiting_for_address.set()
    await message.answer("آدرس تریدر رو وارد کن:")

@dp.message_handler(state=AddTrader.waiting_for_address, content_types=types.ContentTypes.TEXT)
async def add_trader_step2(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    await AddTrader.next()
    await message.answer("اسم مستعار تریدر رو بنویس:")

@dp.message_handler(state=AddTrader.waiting_for_nickname, content_types=types.ContentTypes.TEXT)
async def add_trader_step3(message: types.Message, state: FSMContext):
    await state.update_data(nickname=message.text.strip())
    await AddTrader.next()
    await message.answer("از چه مبلغی به بالا می‌خوای هشدار بگیری؟ (مثلاً: 150000)")

@dp.message_handler(state=AddTrader.waiting_for_alert_value, content_types=types.ContentTypes.TEXT)
async def add_trader_step4(message: types.Message, state: FSMContext):
    try:
        alert_value = int(message.text.strip())
    except ValueError:
        await message.answer("❌ لطفاً فقط عدد بنویس (مثلاً 150000).")
        return

    user_data = await state.get_data()
    address = user_data["address"]
    nickname = user_data["nickname"]
    user_id = str(message.from_user.id)
    username = message.from_user.username or "نداره"

    data = load_user_data(user_id, username)
    if user_id not in data:
        data[user_id] = {
            "traders": {},
            "alert_value": 100000,
            "username": username
        }

    # بررسی تکراری بودن آدرس
    if address in data[user_id]["traders"]:
        await message.answer("⚠️ این آدرس قبلاً ثبت شده.")
        await state.finish()
        return

    is_bot = 'bot' in nickname.lower() or 'bot' in address.lower()
    data[user_id]["traders"][address] = {
        "nickname": nickname,
        "is_bot": is_bot,
        "added_by": user_id,
        "added_by_username": username,
        "alert_value": alert_value
    }

    save_user_data(user_id, username, data)
    await state.finish()
    await message.answer("✅ تریدر با موفقیت ذخیره شد.")


# ========== لیست تریدرها ==========
@dp.message_handler(lambda msg: msg.text == "📋 لیست تریدرها")
async def list_traders(message: types.Message, state: FSMContext):
    await state.finish()  # این خط رو اضافه کن تا state تموم شه
    ...

    user_id = str(message.from_user.id)
    data = load_user_data(user_id, username)

    if user_id not in data or not data[user_id].get("traders"):
        await message.answer("📭 لیست تریدرها خالیه.")
        return

    traders = data[user_id]["traders"]
    msg = "📋 لیست تریدرها:\n\n"

    for address, info in traders.items():
        nickname = info.get("nickname", "نامشخص")
        added_by = info.get("added_by", "ناشناس")
        username = data.get(user_id, {}).get("username", "نداره")
        msg += (
            f"🏷️ {nickname}\n"
            f"🔗 {address}\n"
            f"👤 ID: `{added_by}`\n"
            f"🆔 @{username}\n"
            f"──────────────\n"
        )

    # استفاده از تابع split_text برای تقسیم پیام بلند
    for part in split_text(msg):
        await message.answer(part)
def split_text(text, max_length=4000):
    lines = text.split('\n')
    chunks = []
    current_chunk = ""

    for line in lines:
        if len(current_chunk) + len(line) + 1 <= max_length:
            current_chunk += line + '\n'
        else:
            chunks.append(current_chunk)
            current_chunk = line + '\n'

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


# ========== حذف تریدر ==========
class DeleteTrader(StatesGroup):
    waiting_for_delete_address = State()

@dp.message_handler(lambda msg: msg.text == "🗑️ حذف تریدر")
async def delete_trader_prompt(message: types.Message, state: FSMContext):
    await state.finish()
    ...

    user_id = str(message.from_user.id)
    username = message.from_user.username or "نداره"

    data = load_user_data(user_id, username)
    if user_id not in data:
        data[user_id] = {"traders": {}, "alert_value": 100000, "username": username}
    elif "username" not in data[user_id]:
        data[user_id]["username"] = username

    traders = data[user_id].get("traders", {})
    if not traders:
        await message.answer("❌ هیچ تریدری ثبت نشده.")
        return

    msg_text = "\n".join([f"{info['nickname']} → `{addr}`" for addr, info in traders.items()])
    await message.answer(f"کد آدرس تریدر مورد نظر برای حذف رو بفرست:\n\n{msg_text}", parse_mode="Markdown")
    await DeleteTrader.waiting_for_delete_address.set()

@dp.message_handler(state=DeleteTrader.waiting_for_delete_address, content_types=types.ContentTypes.TEXT)
async def delete_trader_execute(message: types.Message, state: FSMContext):
    address = message.text.strip()
    user_id = str(message.from_user.id)

    data = load_user_data(user_id, username)
    traders = data.get(user_id, {}).get("traders", {})

    if address in traders:
        del data[user_id]["traders"][address]
        save_user_data(user_id, username, data)
        await message.answer("✅ تریدر با موفقیت حذف شد.")
    else:
        await message.answer("❌ آدرس وارد شده در لیست شما نیست.")
    
    await state.finish()


# ========== پروفایل ==========
@dp.message_handler(lambda msg: msg.text == "📊 پروفایل")
async def user_profile(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_user_data(user_id, username)

    if user_id not in data:
        await message.answer("❌ هیچ اطلاعاتی برای شما ثبت نشده.")
        return

    user_info = data[user_id]
    username = message.from_user.username or "نداره"
    count = len(user_info.get("traders", {}))

    text = f"""📊 پروفایل شما:

👤 یوزرنیم: @{username}
🆔 آیدی عددی: `{user_id}`
📈 تعداد تریدرهای ثبت‌شده: {count}
"""
    await message.answer(text, parse_mode="Markdown")



# ========== اجرای ربات ==========
if __name__ == "__main__":
    print("ربات اجرا شد...")
    executor.start_polling(dp, skip_updates=True)
ADMIN_ID = 805989529  # آیدی تلگرام خودت

def split_text(text, max_length=4000):
    parts = []
    while len(text) > max_length:
        split_pos = text.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        parts.append(text[:split_pos])
        text = text[split_pos:]
    parts.append(text)
    return parts

@dp.message_handler(commands=['user_data'])
async def user_data_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ شما دسترسی ندارید.")
        return
    data = load_user_data(user_id, username)
    if not data:
        await message.answer("هیچ داده‌ای ثبت نشده.")
        return

    text = ""
    for user_id, info in data.items():
        username = info.get("username", "نداره")
        text += f"\n👤 User ID: {user_id}\n"
        text += f"🔗 Username: @{username}\n"
        for addr, t in info.get("traders", {}).items():
            text += f"• {t['nickname']} → {addr}\n"

    messages = split_text(text)
    for part in messages:
        await message.answer(part)
def split_text(text, limit=4000):
    lines = text.split('\n')
    chunks = []
    current = ''
    for line in lines:
        if len(current) + len(line) + 1 > limit:
            chunks.append(current)
            current = ''
        current += line + '\n'
    if current:
        chunks.append(current)
    return chunks
