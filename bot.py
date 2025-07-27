from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging

API_TOKEN = "7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

user_traders = {}

class AddTrader(StatesGroup):
    waiting_for_address = State()
    waiting_for_nickname = State()

class DeleteTrader(StatesGroup):
    waiting_for_name = State()

menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(KeyboardButton("➕ افزودن تریدر"))
menu.add(KeyboardButton("📋 لیست تریدرها"), KeyboardButton("🗑 حذف تریدر"))
menu.add(KeyboardButton("📊 پروفایل من"), KeyboardButton("❓ راهنما"))

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("سلام! به ربات خوش اومدی 😊", reply_markup=menu)

@dp.message_handler(lambda msg: msg.text == "➕ افزودن تریدر")
async def add_trader(message: types.Message, state: FSMContext):
    await state.update_data(uid=message.from_user.id)
    await message.answer("آدرس تریدر رو وارد کن:")
    await AddTrader.waiting_for_address.set()

@dp.message_handler(state=AddTrader.waiting_for_address)
async def trader_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    await message.answer("اسم مستعار برای تریدر بنویس:")
    await AddTrader.waiting_for_nickname.set()

@dp.message_handler(state=AddTrader.waiting_for_nickname)
async def trader_nickname(message: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = data['uid']
    address = data['address']
    nickname = message.text.strip()

    # تشخیص رباتی یا واقعی بودن با قاعده ساده (در آینده می‌تونیم بهترش کنیم)
    is_bot = address.lower().startswith("bot_") or address.lower().endswith("_bot")

    if uid not in user_traders:
        user_traders[uid] = {}

    user_traders[uid][nickname] = {
        "address": address,
        "is_bot": is_bot
    }

    msg_bot = "🤖 این تریدر یک ربات شناسایی شد!" if is_bot else "✅ تریدر واقعی ثبت شد!"
    await message.answer(f"{msg_bot}\n{nickname} → `{address}`", parse_mode="Markdown")
    await state.finish()

@dp.message_handler(lambda msg: msg.text == "📋 لیست تریدرها")
async def list_traders(message: types.Message):
    uid = message.from_user.id
    traders = user_traders.get(uid, {})
    if not traders:
        await message.answer("هنوز تریدری ذخیره نشده 😐")
    else:
        txt = "📋 لیست تریدرهای شما:\n"
        for name, info in traders.items():
            bot_tag = "🤖" if info['is_bot'] else "✅"
            txt += f"{bot_tag} {name}: `{info['address']}`\n"
        await message.answer(txt, parse_mode="Markdown")

@dp.message_handler(lambda msg: msg.text == "🗑 حذف تریدر")
async def delete_trader(message: types.Message):
    await message.answer("اسم مستعار تریدری که می‌خوای حذف کنی رو بنویس:")
    await DeleteTrader.waiting_for_name.set()

@dp.message_handler(state=DeleteTrader.waiting_for_name)
async def do_delete(message: types.Message, state: FSMContext):
    name = message.text.strip()
    uid = message.from_user.id
    if uid in user_traders and name in user_traders[uid]:
        del user_traders[uid][name]
        await message.answer(f"✅ تریدر '{name}' با موفقیت حذف شد.")
    else:
        await message.answer("❌ تریدری با این نام پیدا نشد.")
    await state.finish()

@dp.message_handler(lambda msg: msg.text == "📊 پروفایل من")
async def profile(message: types.Message):
    uid = message.from_user.id
    traders = user_traders.get(uid, {})
    total = len(traders)
    bots = sum(1 for t in traders.values() if t["is_bot"])
    real = total - bots
    await message.answer(
        f"👤 پروفایل شما:\n"
        f"📌 مجموع تریدرها: {total}\n"
        f"🤖 ربات‌ها: {bots}\n"
        f"✅ تریدرهای واقعی: {real}"
    )

@dp.message_handler(lambda msg: msg.text == "❓ راهنما")
async def help_section(message: types.Message):
    await message.answer(
        "📌 راهنمای دستورات:\n"
        "➕ افزودن تریدر\n"
        "📋 لیست تریدرها\n"
        "🗑 حذف تریدر\n"
        "📊 پروفایل برای دیدن آمار کلی"
    )

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
