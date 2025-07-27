from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging

# توکن رباتت رو همینجا بذار:
API_TOKEN = "7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ"

# تنظیمات پایه
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# دیتابیس ساده برای ذخیره تریدرها
user_traders = {}

# تعریف State‌ها
class AddTrader(StatesGroup):
    waiting_for_address = State()
    waiting_for_nickname = State()

class DeleteTrader(StatesGroup):
    waiting_for_name = State()

# تعریف کیبورد منو
menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(KeyboardButton("➕ افزودن تریدر"))
menu.add(KeyboardButton("📋 لیست تریدرها"), KeyboardButton("🗑 حذف تریدر"))
menu.add(KeyboardButton("📊 پروفایل من"), KeyboardButton("❓ راهنما"))

# استارت
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("سلام! به ربات خوش اومدی 😊", reply_markup=menu)

# افزودن تریدر
@dp.message_handler(lambda msg: msg.text == "➕ افزودن تریدر")
async def add_trader(message: types.Message):
    await message.answer("لطفاً آدرس تریدر رو وارد کن:")
    await AddTrader.waiting_for_address.set()

@dp.message_handler(state=AddTrader.waiting_for_address)
async def trader_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    await message.answer("حالا یه اسم مستعار براش بنویس:")
    await AddTrader.waiting_for_nickname.set()

@dp.message_handler(state=AddTrader.waiting_for_nickname)
async def trader_nickname(message: types.Message, state: FSMContext):
    data = await state.get_data()
    address = data['address']
    nickname = message.text.strip()
    uid = message.from_user.id

    if uid not in user_traders:
        user_traders[uid] = {}
    user_traders[uid][nickname] = address

    await message.answer(f"✅ ذخیره شد:\n{nickname} → `{address}`", parse_mode="Markdown")
    await state.finish()

# لیست تریدرها
@dp.message_handler(lambda msg: msg.text == "📋 لیست تریدرها")
async def list_traders(message: types.Message):
    uid = message.from_user.id
    traders = user_traders.get(uid, {})
    if not traders:
        await message.answer("هیچ تریدری ثبت نشده 😕")
    else:
        txt = "📋 تریدرهای ثبت‌شده:\n"
        for name, addr in traders.items():
            txt += f"• {name}: `{addr}`\n"
        await message.answer(txt, parse_mode="Markdown")

# حذف تریدر
@dp.message_handler(lambda msg: msg.text == "🗑 حذف تریدر")
async def delete_trader(message: types.Message):
    await message.answer("اسم مستعار تریدری که می‌خوای حذف کنی رو بنویس:")
    await DeleteTrader.waiting_for_name.set()

@dp.message_handler(state=DeleteTrader.waiting_for_name)
async def do_delete(message: types.Message, state: FSMContext):
    name = message.text.strip()
    uid = message.from_user.id
    if name in user_traders.get(uid, {}):
        del user_traders[uid][name]
        await message.answer(f"✅ '{name}' با موفقیت حذف شد.")
    else:
        await message.answer("❌ چنین تریدری پیدا نشد.")
    await state.finish()

# پروفایل
@dp.message_handler(lambda msg: msg.text == "📊 پروفایل من")
async def profile(message: types.Message):
    uid = message.from_user.id
    count = len(user_traders.get(uid, {}))
    await message.answer(f"شما {count} تریدر ثبت کردید ✅")

# راهنما
@dp.message_handler(lambda msg: msg.text == "❓ راهنما")
async def help_section(message: types.Message):
    await message.answer(
        "📌 راهنمای استفاده:\n"
        "➕ افزودن تریدر\n"
        "📋 لیست تریدرها\n"
        "🗑 حذف تریدر\n"
        "📊 پروفایل: تعداد تریدرهای ثبت‌شده"
    )

# اجرای ربات
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
