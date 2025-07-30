import os
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# ==== پیکربندی ربات ====
API_TOKEN = '7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ'
ADMIN_USERNAME = '@hosseinreyhani74'

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
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

API_TOKEN = '7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ'

# آی‌دی عددی ادمین (@hosseinreyhani74)
ADMIN_ID = 805989529

# مسیر ذخیره‌سازی داده‌ها
data_folder = 'data'
os.makedirs(data_folder, exist_ok=True)
user_data_path = os.path.join(data_folder, 'users.json')

if not os.path.exists(user_data_path):
    with open(user_data_path, 'w', encoding='utf-8') as f:
        json.dump({}, f)

def load_data():
    with open(user_data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(user_data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add("➕ افزودن تریدر", "🗑️ حذف تریدر")
main_menu.add("📋 لیست تریدرها", "📊 پروفایل")

user_states = {}

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer("سلام! یکی از گزینه‌های زیر رو انتخاب کن:", reply_markup=main_menu)

@dp.message_handler(commands=['user_data'])
async def user_data_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ شما دسترسی ندارید.")
        return
    data = load_data()
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
    await message.answer(text or "هیچ داده‌ای ثبت نشده.")

@dp.message_handler(lambda msg: msg.text == "➕ افزودن تریدر")
async def add_trader_step1(message: types.Message):
    user_states[message.from_user.id] = {'step': 'get_address'}
    await message.answer("آدرس تریدر رو ارسال کن:")

@dp.message_handler(lambda msg: msg.text == "🗑️ حذف تریدر")
async def delete_trader(message: types.Message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data or not data[user_id]['traders']:
        await message.answer("❌ تریدری ثبت نشده.")
        return
    user_states[message.from_user.id] = {'step': 'delete'}
    trader_list = "\n".join([f"{t['nickname']} ({addr})" for addr, t in data[user_id]['traders'].items()])
    await message.answer(f"کدام آدرس را می‌خواهی حذف کنی؟\n{trader_list}")

@dp.message_handler(lambda msg: msg.text == "📋 لیست تریدرها")
async def list_traders(message: types.Message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data or not data[user_id]['traders']:
        await message.answer("⛔ لیست شما خالی است.")
        return
    msg_text = "📋 لیست تریدرهای شما:\n"
    for addr, info in data[user_id]['traders'].items():
        msg_text += f"• {info['nickname']} → {addr}\n"
    await message.answer(msg_text)

@dp.message_handler(lambda msg: msg.text == "📊 پروفایل")
async def profile(message: types.Message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data:
        await message.answer("❗ شما هنوز تریدری ثبت نکردید.")
        return
    traders = data[user_id]['traders']
    total = len(traders)
    bots = sum(1 for t in traders.values() if t.get('is_bot', False))
    real = total - bots
    alert = data[user_id].get('alert_value', 'نامشخص')
    await message.answer(
        f"📊 پروفایل:\n"
        f"• مجموع تریدرها: {total}\n"
        f"• واقعی: {real}\n"
        f"• ربات: {bots}\n"
        f"• هشدار از مبلغ: {alert} دلار"
    )

@dp.message_handler()
async def all_messages_handler(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "نداره"
    state = user_states.get(message.from_user.id)
    data = load_data()
    if user_id not in data:
        data[user_id] = {'traders': {}, 'alert_value': 100000, 'username': username}
    else:
        data[user_id]['username'] = username
    if state:
        if state['step'] == 'get_address':
            address = message.text.strip()
            user_states[message.from_user.id] = {'step': 'get_nickname', 'address': address}
            await message.answer("اسم مستعار تریدر رو وارد کن:")
        elif state['step'] == 'get_nickname':
            address = state['address']
            nickname = message.text.strip()
            is_bot = 'bot' in nickname.lower() or 'bot' in address.lower()
            data[user_id]['traders'][address] = {
                'nickname': nickname,
                'is_bot': is_bot,
                'added_by': message.from_user.id
            }
            save_data(data)
            user_states.pop(message.from_user.id)
            await message.answer("✅ تریدر با موفقیت ذخیره شد.")
        elif state['step'] == 'delete':
            address = message.text.strip()
            if address in data[user_id]['traders']:
                del data[user_id]['traders'][address]
                save_data(data)
                user_states.pop(message.from_user.id)
                await message.answer("✅ تریدر حذف شد.")
            else:
                await message.answer("❌ آدرس پیدا نشد.")
    else:
        await message.answer("⚠️ لطفاً یکی از گزینه‌های منو را انتخاب کنید.")

if __name__ == '__main__':
    print("ربات اجرا شد...")
    executor.start_polling(dp, skip_updates=True)
