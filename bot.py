import json
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

API_TOKEN = '7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ'

# تنظیمات ادمین
ADMIN_USERNAME = 'hosseinreyhani74'

# پوشه ذخیره‌سازی دیتا
DATA_FOLDER = 'data'
USER_DATA_PATH = os.path.join(DATA_FOLDER, 'users.json')

os.makedirs(DATA_FOLDER, exist_ok=True)

if not os.path.exists(USER_DATA_PATH):
    with open(USER_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump({}, f)

# بارگذاری و ذخیره‌سازی داده‌ها
def load_data():
    with open(USER_DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(USER_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add("\u2795 افزودن تریدر", "\ud83d\uddd1\ufe0f حذف تریدر")
main_menu.add("\ud83d\udccb لیست تریدرها", "\ud83d\udcca پروفایل")

user_states = {}

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer("سلام! به ربات خوش اومدی. گزینه‌ای رو از منو انتخاب کن:", reply_markup=main_menu)

@dp.message_handler(lambda msg: msg.text == "\u2795 افزودن تریدر")
async def add_trader_step1(message: types.Message):
    user_states[message.from_user.id] = {'step': 'get_address'}
    await message.answer("آیدی تریدر رو بفرست:")

@dp.message_handler(lambda msg: msg.text == "\ud83d\uddd1\ufe0f حذف تریدر")
async def delete_trader(message: types.Message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data or not data[user_id]['traders']:
        await message.answer("شما هیچ تریدری ثبت نکردی.")
        return
    user_states[message.from_user.id] = {'step': 'delete'}
    trader_list = "\n".join([f"{t['nickname']} ({addr})" for addr, t in data[user_id]['traders'].items()])
    await message.answer(f"کدوم آدرس تریدر رو میخوای حذف کنی؟\n{trader_list}")

@dp.message_handler(lambda msg: msg.text == "\ud83d\udccb لیست تریدرها")
async def list_traders(message: types.Message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data or not data[user_id]['traders']:
        await message.answer("هیچ تریدری ثبت نشده.")
        return
    msg_text = "لیست تریدرهای شما:\n"
    for addr, info in data[user_id]['traders'].items():
        msg_text += f"• {info['nickname']} → {addr}\n"
    await message.answer(msg_text)

@dp.message_handler(lambda msg: msg.text == "\ud83d\udcca پروفایل")
async def profile(message: types.Message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data:
        await message.answer("شما هنوز هیچ اطلاعاتی ثبت نکردی.")
        return
    traders = data[user_id]['traders']
    total = len(traders)
    bots = sum(1 for t in traders.values() if t.get('is_bot', False))
    real = total - bots
    alert = data[user_id].get('alert_value', 'مشخص نشده')
    await message.answer(
        f"\ud83d\udcca پروفایل شما:\n"
        f"• تعداد تریدرها: {total}\n"
        f"• تریدر واقعی: {real}\n"
        f"• ربات‌ها: {bots}\n"
        f"• هشدار از مبلغ: {alert} دلار به بالا"
    )

@dp.message_handler(commands=['admin'])
async def show_all_users(message: types.Message):
    if message.from_user.username != ADMIN_USERNAME:
        await message.answer("شما اجازه دسترسی به این بخش رو ندارید.")
        return

    data = load_data()
    if not data:
        await message.answer("هیچ کاربری ثبت نشده.")
        return

    result = "لیست تمام کاربران:\n"
    for uid, info in data.items():
        result += f"\n👤 User ID: {uid}\n"
        for addr, t in info['traders'].items():
            result += f"• {t['nickname']} → {addr}\n"
    await message.answer(result or "اطلاعاتی یافت نشد.")

@dp.message_handler()
async def all_messages_handler(message: types.Message):
    user_id = str(message.from_user.id)
    state = user_states.get(message.from_user.id)
    data = load_data()
    if user_id not in data:
        data[user_id] = {'traders': {}, 'alert_value': 100000}  # مقدار پیش‌فرض هشدار

    if state:
        if state['step'] == 'get_address':
            address = message.text.strip()
            user_states[message.from_user.id] = {'step': 'get_nickname', 'address': address}
            await message.answer("اسم مستعار تریدر رو بنویس:")

        elif state['step'] == 'get_nickname':
            address = state['address']
            nickname = message.text.strip()
            is_bot = 'bot' in nickname.lower() or 'bot' in address.lower()
            data[user_id]['traders'][address] = {'nickname': nickname, 'is_bot': is_bot}
            save_data(data)
            user_states.pop(message.from_user.id)
            await message.answer("✅ تریدر ذخیره شد.")

        elif state['step'] == 'delete':
            address = message.text.strip()
            if address in data[user_id]['traders']:
                del data[user_id]['traders'][address]
                save_data(data)
                user_states.pop(message.from_user.id)
                await message.answer("✅ با موفقیت حذف شد.")
            else:
                await message.answer("❌ آدرس پیدا نشد.")
    else:
        await message.answer("لطفاً یکی از گزینه‌ها رو از منو انتخاب کن.")

if __name__ == '__main__':
    print("ربات در حال اجراست...")
    executor.start_polling(dp, skip_updates=True)
