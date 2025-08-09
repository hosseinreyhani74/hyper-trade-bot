import os
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import pytz

# ==================== تنظیمات ====================
API_TOKEN = '7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ'  # توکن ربات تلگرام خودت
ADMIN_ID = 805989529  # آیدی عددی خودت در تلگرام

# پوشه‌های ذخیره‌سازی داده‌ها
DATA_DIR = "data"
BACKUP_DIR = "backups"

# ساخت پوشه‌ها در صورت عدم وجود
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# فایل اصلی داده‌ها
DATA_FILE = os.path.join(DATA_DIR, "users_data.json")

# ==================== تابع گرفتن زمان ایران ====================
def get_iran_time():
    iran_tz = pytz.timezone('Asia/Tehran')
    return datetime.now(iran_tz)

# ==================== تابع بارگذاری داده‌ها ====================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ==================== تابع ذخیره داده‌ها با بکاپ ====================
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    # بکاپ‌گیری
    iran_time_str = get_iran_time().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = os.path.join(BACKUP_DIR, f"backup_{iran_time_str}.json")
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ==================== توابع کمکی ====================
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

# ==================== تعریف حالت‌ها (FSM) ====================
class AddTrader(StatesGroup):
    waiting_for_address = State()
    waiting_for_nickname = State()
    waiting_for_alert_value = State()

class DeleteTrader(StatesGroup):
    waiting_for_delete_address = State()

# ==================== راه‌اندازی ربات ====================
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ==================== کیبورد منوی اصلی ====================
main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add("➕ افزودن تریدر", "🗑️ حذف تریدر")
main_menu.add("📋 لیست تریدرها", "📊 پروفایل")

# ==================== هندلر شروع /start ====================
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer("سلام! یکی از گزینه‌های زیر رو انتخاب کن:", reply_markup=main_menu)

# ==================== افزودن تریدر ====================
@dp.message_handler(lambda m: m.text == "➕ افزودن تریدر")
async def add_trader_start(message: types.Message):
    await AddTrader.waiting_for_address.set()
    await message.answer("آدرس تریدر رو وارد کن:")

@dp.message_handler(state=AddTrader.waiting_for_address, content_types=types.ContentTypes.TEXT)
async def add_trader_get_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    await AddTrader.next()
    await message.answer("اسم مستعار تریدر رو وارد کن:")

@dp.message_handler(state=AddTrader.waiting_for_nickname, content_types=types.ContentTypes.TEXT)
async def add_trader_get_nickname(message: types.Message, state: FSMContext):
    await state.update_data(nickname=message.text.strip())
    await AddTrader.next()
    await message.answer("از چه مبلغی به بالا می‌خوای هشدار بگیری؟ (مثلاً: 150000)")

@dp.message_handler(state=AddTrader.waiting_for_alert_value, content_types=types.ContentTypes.TEXT)
async def add_trader_get_alert_value(message: types.Message, state: FSMContext):
    try:
        alert_value = int(message.text.strip())
    except ValueError:
        await message.answer("❌ لطفاً فقط عدد وارد کن.")
        return

    data = load_data()
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"user_{user_id}"

    # گرفتن اطلاعات موقت از FSM
    state_data = await state.get_data()
    address = state_data["address"]
    nickname = state_data["nickname"]

    # آماده کردن ساختار داده کاربر اگر نبود
    if user_id not in data:
        data[user_id] = {
            "username": username,
            "traders": []
        }
    else:
        data[user_id]["username"] = username

    # بررسی تکراری بودن آدرس
    if any(t['address'] == address for t in data[user_id]["traders"]):
        await message.answer("⚠️ این آدرس قبلاً ثبت شده.")
        await state.finish()
        return

    # افزودن تریدر جدید
    new_trader = {
        "address": address,
        "nickname": nickname,
        "alert_value": alert_value,
        "added_at": get_iran_time().strftime("%Y-%m-%d %H:%M:%S")
    }
    data[user_id]["traders"].append(new_trader)

    # ذخیره داده‌ها
    save_data(data)
    await message.answer("✅ تریدر با موفقیت ثبت شد.")
    await state.finish()

# ==================== لیست تریدرها ====================
@dp.message_handler(lambda m: m.text == "📋 لیست تریدرها")
async def list_traders(message: types.Message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data or not data[user_id].get("traders"):
        await message.answer("📭 لیست تریدرها خالی است.")
        return

    trader_texts = []
    for t in data[user_id]["traders"]:
        trader_texts.append(
            f"🏷️ {t['nickname']}\n🔗 {t['address']}\n💰 هشدار بالای: {t['alert_value']}\n📅 ثبت شده در: {t['added_at']}\n─────────────"
        )
    full_text = "📋 لیست تریدرهای شما:\n\n" + "\n".join(trader_texts)
    for part in split_text(full_text):
        await message.answer(part)

# ==================== حذف تریدر ====================
@dp.message_handler(lambda m: m.text == "🗑️ حذف تریدر")
async def delete_trader_start(message: types.Message, state: FSMContext):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data or not data[user_id].get("traders"):
        await message.answer("❌ هیچ تریدری ثبت نشده.")
        return

    trader_list_text = "\n".join(
        [f"{idx+1}. {t['nickname']} → {t['address']}" for idx, t in enumerate(data[user_id]["traders"])]
    )
    await message.answer(f"کد عددی تریدر مورد نظر برای حذف را بفرستید:\n\n{trader_list_text}")
    await DeleteTrader.waiting_for_delete_address.set()

@dp.message_handler(state=DeleteTrader.waiting_for_delete_address, content_types=types.ContentTypes.TEXT)
async def delete_trader_execute(message: types.Message, state: FSMContext):
    data = load_data()
    user_id = str(message.from_user.id)

    if user_id not in data or not data[user_id].get("traders"):
        await message.answer("❌ هیچ تریدری برای حذف وجود ندارد.")
        await state.finish()
        return

    try:
        idx = int(message.text.strip()) - 1
        if idx < 0 or idx >= len(data[user_id]["traders"]):
            await message.answer("❌ عدد وارد شده معتبر نیست.")
            return
    except ValueError:
        await message.answer("❌ لطفاً فقط عدد وارد کنید.")
        return

    removed = data[user_id]["traders"].pop(idx)
    save_data(data)
    await message.answer(f"✅ تریدر '{removed['nickname']}' با موفقیت حذف شد.")
    await state.finish()

# ==================== نمایش پروفایل ====================
@dp.message_handler(lambda m: m.text == "📊 پروفایل")
async def show_profile(message: types.Message):
    data = load_data()
    user_id = str(message.from_user.id)

    if user_id not in data:
        await message.answer("❌ پروفایل شما پیدا نشد. لطفاً ابتدا تریدر اضافه کنید.")
        return

    user_info = data[user_id]
    traders = user_info.get("traders", [])
    trader_count = len(traders)
    username = user_info.get("username", "ندارد")

    text = (
        f"📊 پروفایل شما:\n\n"
        f"👤 نام کاربری: @{username}\n"
        f"🆔 آیدی عددی: {user_id}\n"
        f"📈 تعداد تریدرهای ثبت‌شده: {trader_count}\n"
    )
    if trader_count > 0:
        text += "\n📋 لیست تریدرها:\n"
        for t in traders:
            text += f"🏷️ {t['nickname']} → 🔗 {t['address']}\n"

    await message.answer(text)

# ==================== دستور مدیریت: نمایش کل داده‌ها ====================
@dp.message_handler(commands=["user_data"])
async def user_data_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ شما دسترسی ندارید.")
        return
    data = load_data()
    if not data:
        await message.answer("❌ هیچ داده‌ای ثبت نشده است.")
        return

    text = ""
    for uid, info in data.items():
        uname = info.get("username", "ندارد")
        text += f"\n👤 User ID: {uid}\n🔗 Username: @{uname}\n"
        for t in info.get("traders", []):
            text += f"• {t['nickname']} → {t['address']}\n"

    for part in split_text(text):
        await message.answer(part)

# ==================== اجرای ربات ====================
if __name__ == "__main__":
    print("ربات در حال اجراست...")
    executor.start_polling(dp, skip_updates=True)
