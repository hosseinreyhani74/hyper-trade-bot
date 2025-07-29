import json
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

API_TOKEN = '7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ'

# مسیر و ایجاد پوشه و فایل داده‌ها
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

# کیبورد اصلی
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add("➕ افزودن تریدر", "🗑️ حذف تریدر")
main_menu.add("📋 لیست تریدرها", "📊 پروفایل")

# ذخیره وضعیت کاربران
user_states = {}

@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    await message.answer("سلام! یکی از گزینه‌های زیر رو انتخاب کن:", reply_markup=main_menu)

@dp.message_handler(lambda msg: msg.text == "➕ افزودن تریدر")
async def handle_add_trader(message: types.Message):
    user_states[message.from_user.id] = {'step': 'get_address'}
    await message.answer("آدرس تریدر رو بفرست:")

@dp.message_handler(lambda msg: msg.text == "🗑️ حذف تریدر")
async def handle_delete_trader(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id not in data or not data[user_id]['traders']:
        await message.answer("تریدر ثبت‌نشده‌ای ندارید.")
        return

    trader_list = "\n".join([f"{nickname} → {addr}" for addr, nickname in data[user_id]['traders'].items()])
    user_states[message.from_user.id] = {'step': 'delete'}
    await message.answer(f"کدوم آدرس رو می‌خوای حذف کنی؟\n{trader_list}")

@dp.message_handler(lambda msg: msg.text == "📋 لیست تریدرها")
async def handle_list(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id not in data or not data[user_id]['traders']:
        await message.answer("هیچ تریدری ثبت نشده.")
        return

    trader_list = "\n".join([f"• {nickname} → {addr}" for addr, nickname in data[user_id]['traders'].items()])
    await message.answer(f"📋 لیست تریدرها:\n{trader_list}")

@dp.message_handler(lambda msg: msg.text == "📊 پروفایل")
async def handle_profile(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id not in data or not data[user_id]['traders']:
        await message.answer("پروفایلت خالیه. هنوز تریدری ثبت نکردی.")
        return

    total = len(data[user_id]['traders'])
    bots = sum(1 for addr in data[user_id]['traders'] if 'bot' in addr.lower())
    real = total - bots
    alert = data[user_id].get('alert_value', 100000)

    await message.answer(
        f"📊 پروفایل شما:\n"
        f"• کل تریدرها: {total}\n"
        f"• تریدر واقعی: {real}\n"
        f"• ربات: {bots}\n"
        f"• هشدار از مبلغ: {alert}$"
    )

@dp.message_handler()
async def handle_all_messages(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id not in data:
        data[user_id] = {'traders': {}, 'alert_value': 100000}

    state = user_states.get(message.from_user.id)
    if state:
        if state['step'] == 'get_address':
            address = message.text.strip()
            if address in data[user_id]['traders']:
                await message.answer("این آدرس قبلاً ثبت شده.")
                return
            user_states[message.from_user.id] = {'step': 'get_nickname', 'address': address}
            await message.answer("اسم مستعار تریدر رو بنویس:")

        elif state['step'] == 'get_nickname':
            nickname = message.text.strip()
            address = state['address']
            data[user_id]['traders'][address] = nickname
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
                await message.answer("❌ این آدرس توی لیست نیست.")

    else:
        await message.answer("لطفاً یکی از گزینه‌ها رو از منو انتخاب کن.")

if __name__ == '__main__':
    print("ربات اجرا شد.")
    executor.start_polling(dp, skip_updates=True)
