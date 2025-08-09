import os
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# ======== تنظیمات =========
API_TOKEN = "7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ"  # توکن ربات خودت
ADMIN_ID = 805989529  # آیدی تلگرام خودت (عدد)

# پوشه و فایل ذخیره داده‌ها
DATA_FOLDER = "user_data"
DATA_FILE = os.path.join(DATA_FOLDER, "data.json")

# ساخت فولدر اگر وجود نداشت
os.makedirs(DATA_FOLDER, exist_ok=True)

# ======== توابع بارگذاری و ذخیره داده‌ها ========
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        # اگر فایل خراب بود، دیتای خالی برگردون
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ======== تقسیم متن برای پیام‌های طولانی ========
def split_text(text, max_len=4000):
    lines = text.split('\n')
    chunks = []
    current = ""
    for line in lines:
        if len(current) + len(line) + 1 > max_len:
            chunks.append(current)
            current = ""
        current += line + "\n"
    if current:
        chunks.append(current)
    return chunks

# ======== تعریف حالت‌ها برای افزودن و حذف تریدر ========
class AddTrader(StatesGroup):
    waiting_for_address = State()
    waiting_for_nickname = State()

class DeleteTrader(StatesGroup):
    waiting_for_index = State()

# ======== راه‌اندازی ربات ========
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ======== کیبورد اصلی ========
main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add("➕ افزودن تریدر", "🗑️ حذف تریدر")
main_keyboard.add("📋 لیست تریدرها", "📊 پروفایل")

# ======== دستور start ========
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer(
        "سلام! یکی از گزینه‌های زیر را انتخاب کن:",
        reply_markup=main_keyboard,
    )

# ======== افزودن تریدر ========
@dp.message_handler(lambda m: m.text == "➕ افزودن تریدر")
async def add_trader_start(message: types.Message):
    await AddTrader.waiting_for_address.set()
    await message.answer("لطفاً آدرس تریدر را وارد کنید:")

@dp.message_handler(state=AddTrader.waiting_for_address)
async def add_trader_get_address(message: types.Message, state: FSMContext):
    address = message.text.strip()
    if not address:
        await message.answer("آدرس نامعتبر است، لطفاً مجدداً وارد کنید.")
        return
    await state.update_data(address=address)
    await AddTrader.next()
    await message.answer("اسم مستعار (nickname) تریدر را وارد کنید:")

@dp.message_handler(state=AddTrader.waiting_for_nickname)
async def add_trader_get_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    if not nickname:
        await message.answer("نام مستعار نامعتبر است، لطفاً مجدداً وارد کنید.")
        return

    user_id = str(message.from_user.id)
    username = message.from_user.username or f"user_{user_id}"

    data = load_data()

    if user_id not in data:
        data[user_id] = {"username": username, "traders": []}
    else:
        # به‌روزرسانی username در صورت تغییر
        data[user_id]["username"] = username

    user_traders = data[user_id]["traders"]

    # گرفتن داده‌های مرحله قبل
    state_data = await state.get_data()
    address = state_data["address"]

    # بررسی تکراری نبودن آدرس
    if any(t["address"] == address for t in user_traders):
        await message.answer("⚠️ این آدرس قبلاً ثبت شده است.")
        await state.finish()
        return

    # افزودن تریدر
    user_traders.append({"address": address, "nickname": nickname})

    save_data(data)

    await message.answer(f"✅ تریدر '{nickname}' با موفقیت ثبت شد.", reply_markup=main_keyboard)
    await state.finish()

# ======== لیست تریدرها ========
@dp.message_handler(lambda m: m.text == "📋 لیست تریدرها")
async def list_traders(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id not in data or not data[user_id].get("traders"):
        await message.answer("📭 شما هنوز هیچ تریدری ثبت نکرده‌اید.", reply_markup=main_keyboard)
        return

    text = "📋 لیست تریدرهای شما:\n\n"
    for idx, t in enumerate(data[user_id]["traders"], 1):
        text += f"{idx}. 🏷️ {t['nickname']} → 🔗 {t['address']}\n"

    for chunk in split_text(text):
        await message.answer(chunk, reply_markup=main_keyboard)

# ======== حذف تریدر ========
@dp.message_handler(lambda m: m.text == "🗑️ حذف تریدر")
async def delete_trader_start(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id not in data or not data[user_id].get("traders"):
        await message.answer("❌ هیچ تریدری برای حذف وجود ندارد.", reply_markup=main_keyboard)
        return

    text = "لطفاً شماره تریدری که می‌خواهید حذف کنید را وارد کنید:\n\n"
    for idx, t in enumerate(data[user_id]["traders"], 1):
        text += f"{idx}. 🏷️ {t['nickname']} → 🔗 {t['address']}\n"

    await DeleteTrader.waiting_for_index.set()
    await message.answer(text)

@dp.message_handler(state=DeleteTrader.waiting_for_index)
async def delete_trader_confirm(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id not in data or not data[user_id].get("traders"):
        await message.answer("❌ لیست تریدرها خالی است.", reply_markup=main_keyboard)
        await state.finish()
        return

    try:
        idx = int(message.text.strip()) - 1
        if idx < 0 or idx >= len(data[user_id]["traders"]):
            await message.answer("❌ شماره وارد شده معتبر نیست، لطفاً مجدداً تلاش کنید.")
            return
    except:
        await message.answer("❌ لطفاً فقط عدد وارد کنید.")
        return

    removed = data[user_id]["traders"].pop(idx)
    save_data(data)

    await message.answer(f"✅ تریدر '{removed['nickname']}' حذف شد.", reply_markup=main_keyboard)
    await state.finish()

# ======== نمایش پروفایل ========
@dp.message_handler(lambda m: m.text == "📊 پروفایل")
async def show_profile(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id not in data:
        await message.answer("❌ پروفایل پیدا نشد. لطفاً ابتدا تریدر اضافه کنید.", reply_markup=main_keyboard)
        return

    user = data[user_id]
    username = user.get("username", "ندارد")
    traders = user.get("traders", [])
    trader_count = len(traders)

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

    await message.answer(text, reply_markup=main_keyboard)

# ======== دستور ادمین برای دیدن کل داده‌ها ========
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
    for uid, user in data.items():
        uname = user.get("username", "ندارد")
        text += f"\n👤 User ID: {uid}\n🔗 Username: @{uname}\n"
        for t in user.get("traders", []):
            text += f"• {t['nickname']} → {t['address']}\n"

    for chunk in split_text(text):
        await message.answer(chunk)

# ======== اجرای ربات ========
if __name__ == "__main__":
    print("ربات در حال اجراست...")
    executor.start_polling(dp, skip_updates=True)
