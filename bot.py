import json
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

API_TOKEN = '7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ'

# پوشه برای ذخیره داده‌ها
data_folder = 'data'
os.makedirs(data_folder, exist_ok=True)
user_data_path = os.path.join(data_folder, 'users.json')

# اگر فایل وجود نداره، یه فایل خالی بساز
if not os.path.exists(user_data_path):
    with open(user_data_path, 'w', encoding='utf-8') as f:
        json.dump({}, f)

# بارگذاری یا ذخیره داده‌ها
def load_data():
    with open(user_data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(user_data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ساختار ربات
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# کیبورد منو
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add("➕ افزودن تریدر", "🗑️ حذف تریدر")
main_menu.add("📋 لیست تریدرها", "📊 پروفایل")

# وضعیت کاربران برای فاز بعدی
user_states = {}

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer("سلام! به ربات خوش اومدی. گزینه‌ای رو از منو انتخاب کن:", reply_markup=main_menu)

@dp.message_handler(lambda msg: msg.text == "➕ افزودن تریدر")
async def add_trader_step1(message: types.Message):
    user_states[message.from_user.id] = {'step': 'get_address'}
    await message.answer("آیدی تریدر رو بفرست:")

@dp.message_handler(lambda msg: msg.text == "🗑️ حذف تریدر")
async def delete_trader(message: types.Message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data or not data[user_id]['traders']:
        await message.answer("شما هیچ تریدری ثبت نکردی.")
        return
    user_states[user_id] = {'step': 'delete'}
    trader_list = "\n".join([f"{t['nickname']} ({addr})" for addr, t in data[user_id]['traders'].items()])
    await message.answer(f"کدوم آدرس تریدر رو میخوای حذف کنی؟\n{trader_list}")

@dp.message_handler(lambda msg: msg.text == "📋 لیست تریدرها")
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

@dp.message_handler(lambda msg: msg.text == "📊 پروفایل")
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
        f"📊 پروفایل شما:\n"
        f"• تعداد تریدرها: {total}\n"
        f"• تریدر واقعی: {real}\n"
        f"• ربات‌ها: {bots}\n"
        f"• هشدار از مبلغ: {alert} دلار به بالا"
    )

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
            # تشخیص ساده ربات بودن (مثلاً اگر اسم شامل bot بود)
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
import json
from aiogram.types import ParseMode

ADMIN_ID = hosseinreyhani74  # 👈 اینجا آیدی عددی خودتو بذار

@dp.message_handler(commands=['admin_data'])
async def send_all_users_data(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ فقط مدیر به این دستور دسترسی داره.")
        return

    try:
        with open("data/users.json", "r") as file:
            data = json.load(file)
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        if len(formatted) > 4000:
            await message.answer("📄 فایل اطلاعات خیلی بزرگه. لطفاً از طریق هاست ببینش.")
        else:
            await message.answer(f"<pre>{formatted}</pre>", parse_mode=ParseMode.HTML)
    except FileNotFoundError:
        await message.answer("⚠️ فایل اطلاعات پیدا نشد.")
