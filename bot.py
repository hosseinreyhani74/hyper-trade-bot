import os
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext

# === تنظیمات ربات ===
API_TOKEN = '7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ'  # توکن ربات تلگرام
ADMIN_ID = 805989529  # ایدی عددی تلگرام خودت برای دسترسی ادمین

# === ساختار پوشه‌ها و فایل‌ها ===
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)  # اطمینان از وجود پوشه ذخیره‌سازی

# فایل اصلی ذخیره داده‌ها
DATA_FILE = os.path.join(DATA_DIR, "users_data.json")

# === بارگذاری داده‌های کاربر از فایل ===
def load_all_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Load data error: {e}")
        return {}

# === ذخیره داده‌های کاربران به فایل ===
def save_all_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[ERROR] Save data error: {e}")

# === تعریف حالات FSM برای افزودن تریدر ===
class AddTraderStates(StatesGroup):
    waiting_for_address = State()
    waiting_for_nickname = State()
    waiting_for_alert_value = State()

# === تعریف حالات FSM برای حذف تریدر ===
class DeleteTraderStates(StatesGroup):
    waiting_for_address = State()

# === راه‌اندازی ربات و دیسپچر ===
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# === کیبورد اصلی ===
main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add("➕ افزودن تریدر", "🗑️ حذف تریدر")
main_menu.add("📋 لیست تریدرها", "📊 پروفایل")

# === تابع کمکی تقسیم متن طولانی برای پیام‌های تلگرام ===
def split_text(text, max_length=4000):
    parts = []
    while len(text) > max_length:
        split_pos = text.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        parts.append(text[:split_pos])
        text = text[split_pos:].lstrip('\n')
    parts.append(text)
    return parts

# ======== هندلر دستور start ========
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    user = message.from_user
    await message.answer(
        f"سلام {user.full_name} 👋\n"
        "من ربات مدیریت تریدرهای تو هستم.\n"
        "از منوی پایین یکی از گزینه‌ها رو انتخاب کن.",
        reply_markup=main_menu
    )
# ======= افزودن تریدر - مرحله اول: گرفتن آدرس =======
@dp.message_handler(lambda msg: msg.text == "➕ افزودن تریدر")
async def add_trader_start(message: types.Message):
    await AddTraderStates.waiting_for_address.set()
    await message.answer("لطفاً آدرس تریدر را وارد کنید:")

# ======= افزودن تریدر - مرحله دوم: گرفتن اسم مستعار =======
@dp.message_handler(state=AddTraderStates.waiting_for_address, content_types=types.ContentTypes.TEXT)
async def add_trader_address_received(message: types.Message, state: FSMContext):
    address = message.text.strip()
    if not address:
        await message.answer("❌ آدرس نمی‌تواند خالی باشد. دوباره وارد کنید.")
        return
    await state.update_data(address=address)
    await AddTraderStates.next()
    await message.answer("حالا اسم مستعار تریدر را بنویس:")

# ======= افزودن تریدر - مرحله سوم: گرفتن مقدار هشدار =======
@dp.message_handler(state=AddTraderStates.waiting_for_nickname, content_types=types.ContentTypes.TEXT)
async def add_trader_nickname_received(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    if not nickname:
        await message.answer("❌ اسم مستعار نمی‌تواند خالی باشد. لطفا دوباره وارد کن.")
        return
    await state.update_data(nickname=nickname)
    await AddTraderStates.next()
    await message.answer("از چه مبلغی به بالا می‌خوای هشدار بگیری؟ (مثلا: 150000)")

@dp.message_handler(state=AddTraderStates.waiting_for_alert_value, content_types=types.ContentTypes.TEXT)
async def add_trader_alert_value_received(message: types.Message, state: FSMContext):
    try:
        alert_value = int(message.text.strip())
        if alert_value <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ لطفا فقط عدد مثبت وارد کن (مثلا 150000). دوباره تلاش کن.")
        return

    data = await state.get_data()
    address = data.get("address")
    nickname = data.get("nickname")
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"user_{user_id}"

    all_data = load_all_data()

    if user_id not in all_data:
        all_data[user_id] = {
            "username": username,
            "traders": {}
        }

    # بررسی تکراری بودن آدرس
    if address in all_data[user_id]["traders"]:
        await message.answer("⚠️ این آدرس قبلا ثبت شده است.")
        await state.finish()
        return

    # ذخیره تریدر جدید
    all_data[user_id]["traders"][address] = {
        "nickname": nickname,
        "alert_value": alert_value,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    save_all_data(all_data)
    await state.finish()
    await message.answer("✅ تریدر با موفقیت ثبت شد.", reply_markup=main_menu)

# ======= لیست تریدرها =======
@dp.message_handler(lambda msg: msg.text == "📋 لیست تریدرها")
async def list_traders_handler(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"user_{user_id}"

    all_data = load_all_data()
    if user_id not in all_data or not all_data[user_id]["traders"]:
        await message.answer("📭 هیچ تریدری ثبت نشده است.", reply_markup=main_menu)
        return

    traders = all_data[user_id]["traders"]

    text = "📋 لیست تریدرهای شما:\n\n"
    for addr, info in traders.items():
        text += (
            f"🏷️ {info['nickname']}\n"
            f"🔗 آدرس: {addr}\n"
            f"⚠️ مقدار هشدار: {info['alert_value']}\n"
            f"📅 تاریخ ثبت: {info['saved_at']}\n"
            "──────────────\n"
        )

    for part in split_text(text):
        await message.answer(part, reply_markup=main_menu)

# ======= حذف تریدر - شروع =======
@dp.message_handler(lambda msg: msg.text == "🗑️ حذف تریدر")
async def delete_trader_start(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"user_{user_id}"

    all_data = load_all_data()
    if user_id not in all_data or not all_data[user_id]["traders"]:
        await message.answer("❌ هیچ تریدری برای حذف ثبت نشده است.", reply_markup=main_menu)
        return

    traders = all_data[user_id]["traders"]

    text = "کد آدرس تریدر مورد نظر برای حذف را وارد کنید:\n\n"
    for addr, info in traders.items():
        text += f"🏷️ {info['nickname']} → `{addr}`\n"

    await message.answer(text, parse_mode="Markdown")
    await DeleteTraderStates.waiting_for_address.set()

# ======= حذف تریدر - دریافت آدرس و حذف =======
@dp.message_handler(state=DeleteTraderStates.waiting_for_address, content_types=types.ContentTypes.TEXT)
async def delete_trader_execute(message: types.Message, state: FSMContext):
    address = message.text.strip()
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"user_{user_id}"

    all_data = load_all_data()
    if user_id not in all_data or not all_data[user_id]["traders"]:
        await message.answer("❌ لیست شما خالی است.", reply_markup=main_menu)
        await state.finish()
        return

    traders = all_data[user_id]["traders"]
    if address not in traders:
        await message.answer("❌ این آدرس در لیست شما وجود ندارد.", reply_markup=main_menu)
        await state.finish()
        return

    del traders[address]
    save_all_data(all_data)

    await message.answer("✅ تریدر با موفقیت حذف شد.", reply_markup=main_menu)
    await state.finish()

# ======= نمایش پروفایل کاربر =======
@dp.message_handler(lambda msg: msg.text == "📊 پروفایل")
async def profile_handler(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"user_{user_id}"

    all_data = load_all_data()
    if user_id not in all_data:
        await message.answer("❌ هیچ داده‌ای برای شما ثبت نشده است.", reply_markup=main_menu)
        return

    user_info = all_data[user_id]
    traders = user_info.get("traders", {})
    trader_count = len(traders)

    text = (
        f"📊 پروفایل شما:\n\n"
        f"👤 نام کاربری: @{username}\n"
        f"🆔 آیدی عددی: {user_id}\n"
        f"📈 تعداد تریدرهای ثبت شده: {trader_count}\n"
    )

    if trader_count > 0:
        text += "\n📋 لیست تریدرها:\n"
        for addr, info in traders.items():
            text += f"🏷️ {info['nickname']} → 🔗 {addr}\n"

    await message.answer(text, reply_markup=main_menu)
# ======= دستور مخصوص ادمین برای دیدن داده‌ها =======
@dp.message_handler(commands=['user_data'])
async def user_data_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ شما دسترسی ندارید.")
        return

    all_data = load_all_data()
    if not all_data:
        await message.answer("هیچ داده‌ای ثبت نشده است.")
        return

    text = ""
    for user_id, info in all_data.items():
        username = info.get("username", "ندارد")
        text += f"\n👤 User ID: {user_id}\n"
        text += f"🔗 Username: @{username}\n"
        for addr, t in info.get("traders", {}).items():
            text += f"• {t['nickname']} → {addr}\n"
        text += "──────────────\n"

    messages = split_text(text)
    for part in messages:
        await message.answer(part)

# ======= تابع گزارش خطا =======
@dp.errors_handler()
async def error_handler(update, exception):
    try:
        await bot.send_message(ADMIN_ID, f"⚠️ خطا در ربات: {exception}")
    except Exception:
        pass
    return True

# ======= حذف تبلیغات (چون خودت گفتی نباشه) =======
# هیچ کدی برای تبلیغات اضافه نکردم، بنابراین تبلیغ نخواهد آمد

# ======= شروع ربات =======
if __name__ == "__main__":
    print("ربات شروع به کار کرد...")
    executor.start_polling(dp, skip_updates=True)
