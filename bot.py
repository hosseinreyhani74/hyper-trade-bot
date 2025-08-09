import os
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# =================== تنظیمات اولیه ===================
API_TOKEN = '7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ'  # توکن ربات خودت
ADMIN_ID = 805989529  # آیدی عددی تلگرام خودت

DATA_DIR = "data"  # فولدر ذخیره سازی دیتا
os.makedirs(DATA_DIR, exist_ok=True)

# =================== تعریف حالت‌ها (FSM) ===================
class AddTrader(StatesGroup):
    waiting_for_address = State()
    waiting_for_nickname = State()
    waiting_for_alert_value = State()

class DeleteTrader(StatesGroup):
    waiting_for_delete_address = State()

# =================== تابع‌های کمکی ===================
def get_user_file(user_id: str):
    """
    مسیر فایل ذخیره‌سازی کاربر را برمی‌گرداند.
    اینجا هر کاربر یک فایل جداگانه دارد به نام userID.json داخل فولدر data
    """
    return os.path.join(DATA_DIR, f"{user_id}.json")

def load_user_data(user_id: str):
    """
    داده‌های کاربر را از فایل می‌خواند.
    اگر فایل موجود نبود، دیکشنری اولیه خالی برمی‌گرداند.
    """
    filepath = get_user_file(user_id)
    if not os.path.exists(filepath):
        return {"traders": {}}
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if "traders" not in data:
                data["traders"] = {}
            return data
        except Exception as e:
            print(f"Error loading user data: {e}")
            return {"traders": {}}

def save_user_data(user_id: str, data: dict):
    """
    داده‌های کاربر را به فایل ذخیره می‌کند.
    """
    filepath = get_user_file(user_id)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def split_text(text: str, max_length=4000):
    """
    متن طولانی را به قسمت‌های مناسب برای ارسال در تلگرام تقسیم می‌کند.
    """
    lines = text.split('\n')
    chunks = []
    current_chunk = ""
    for line in lines:
        # +1 برای کاراکتر \n
        if len(current_chunk) + len(line) + 1 > max_length:
            chunks.append(current_chunk)
            current_chunk = ""
        current_chunk += line + "\n"
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

# =================== راه‌اندازی ربات ===================
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# =================== تعریف کیبورد اصلی ===================
main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add("➕ افزودن تریدر", "🗑️ حذف تریدر")
main_menu.add("📋 لیست تریدرها", "📊 پروفایل")

# =================== هندلر شروع ربات ===================
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer(
        "سلام! به ربات مدیریت تریدرها خوش آمدید.\n"
        "از منوی زیر گزینه‌ای انتخاب کنید:",
        reply_markup=main_menu
    )

# =================== افزودن تریدر ===================
@dp.message_handler(lambda msg: msg.text == "➕ افزودن تریدر")
async def cmd_add_trader_start(message: types.Message):
    await AddTrader.waiting_for_address.set()
    await message.answer("لطفاً آدرس تریدر را وارد کنید:")

@dp.message_handler(state=AddTrader.waiting_for_address, content_types=types.ContentTypes.TEXT)
async def add_trader_get_address(message: types.Message, state: FSMContext):
    address = message.text.strip()
    if not address:
        await message.answer("آدرس نمی‌تواند خالی باشد. لطفاً دوباره وارد کنید:")
        return
    await state.update_data(address=address)
    await AddTrader.next()
    await message.answer("اسم مستعار (nickname) تریدر را وارد کنید:")

@dp.message_handler(state=AddTrader.waiting_for_nickname, content_types=types.ContentTypes.TEXT)
async def add_trader_get_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    if not nickname:
        await message.answer("اسم مستعار نمی‌تواند خالی باشد. لطفاً دوباره وارد کنید:")
        return
    await state.update_data(nickname=nickname)
    await AddTrader.next()
    await message.answer("حداقل مقدار هشدار را وارد کنید (مثلاً: 150000):")

@dp.message_handler(state=AddTrader.waiting_for_alert_value, content_types=types.ContentTypes.TEXT)
async def add_trader_get_alert_value(message: types.Message, state: FSMContext):
    alert_value_text = message.text.strip()
    try:
        alert_value = int(alert_value_text)
        if alert_value <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ لطفاً فقط عدد مثبت وارد کنید (مثلاً 150000). دوباره وارد کنید:")
        return

    user_id = str(message.from_user.id)
    username = message.from_user.username or f"user_{user_id}"

    user_data = load_user_data(user_id)
    traders = user_data.get("traders", {})

    state_data = await state.get_data()
    address = state_data.get("address")
    nickname = state_data.get("nickname")

    # چک تکراری بودن آدرس
    if address in traders:
        await message.answer("⚠️ این آدرس قبلاً ثبت شده است.")
        await state.finish()
        return

    # ساختار داده تریدر
    trader_info = {
        "nickname": nickname,
        "alert_value": alert_value,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "username": username,
        "telegram_id": user_id
    }

    traders[address] = trader_info
    user_data["traders"] = traders
    save_user_data(user_id, user_data)

    await message.answer("✅ تریدر با موفقیت ثبت شد.")
    await state.finish()

# =================== لیست تریدرها ===================
@dp.message_handler(lambda msg: msg.text == "📋 لیست تریدرها")
async def cmd_list_traders(message: types.Message):
    user_id = str(message.from_user.id)
    user_data = load_user_data(user_id)
    traders = user_data.get("traders", {})

    if not traders:
        await message.answer("📭 لیست تریدرها خالی است.")
        return

    text = "📋 لیست تریدرهای شما:\n\n"
    for addr, info in traders.items():
        text += (
            f"🏷️ {info.get('nickname', '---')}\n"
            f"🔗 {addr}\n"
            f"📅 ثبت شده در: {info.get('saved_at', '---')}\n"
            "──────────────\n"
        )

    for chunk in split_text(text):
        await message.answer(chunk)

# =================== حذف تریدر ===================
@dp.message_handler(lambda msg: msg.text == "🗑️ حذف تریدر")
async def cmd_delete_trader_start(message: types.Message, state: FSMContext):
    await state.finish()  # اطمینان از پایان همه حالات قبلی

    user_id = str(message.from_user.id)
    user_data = load_user_data(user_id)
    traders = user_data.get("traders", {})

    if not traders:
        await message.answer("❌ هیچ تریدری ثبت نشده است.")
        return

    text = "کد آدرس تریدر مورد نظر برای حذف را ارسال کنید:\n\n"
    for addr, info in traders.items():
        text += f"🏷️ {info.get('nickname', '---')} → `{addr}`\n"

    await message.answer(text, parse_mode="Markdown")
    await DeleteTrader.waiting_for_delete_address.set()

@dp.message_handler(state=DeleteTrader.waiting_for_delete_address, content_types=types.ContentTypes.TEXT)
async def cmd_delete_trader_execute(message: types.Message, state: FSMContext):
    address = message.text.strip()
    user_id = str(message.from_user.id)

    user_data = load_user_data(user_id)
    traders = user_data.get("traders", {})

    if address not in traders:
        await message.answer("❌ آدرس وارد شده در لیست شما نیست.")
        await state.finish()
        return

    del traders[address]
    user_data["traders"] = traders
    save_user_data(user_id, user_data)

    await message.answer("✅ تریدر با موفقیت حذف شد.")
    await state.finish()

# =================== نمایش پروفایل ===================
@dp.message_handler(lambda msg: msg.text == "📊 پروفایل")
async def cmd_show_profile(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "بدون_نام"

    user_data = load_user_data(user_id)
    traders = user_data.get("traders", {})
    trader_count = len(traders)

    text = (
        f"📊 پروفایل شما:\n\n"
        f"👤 نام کاربری: @{username}\n"
        f"🆔 آیدی عددی: {user_id}\n"
        f"📈 تعداد
    text += f"📈 تعداد تریدرهای ثبت‌شده: {trader_count}\n"

    if trader_count > 0:
        text += "\n📋 لیست تریدرها:\n"
        for addr, info in traders.items():
            text += (
                f"🏷️ {info.get('nickname', '---')} → 🔗 {addr}\n"
                f"   ⚠️ حداقل هشدار: {info.get('alert_value', '---')}\n"
                f"   📅 ثبت شده در: {info.get('saved_at', '---')}\n"
                "──────────────\n"
            )

    await message.answer(text)

# =================== فرمان ادمین: مشاهده داده همه کاربران ===================
@dp.message_handler(commands=['user_data'])
async def cmd_user_data_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ شما دسترسی ندارید.")
        return

    all_files = os.listdir(DATA_DIR)
    if not all_files:
        await message.answer("هیچ داده‌ای ثبت نشده است.")
        return

    text = "📂 داده‌های کاربران ثبت شده:\n\n"
    for filename in all_files:
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                user_id = filename.replace(".json", "")
                username = data.get("username", "ندارد")
                traders = data.get("traders", {})
                text += f"👤 آیدی کاربر: {user_id}\n"
                text += f"🔗 نام کاربری: @{username}\n"
                if not traders:
                    text += "• تریدری ثبت نشده است.\n"
                else:
                    for addr, info in traders.items():
                        text += f"• {info.get('nickname', '---')} → {addr}\n"
                text += "──────────────\n"
            except Exception as e:
                text += f"خطا در خواندن فایل {filename}: {e}\n"

    for chunk in split_text(text):
        await message.answer(chunk)

# =================== پیغام خطای پیش‌فرض برای متن‌های ناخواسته ===================
@dp.message_handler()
async def default_message_handler(message: types.Message):
    await message.answer(
        "❓ لطفاً از منوی زیر گزینه‌ای انتخاب کنید یا دستورات معتبر را ارسال کنید.",
        reply_markup=main_menu
    )

# =================== جلوگیری از تبلیغات و اسپم ===================
# این ربات به صورت پایه طراحی شده و تبلیغات اضافه ندارد.
# اگر ربات شما تبلیغات می‌دهد، احتمالاً ناشی از کتابخانه‌های جانبی یا ربات‌های واسط است.
# در این کد تبلیغ یا پیام غیرمرتبطی ارسال نمی‌شود.

# =================== اجرای ربات ===================
if __name__ == "__main__":
    print("ربات با موفقیت اجرا شد...")
    executor.start_polling(dp,  skip_updates=True)
