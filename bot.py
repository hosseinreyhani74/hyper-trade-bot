from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import Message

API_TOKEN = '7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

saved_traders = {}

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.reply("سلام! 👋 به ربات خوش اومدی.\nبرای افزودن تریدر از دستور /add استفاده کن.")

@dp.message_handler(commands=['add'])
async def ask_trader_info(message: Message):
    await message.reply("آدرس تریدر رو برام بفرست:")

@dp.message_handler(lambda message: message.reply_to_message and message.reply_to_message.text == "آدرس تریدر رو برام بفرست:")
async def get_address(msg: Message):
    address = msg.text.strip()
    saved_traders[msg.from_user.id] = {'address': address}
    await msg.answer("اسم مستعار برای این تریدر چیه؟")

@dp.message_handler(lambda message: message.reply_to_message and message.reply_to_message.text == "اسم مستعار برای این تریدر چیه؟")
async def get_nickname(msg: Message):
    nickname = msg.text.strip()
    user_data = saved_traders.get(msg.from_user.id, {})
    address = user_data.get('address', 'آدرس نامشخص')
    saved_traders[address] = nickname
    await msg.answer(f"✅ ذخیره شد:\n{nickname} → {address}")

if __name__ == '__main__':
    print("✅ ربات در حال اجراست...")
    executor.start_polling(dp, skip_updates=True)
