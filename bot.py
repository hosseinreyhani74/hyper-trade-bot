import os
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup

API_TOKEN = "7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ"
ADMIN_USERNAME = "hosseinreyhani74"

# مسیر فایل ذخیره‌سازی
DATA_FOLDER = "data"
DATA_FILE = os.path.join(DATA_FOLDER, "users.json")
os.makedirs(DATA_FOLDER, exist_ok=True)

# اگر فایل وجود نداره بساز
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# شروع aiogram
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
user_states = {}

# منو
menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add("➕ افزودن تریدر", "🗑 حذف تریدر")
menu.add("📋 لیست تریدرها", "📊 پروفایل")

@dp.message_handler(commands=["start"])
async def start_handler(msg: types.Message):
    user_states.pop(msg.from_user.id, None)
    await msg.answer("سلام! یکی از گزینه‌های زیر رو انتخاب کن 👇", reply_markup=menu)

@dp.message_handler(lambda m: m.text == "➕ افزودن تریدر")
async def add_trader_step1(msg: types.Message):
    user_states[msg.from_user.id] = {"step": "get_address"}
    await msg.answer("لطفاً آدرس تریدر رو بفرست:")

@dp.message_handler(lambda m: m.text == "🗑 حذف تریدر")
async def delete_trader_step(msg: types.Message):
    user_id = str(msg.from_user.id)
    data = load_data()
    if user_id not in data or not data[user_id]["traders"]:
        await msg.answer("شما هیچ تریدری ثبت نکردی.")
        return
    user_states[msg.from_user.id] = {"step": "delete"}
    traders = data[user_id]["traders"]
    list_txt = "\n".join([f"{t['nickname']} → {addr}" for addr, t in traders.items()])
    await msg.answer(f"کدوم آدرس رو حذف کنم؟ 👇\n{list_txt}")

@dp.message_handler(lambda m: m.text == "📋 لیست تریدرها")
async def list_traders(msg: types.Message):
    user_id = str(msg.from_user.id)
    data = load_data()
    if user_id not in data or not data[user_id]["traders"]:
        await msg.answer("لیست تریدرها خالیه.")
        return
    txt = "📋 لیست تریدرها:\n"
    for addr, t in data[user_id]["traders"].items():
        txt += f"• {t['nickname']} → {addr}\n"
    await msg.answer(txt)

@dp.message_handler(lambda m: m.text == "📊 پروفایل")
async def show_profile(msg: types.Message):
    user_id = str(msg.from_user.id)
    data = load_data()
    if user_id not in data:
        await msg.answer("هنوز اطلاعاتی ثبت نکردی.")
        return
    traders = data[user_id]["traders"]
    total = len(traders)
    bots = sum(1 for t in traders.values() if t["is_bot"])
    real = total - bots
    alert = data[user_id].get("alert_value", "مشخص نشده")
    await msg.answer(
        f"📊 پروفایل شما:\n"
        f"• کل تریدرها: {total}\n"
        f"• تریدر واقعی: {real}\n"
        f"• ربات: {bots}\n"
        f"• هشدار از مبلغ: {alert}$"
    )

@dp.message_handler(commands=["admin"])
async def admin_view(msg: types.Message):
    if msg.from_user.username != ADMIN_USERNAME:
        await msg.answer("❌ شما دسترسی ادمین ندارید.")
        return
    data = load_data()
    txt = "📦 اطلاعات تمام کاربران:\n"
    for uid, info in data.items():
        txt += f"\n👤 کاربر {uid}:\n"
        for addr, t in info["traders"].items():
            txt += f"• {t['nickname']} → {addr}\n"
    await msg.answer(txt or "هیچ داده‌ای موجود نیست.")

@dp.message_handler()
async def all_messages_handler(msg: types.Message):
    user_id = str(msg.from_user.id)
    state = user_states.get(msg.from_user.id)
    data = load_data()
    if user_id not in data:
        data[user_id] = {"traders": {}, "alert_value": 100000}

    if state:
        if state["step"] == "get_address":
            address = msg.text.strip()
            user_states[msg.from_user.id] = {"step": "get_nickname", "address": address}
            await msg.answer("اسم مستعار تریدر رو وارد کن:")
        elif state["step"] == "get_nickname":
            address = state["address"]
            nickname = msg.text.strip()
            is_bot = "bot" in nickname.lower() or "bot" in address.lower()
            data[user_id]["traders"][address] = {"nickname": nickname, "is_bot": is_bot}
            save_data(data)
            user_states.pop(msg.from_user.id)
            await msg.answer("✅ تریدر با موفقیت ذخیره شد.")
        elif state["step"] == "delete":
            address = msg.text.strip()
            if address in data[user_id]["traders"]:
                del data[user_id]["traders"][address]
                save_data(data)
                user_states.pop(msg.from_user.id)
                await msg.answer("✅ با موفقیت حذف شد.")
            else:
                await msg.answer("❌ آدرس پیدا نشد.")
    else:
        await msg.answer("لطفاً یکی از گزینه‌های منو را انتخاب کن.", reply_markup=menu)

if __name__ == "__main__":
    print("ربات در حال اجراست...")
    executor.start_polling(dp, skip_updates=True)
