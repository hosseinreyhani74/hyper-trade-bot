import os
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

API_TOKEN = "توکن_ربات_تو_اینجا_قرار_بده"  # حتما توکن خودت رو جایگزین کن
ADMIN_ID = 805989529  # آیدی تلگرام خودت

# پوشه ذخیره داده‌ها
BACKUP_FOLDER = "backup"
os.makedirs(BACKUP_FOLDER, exist_ok=True)

# توابع کمکی برای مدیریت فایل‌ها

def sanitize_filename(text):
    return "".join(c for c in text if c.isalnum() or c in ("_", "-"))

def get_user_filepath(user_id, username):
    safe_username = sanitize_filename(username or "بدون_نام")
    return os.path.join(BACKUP_FOLDER, f"{user_id}_{safe_username}.json")

def load_user_data(user_id, username):
    path = get_user_filepath(user_id, username)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"traders": {}}
    else:
        return {"traders": {}}

def save_user_data(user_id, username, data):
    path = get_user_filepath(user_id, username)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def split_text(text, max_length=4000):
    parts = []
    while len(text) > max_length:
        split_pos = text.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        parts.append(text[:split_pos])
        text = text[split_pos:]
    parts.append(text)
    return parts

# تعریف حالات FSM برای افزودن و حذف تریدر

class TraderStates(StatesGroup):
    waiting_for_address = State()
    waiting_for_nickname = State()
    waiting_for_delete_index = State()

# راه اندازی ربات و دیسپچر

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# کیبورد اصلی
main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add("📊 پروفایل", "➕ افزودن تریدر")
main_keyboard.add("🗑️ حذف تریدر", "📋 لیست تریدرها")

# هندلر شروع کاربر
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer(
        "سلام! خوش آمدید.\n"
        "لطفا یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=main_keyboard
    )

# پروفایل کاربر
@dp.message_handler(lambda m: m.text == "📊 پروفایل")
async def show_profile(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "بدون_نام"
    data = load_user_data(user_id, username)
    traders = data.get("traders", {})
    count = len(traders)

    text = (
        f"📊 پروفایل شما:\n\n"
        f"👤 نام کاربری: @{username}\n"
        f"🆔 آیدی عددی: {user_id}\n"
        f"📈 تعداد تریدرهای ثبت‌شده: {count}\n"
    )

    if count > 0:
        text += "\n📋 لیست تریدرها:\n"
        for addr, info in traders.items():
            text += f"🏷️ {info['nickname']} → 🔗 {addr}\n"

    await message.answer(text, reply_markup=main_keyboard)

# لیست تریدرها
@dp.message_handler(lambda m: m.text == "📋 لیست تریدرها")
async def list_traders(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "بدون_نام"
    data = load_user_data(user_id, username)
    traders = data.get("traders", {})

    if not traders:
        await message.answer("شما هیچ تریدری ثبت نکرده‌اید.", reply_markup=main_keyboard)
        return

    text = "📋 لیست تریدرهای شما:\n\n"
    for addr, info in traders.items():
        text += f"🏷️ {info['nickname']} → 🔗 {addr}\n"

    await message.answer(text, reply_markup=main_keyboard)

# افزودن تریدر - مرحله 1 آدرس
@dp.message_handler(lambda m: m.text == "➕ افزودن تریدر")
async def add_trader_start(message: types.Message):
    await message.answer("لطفاً آدرس تریدر را ارسال کنید:", reply_markup=types.ReplyKeyboardRemove())
    await TraderStates.waiting_for_address.set()

# افزودن تریدر - مرحله 2 نام مستعار
@dp.message_handler(state=TraderStates.waiting_for_address)
async def add_trader_get_address(message: types.Message, state: FSMContext):
    address = message.text.strip()
    if not address:
        await message.answer("آدرس نامعتبر است، لطفا مجددا ارسال کنید.")
        return
    await state.update_data(address=address)
    await message.answer("حالا نام مستعار (nickname) تریدر را ارسال کنید:")
    await TraderStates.waiting_for_nickname.set()

@dp.message_handler(state=TraderStates.waiting_for_nickname)
async def add_trader_get_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    if not nickname:
        await message.answer("نام مستعار نمی‌تواند خالی باشد، لطفا مجددا ارسال کنید.")
        return
    user_id = str(message.from_user.id)
    username = message.from_user.username or "بدون_نام"

    data = load_user_data(user_id, username)
    user_data = await state.get_data()
    address = user_data.get("address")

    if "traders" not in data:
        data["traders"] = {}

    # جلوگیری از ثبت آدرس تکراری
    if address in data["traders"]:
        await message.answer("این آدرس قبلا ثبت شده است.", reply_markup=main_keyboard)
        await state.finish()
        return

    data["traders"][address] = {"nickname": nickname}
    save_user_data(user_id, username, data)

    await message.answer(f"تریدر '{nickname}' با آدرس {address} با موفقیت ثبت شد.", reply_markup=main_keyboard)
    await state.finish()

# حذف تریدر - مرحله 1 نمایش لیست و درخواست شماره
@dp.message_handler(lambda m: m.text == "🗑️ حذف تریدر")
async def delete_trader_start(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "بدون_نام"
    data = load_user_data(user_id, username)
    traders = data.get("traders", {})

    if not traders:
        await message.answer("هیچ تریدری برای حذف وجود ندارد.", reply_markup=main_keyboard)
        return

    text = "لیست تریدرها:\n"
    for i, (addr, info) in enumerate(traders.items(), 1):
        text += f"{i}. {info['nickname']} → {addr}\n"
    text += "\nلطفاً شماره تریدری که می‌خواهید حذف کنید را ارسال کنید:"

    await message.answer(text, reply_markup=types.ReplyKeyboardRemove())

    # ذخیره لیست آدرس‌ها در حالت
    await TraderStates.waiting_for_delete_index.set()
    state = dp.current_state(user=message.from_user.id)
    await state.update_data(traders_list=list(traders.keys()))

# حذف تریدر - مرحله 2 دریافت شماره و حذف
@dp.message_handler(state=TraderStates.waiting_for_delete_index)
async def delete_trader_confirm(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "بدون_نام"
    data = load_user_data(user_id, username)

    user_state = await state.get_data()
    traders_list = user_state.get("traders_list", [])

    try:
        index = int(message.text.strip()) - 1
        if index < 0 or index >= len(traders_list):
            await message.answer("شماره وارد شده نامعتبر است، لطفاً دوباره تلاش کنید.")
            return
    except ValueError:
        await message.answer("لطفاً فقط شماره تریدر را به صورت عددی ارسال کنید.")
        return

    addr_to_remove = traders_list[index]
    nickname_removed = data["traders"][addr_to_remove]["nickname"]
    del data["traders"][addr_to_remove]
    save_user_data(user_id, username, data)

    await message.answer(f"تریدر '{nickname_removed}' با موفقیت حذف شد.", reply_markup=main_keyboard)
    await state.finish()

# دستور ادمین برای مشاهده کل داده ها
@dp.message_handler(commands=['user_data'])
async def user_data_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ شما دسترسی ندارید.")
        return

    text = ""
    files = os.listdir(BACKUP_FOLDER)
    if not files:
        await message.answer("هیچ داده‌ای ثبت نشده است.")
        return

    for filename in files:
        if filename.endswith(".json"):
            filepath = os.path.join(BACKUP_FOLDER, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    user_data = json.load(f)
                except:
                    continue
            user_info = filename.replace(".json", "").split("_")
            user_id_file = user_info[0] if len(user_info) > 0 else "نامشخص"
            username_file = user_info[1] if len(user_info) > 1 else "نامشخص"

            text += f"\n👤 User ID: {user_id_file}\n🔗 Username: @{username_file}\n"
            for addr, info in user_data.get("traders", {}).items():
                text += f"• {info['nickname']} → {addr}\n"

    parts = split_text(text)
    for part in parts:
        await message.answer(part)

# هندلر نا مفهوم و خطا
@dp.message_handler()
async def default_handler(message: types.Message):
    await message.answer(
        "لطفا از دکمه‌های زیر استفاده کنید یا دستور /start را بزنید.",
        reply_markup=main_keyboard
    )


# اجرای ربات
if __name__ == "__main__":
    print("ربات اجرا شد...")
    executor.start_polling(dp, skip_updates=True)
