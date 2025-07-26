from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import Message

API_TOKEN = '7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ذخیره‌سازی تریدرها برای هر کاربر به صورت دیکشنری
users_data = {}

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.reply("سلام! 👋 به ربات خوش اومدی.\nبا دستور /add می‌تونی تریدر جدید اضافه کنی.")

@dp.message_handler(commands=['add'])
async def ask_trader_info(message: Message):
    await message.reply("آدرس تریدر رو برام بفرست:")

@dp.message_handler(lambda message: message.reply_to_message and message.reply_to_message.text == "آدرس تریدر رو برام بفرست:")
async def get_address(msg: Message):
    address = msg.text.strip()
    users_data[msg.from_user.id] = users_data.get(msg.from_user.id, {})
    users_data[msg.from_user.id]['pending_address'] = address
    await msg.answer("اسم مستعار برای این تریدر چیه؟")

@dp.message_handler(lambda message: message.reply_to_message and message.reply_to_message.text == "اسم مستعار برای این تریدر چیه؟")
async def get_nickname(msg: Message):
    nickname = msg.text.strip()
    address = users_data[msg.from_user.id].pop('pending_address', None)

    if not address:
        await msg.answer("⛔ آدرس تریدر یافت نشد. لطفا دوباره با /add شروع کن.")
        return

    users_data[msg.from_user.id]['traders'] = users_data[msg.from_user.id].get('traders', {})
    users_data[msg.from_user.id]['traders'][nickname] = address
    await msg.answer(f"✅ ذخیره شد:\n{nickname} → {address}")

@dp.message_handler(commands=['list'])
async def list_traders(msg: Message):
    traders = users_data.get(msg.from_user.id, {}).get('traders', {})
    if not traders:
        await msg.answer("📭 هیچ تریدری ثبت نشده.")
        return
    text = "📋 لیست تریدرهای ثبت‌شده:\n"
    for i, (nick, addr) in enumerate(traders.items(), start=1):
        text += f"{i}. {nick} → {addr}\n"
    await msg.answer(text)

@dp.message_handler(commands=['remove'])
async def remove_trader(msg: Message):
    traders = users_data.get(msg.from_user.id, {}).get('traders', {})
    if not traders:
        await msg.answer("❌ هیچ تریدری برای حذف وجود نداره.")
        return
    await msg.answer("✂️ اسم مستعار تریدری که می‌خوای حذف بشه رو بفرست:")

    @dp.message_handler()
    async def confirm_remove(msg: Message):
        nickname = msg.text.strip()
        if nickname in traders:
            del traders[nickname]
            await msg.answer(f"✅ {nickname} حذف شد.")
        else:
            await msg.answer("❌ این اسم مستعار پیدا نشد.")
