from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message

API_TOKEN = '7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# دیتابیس ساده برای ذخیره تریدرها (حافظه‌ای)
user_traders = {}

# ساخت منوی اصلی
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("➕ افزودن تریدر"), KeyboardButton("📋 لیست تریدرها")],
        [KeyboardButton("🗑 حذف تریدر"), KeyboardButton("📊 پروفایل من")],
        [KeyboardButton("❓ راهنما")]
    ],
    resize_keyboard=True
)

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.reply("سلام! به ربات خوش اومدی 😊\nچه کاری برات انجام بدم؟", reply_markup=main_menu)

@dp.message_handler(lambda msg: msg.text == "➕ افزودن تریدر")
async def add_trader(message: Message):
    await message.reply("📥 لطفاً آدرس تریدر رو بفرست:")

@dp.message_handler(lambda message: message.reply_to_message and "آدرس تریدر" in message.reply_to_message.text)
async def get_address(msg: Message):
    address = msg.text.strip()

    if not address:
        await msg.answer("❌ آدرس تریدر نباید خالی باشه.")
        return

    user_traders[msg.from_user.id] = user_traders.get(msg.from_user.id, {})
    user_traders[msg.from_user.id]['pending_address'] = address
    await msg.answer("📝 حالا اسم مستعار برای این تریدر رو بفرست:")

@dp.message_handler(lambda message: message.reply_to_message and "اسم مستعار" in message.reply_to_message.text)
async def get_nickname(msg: Message):
    nickname = msg.text.strip()
    data = user_traders.get(msg.from_user.id, {})

    address = data.pop('pending_address', None)
    if not address:
        await msg.answer("⚠️ لطفاً ابتدا آدرس تریدر رو ارسال کن.")
        return

    data[nickname] = address
    user_traders[msg.from_user.id] = data
    await msg.answer(f"✅ تریدر ذخیره شد:\n• {nickname} → `{address}`", parse_mode="Markdown")

@dp.message_handler(lambda msg: msg.text == "📋 لیست تریدرها")
async def list_traders(message: Message):
    data = user_traders.get(message.from_user.id, {})
    traders = {k: v for k, v in data.items() if k != 'pending_address'}

    if not traders:
        await message.reply("⛔️ تریدری ثبت نشده.")
        return

    text = "📄 لیست تریدرهای شما:\n\n"
    for name, address in traders.items():
        text += f"• *{name}*: `{address}`\n"
    await message.reply(text, parse_mode="Markdown")

@dp.message_handler(lambda msg: msg.text == "🗑 حذف تریدر")
async def delete_trader_prompt(message: Message):
    await message.reply("❌ لطفاً *اسم مستعار* تریدری که میخوای حذف بشه رو بفرست:", parse_mode="Markdown")

@dp.message_handler(lambda message: message.reply_to_message and "اسم مستعار" in message.reply_to_message.text)
async def delete_trader(msg: Message):
    nickname = msg.text.strip()
    data = user_traders.get(msg.from_user.id, {})

    if nickname in data:
        del data[nickname]
        await msg.answer(f"🗑 تریدر '{nickname}' با موفقیت حذف شد.")
    else:
        await msg.answer("❌ تریدری با این اسم پیدا نشد.")

@dp.message_handler(lambda msg: msg.text == "📊 پروفایل من")
async def profile(message: Message):
    data = user_traders.get(message.from_user.id, {})
    total = len([k for k in data if k != 'pending_address'])
    await message.reply(f"👤 پروفایل شما:\n• تعداد تریدر ثبت‌شده: {total}")

@dp.message_handler(lambda msg: msg.text == "❓ راهنما")
async def help_msg(message: Message):
    await message.reply(
        "📖 راهنمای ربات:\n"
        "➕ افزودن تریدر: ثبت تریدر جدید\n"
        "📋 لیست تریدرها: نمایش همه تریدرها\n"
        "🗑 حذف تریدر: حذف یکی از تریدرها\n"
        "📊 پروفایل من: خلاصه عملکرد شما"
    )

if __name__ == '__main__':
    print("🤖 ربات با موفقیت اجرا شد.")
    executor.start_polling(dp, skip_updates=True)
