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

# ساختار اطلاعات کاربران
user_traders = {}

class AddTrader(StatesGroup):
    waiting_for_address = State()
    waiting_for_nickname = State()

class DeleteTrader(StatesGroup):
    waiting_for_name = State()

# منو اصلی
menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(KeyboardButton("➕ افزودن تریدر"))
menu.add(KeyboardButton("📋 لیست تریدرها"), KeyboardButton("🗑 حذف تریدر"))
menu.add(KeyboardButton("📊 پروفایل من"), KeyboardButton("❓ راهنما"))

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("سلام! به ربات خوش اومدی 😊", reply_markup=menu)

# افزودن تریدر
@dp.message_handler(lambda msg: msg.text == "➕ افزودن تریدر")
async def add_trader(message: types.Message, state: FSMContext):
    await state.update_data(uid=message.from_user.id)
    await message.answer("📥 لطفاً آدرس تریدر رو وارد کن:")
    await AddTrader.waiting_for_address.set()

@dp.message_handler(state=AddTrader.waiting_for_address)
async def trader_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    await message.answer("📝 حالا یه اسم مستعار برای این تریدر بنویس:")
    await AddTrader.waiting_for_nickname.set()

@dp.message_handler(state=AddTrader.waiting_for_nickname)
async def trader_nickname(message: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = message.from_user.id
    address = data['address']
    nickname = message.text.strip()

    # تشخیص ساده برای ربات بودن
    is_bot = address.lower().startswith("bot_") or address.lower().endswith("_bot")

    if uid not in user_traders:
        user_traders[uid] = {}

    user_traders[uid][nickname] = {
        "address": address,
        "is_bot": is_bot
    }

    msg_bot = "🤖 این تریدر یک ربات تشخیص داده شد!" if is_bot else "✅ تریدر واقعی ذخیره شد."
    await message.answer(f"{msg_bot}\n\n{nickname} → `{address}`", parse_mode="Markdown")
    await state.finish()

# لیست تریدرها
@dp.message_handler(lambda msg: msg.text == "📋 لیست تریدرها")
async def list_traders(message: types.Message):
    uid = message.from_user.id
    traders = user_traders.get(uid, {})
    if not traders:
        await message.answer("⛔ هنوز تریدری ذخیره نکردی.")
    else:
        txt = "📋 لیست تریدرهای ذخیره‌شده:\n\n"
        for name, info in traders.items():
            bot_icon = "🤖" if info['is_bot'] else "✅"
            txt += f"{bot_icon} {name}: `{info['address']}`\n"
        await message.answer(txt, parse_mode="Markdown")

# حذف تریدر
@dp.message_handler(lambda msg: msg.text == "🗑 حذف تریدر")
async def delete_trader(message: types.Message):
    await message.answer("🗑 اسم مستعار تریدری که می‌خوای حذف کنی رو بفرست:")
    await DeleteTrader.waiting_for_name.set()

@dp.message_handler(state=DeleteTrader.waiting_for_name)
async def do_delete(message: types.Message, state: FSMContext):
    name = message.text.strip()
    uid = message.from_user.id
    if uid in user_traders and name in user_traders[uid]:
        del user_traders[uid][name]
        await message.answer(f"✅ تریدر «{name}» حذف شد.")
    else:
        await message.answer("⚠️ چنین تریدری پیدا نشد.")
    await state.finish()

# پروفایل دقیق
@dp.message_handler(lambda msg: msg.text == "📊 پروفایل من")
async def profile(message: types.Message):
    uid = message.from_user.id
    traders = user_traders.get(uid, {})
    total = len(traders)
    bots = sum(1 for t in traders.values() if t.get("is_bot"))
    real = total - bots
    await message.answer(
        f"👤 پروفایل شما:\n\n"
        f"🔢 تعداد تریدرها: {total}\n"
        f"🤖 ربات‌ها: {bots}\n"
        f"✅ تریدرهای واقعی: {real}"
    )

# راهنما
@dp.message_handler(lambda msg: msg.text == "❓ راهنما")
async def help_section(message: types.Message):
    await message.answer(
        "📌 راهنمای استفاده از ربات:\n"
        "➕ افزودن تریدر\n"
        "📋 لیست تریدرها\n"
        "🗑 حذف تریدر\n"
        "📊 پروفایل من\n"
        "❓ راهنما برای توضیحات"
    )

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
