import os
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# ==== پیکربندی ربات ====
API_TOKEN = '7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ'
ADMIN_USERNAME = 'hosseinreyhani74'

# ====== ساخت مسیر و فایل ======
if not os.path.exists('data'):
    os.makedirs('data')

DATA_FILE = os.path.join('data', 'users.json')

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ====== تعریف کلاس وضعیت‌ها ======
class AddTrader(StatesGroup):
    waiting_for_address = State()
    waiting_for_nickname = State()

class DeleteTrader(StatesGroup):
    waiting_for_address = State()

# ====== راه‌اندازی ربات ======
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ====== شروع ربات ======
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("➕ افزودن تریدر", "📋 لیست تریدرها")
    keyboard.add("🗑️ حذف تریدر", "📊 پروفایل")
    await message.answer("سلام 👋 لطفاً یکی از گزینه‌ها رو انتخاب کن:", reply_markup=keyboard)

# ====== افزودن تریدر ======
@dp.message_handler(lambda msg: msg.text == "➕ افزودن تریدر")
async def handle_add_trader(message: types.Message):
    await AddTrader.waiting_for_address.set()
    await message.answer("آدرس تریدر رو بفرست:")

@dp.message_handler(state=AddTrader.waiting_for_address, content_types=types.ContentTypes.TEXT)
async def process_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    await AddTrader.next()
    await message.answer("اسم مستعار تریدر رو بنویس:")

@dp.message_handler(state=AddTrader.waiting_for_nickname, content_types=types.ContentTypes.TEXT)
async def process_nickname(message: types.Message, state: FSMContext):
    data = await state.get_data()
    address = data['address']
    nickname = message.text.strip()

    user_id = str(message.from_user.id)
    all_data = load_data()
    if user_id not in all_data:
        all_data[user_id] = {'traders': {}, 'alert_value': 100000}

    all_data[user_id]['traders'][address] = nickname
    save_data(all_data)

    await state.finish()
    await message.answer("✅ تریدر ذخیره شد.")

# ====== لیست تریدرها ======
@dp.message_handler(lambda msg: msg.text == "📋 لیست تریدرها")
async def list_traders(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data or not data[user_id]['traders']:
        await message.answer("هیچ تریدری ثبت نشده.")
        return

    msg = "📋 لیست تریدرها:\n"
    for addr, name in data[user_id]['traders'].items():
        msg += f"▪ {name} → {addr}\n"
    await message.answer(msg)

# ====== حذف تریدر ======
@dp.message_handler(lambda msg: msg.text == "🗑️ حذف تریدر")
async def handle_delete_trader(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data or not data[user_id]['traders']:
        await message.answer("هیچ تریدری برای حذف نداری.")
        return

    text = "\n".join([f"{nickname} → {addr}" for addr, nickname in data[user_id]['traders'].items()])
    await DeleteTrader.waiting_for_address.set()
    await message.answer(f"آدرس تریدر مورد نظر برای حذف رو بفرست:\n{text}")

@dp.message_handler(state=DeleteTrader.waiting_for_address, content_types=types.ContentTypes.TEXT)
async def process_delete_trader(message: types.Message, state: FSMContext):
    address = message.text.strip()
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id in data and address in data[user_id]['traders']:
        del data[user_id]['traders'][address]
        save_data(data)
        await message.answer("✅ تریدر با موفقیت حذف شد.")
    else:
        await message.answer("❌ این آدرس توی لیست نیست.")

    await state.finish()

# ====== پروفایل ======
@dp.message_handler(lambda msg: msg.text == "📊 پروفایل")
async def show_profile(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()
    user_data = data.get(user_id, {'traders': {}, 'alert_value': 100000})

    num_traders = len(user_data['traders'])
    alert_value = user_data.get('alert_value', 100000)

    msg = f"📊 پروفایل شما:\n▪ تریدرها: {num_traders}\n▪ هشدار از مبلغ: ${alert_value}"
    await message.answer(msg)
import json
import os
from aiogram import types
from datetime import datetime

# آی‌دی عددی ادمین (بر اساس username داده شده)
ADMIN_IDS = [1184382091]  # hosseinreyhani74

DATA_FILE = "data/users.json"
os.makedirs("data", exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

# ذخیره اطلاعات تریدر کاربر
def save_trader(user_id: int, username: str, trader_name: str):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {"username": username or "ندارد", "traders": [], "saved_at": ""}

    if trader_name not in data[user_id]["traders"]:
        data[user_id]["traders"].append(trader_name)
        data[user_id]["saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

# کاربر: ثبت تریدر با دستور "add ..."
@dp.message_handler(lambda message: message.text.startswith("add "))
async def handle_add_trader(message: types.Message):
    trader_name = message.text.replace("add ", "").strip()
    if not trader_name:
        await message.reply("❗ اسم تریدر نمی‌تونه خالی باشه.")
        return

    save_trader(
        message.from_user.id,
        message.from_user.username,
        trader_name
    )
    await message.reply(f"✅ تریدر '{trader_name}' ذخیره شد.")

# ادمین: نمایش لیست همه کاربران و تریدرها
@dp.message_handler(commands=["users_data"])
async def show_all_users(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ شما دسترسی ندارید.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        await message.reply("هیچ اطلاعاتی ثبت نشده.")
        return

    text = "📋 لیست کاربران و تریدرها:\n\n"
    for user_id, info in data.items():
        text += f"🆔 ID: {user_id}\n"
        text += f"👤 Username: @{info['username']}\n"
        text += f"📌 تریدرها: {', '.join(info['traders'])}\n"
        text += f"🕒 زمان ذخیره: {info['saved_at']}\n\n"

    if len(text) > 4000:
        with open("data/report.txt", "w", encoding="utf-8") as f:
            f.write(text)
        await message.reply_document(types.InputFile("data/report.txt"))
    else:
        await message.reply(text)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
