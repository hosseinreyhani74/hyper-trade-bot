import os
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

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

def save_data(data):
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

    data = load_data()
    if user_id not in data:
        data[user_id] = {
            "traders": {},
            "alert_value": 100000,
            "username": username
        }

    is_bot = 'bot' in nickname.lower() or 'bot' in address.lower()
    data[user_id]["traders"][address] = {
        "nickname": nickname,
        "is_bot": is_bot,
        "added_by": user_id,
        "alert_value": alert_value
    }

    save_data(data)
    await state.finish()
    await message.answer("✅ تریدر با موفقیت ذخیره شد.")

# ========== لیست تریدرها ==========
@dp.message_handler(lambda msg: msg.text == "📋 لیست تریدرها")
async def list_traders(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data or not data[user_id]["traders"]:
        await message.answer("⛔ لیست شما خالی است.")
        return

    msg_text = "📋 لیست تریدرهای شما:\n\n"
    for address, info in data[user_id]["traders"].items():
        nickname = info.get("nickname", "نامشخص")
        alert = info.get("alert_value", "نامشخص")
        msg_text += f"🔹 {nickname}\n"
        msg_text += f"📍 آدرس: `{address}`\n"
        msg_text += f"💰 هشدار از: ${alert}\n\n"

    await message.answer(msg_text, parse_mode="Markdown")

# ========== حذف تریدر ==========
@dp.message_handler(lambda msg: msg.text == "🗑️ حذف تریدر")
async def delete_trader_prompt(message: types.Message):
    user_id = str(message.from_user.id)
    data = ensure_user_data(load_data(), user_id, message.from_user.username)

    if not data[user_id]["traders"]:
        await message.answer("❌ هیچ تریدری ثبت نشده.")
        return

    msg_text = "\n".join([f"{info['nickname']} → {addr}" for addr, info in data[user_id]["traders"].items()])
    await DeleteTrader.waiting_for_delete_address.set()
    await message.answer(f"کد آدرس تریدر مورد نظر برای حذف رو بفرست:\n{msg_text}")

@dp.message_handler(state=DeleteTrader.waiting_for_delete_address, content_types=types.ContentTypes.TEXT)
async def delete_trader_execute(message: types.Message, state: FSMContext):
    address = message.text.strip()
    user_id = str(message.from_user.id)
    data = load_data()

    if address in data.get(user_id, {}).get("traders", {}):
        del data[user_id]["traders"][address]
        save_data(data)
        await message.answer("✅ تریدر حذف شد.")
    else:
        await message.answer("❌ این تریدر وجود نداره.")
    await state.finish()

# ========== پروفایل ==========
@dp.message_handler(lambda msg: msg.text == "📊 پروفایل")
async def profile_handler(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()
    data = ensure_user_data(data, user_id, message.from_user.username)

    traders = data[user_id]["traders"]
    total = len(traders)
    bots = sum(1 for t in traders.values() if isinstance(t, dict) and t.get("is_bot"))
    real = total - bots
    alert = data[user_id].get("alert_value", 100000)

    await message.answer(
        f"📊 پروفایل:\n"
        f"• تعداد کل تریدرها: {total}\n"
        f"• واقعی: {real}\n"
        f"• ربات: {bots}\n"
        f"• هشدار از مبلغ: {alert} دلار"
    )

# ========== اجرای ربات ==========
if __name__ == "__main__":
    print("ربات اجرا شد...")
    executor.start_polling(dp, skip_updates=True)
