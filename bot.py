from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = '7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ'

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# دیتابیس ساده
user_traders = {}

# منو
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("➕ افزودن تریدر"), KeyboardButton("📋 لیست تریدرها")],
        [KeyboardButton("🗑 حذف تریدر"), KeyboardButton("📊 پروفایل من")],
        [KeyboardButton("❓ راهنما")]
    ],
    resize_keyboard=True
)

# تعریف حالت‌ها
class AddTrader(StatesGroup):
    waiting_for_address = State()
    waiting_for_nickname = State()

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.reply("سلام! به ربات خوش اومدی 😊", reply_markup=main_menu)

@dp.message_handler(lambda msg: msg.text == "➕ افزودن تریدر")
async def ask_for_address(message: types.Message):
    await message.reply("📥 لطفاً آدرس تریدر رو بفرست:")
    await AddTrader.waiting_for_address.set()

@dp.message_handler(state=AddTrader.waiting_for_address)
async def ask_for_nickname(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    await message.reply("📝 حالا اسم مستعار برای این تریدر رو بفرست:")
    await AddTrader.waiting_for_nickname.set()

@dp.message_handler(state=AddTrader.waiting_for_nickname)
async def save_trader(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    address = user_data['address']
    nickname = message.text.strip()

    uid = message.from_user.id
    user_traders[uid] = user_traders.get(uid, {})
    user_traders[uid][nickname] = address

    await message.reply(f"✅ تریدر ذخیره شد:\n• {nickname} → `{address}`", parse_mode="Markdown")
    await state.finish()

@dp.message_handler(lambda msg: msg.text == "📋 لیست تریدرها")
async def list_traders(message: types.Message):
    data = user_traders.get(message.from_user.id, {})
    if not data:
        await message.reply("⛔️ تریدری ثبت نشده.")
        return
    text = "📄 لیست تریدرهای شما:\n\n"
    for name, address in data.items():
        text += f"• *{name}*: `{address}`\n"
    await message.reply(text, parse_mode="Markdown")

@dp.message_handler(lambda msg: msg.text == "🗑 حذف تریدر")
async def delete_trader_prompt(message: types.Message):
    await message.reply("❌ اسم مستعار تریدری که میخوای حذف بشه رو بفرست:")

@dp.message_handler(lambda msg: msg.text in user_traders.get(msg.from_user.id, {}))
async def delete_trader(message: types.Message):
    nickname = message.text.strip()
    data = user_traders.get(message.from_user.id, {})
    if nickname in data:
        del data[nickname]
        await message.reply(f"🗑 تریدر '{nickname}' با موفقیت حذف شد.")
    else:
        await message.reply("❌ تریدری با این اسم پیدا نشد.")

@dp.message_handler(lambda msg: msg.text == "📊 پروفایل من")
async def profile(message: types.Message):
    data = user_traders.get(message.from_user.id, {})
    await message.reply(f"👤 پروفایل شما:\n• تریدر ثبت‌شده: {len(data)}")

@dp.message_handler(lambda msg: msg.text == "❓ راهنما")
async def help_msg(message: types.Message):
    await message.reply(
        "📖 راهنمای ربات:\n"
        "➕ افزودن تریدر: ثبت تریدر جدید\n"
        "📋 لیست تریدرها: نمایش همه تریدرها\n"
        "🗑 حذف تریدر: حذف یکی از تریدرها\n"
        "📊 پروفایل من: خلاصه عملکرد شما"
    )

if __name__ == '__main__':
    print("🤖 ربات اجرا شد")
    executor.start_polling(dp, skip_updates=True)
