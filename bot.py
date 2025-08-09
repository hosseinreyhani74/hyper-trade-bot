import os
import json
from aiogram import Bot, Dispatcher, executor, types

# ========== تنظیمات ==========
API_TOKEN = "توکن_ربات_تو_اینجا_قرار_بده"  # جایگزین کن
ADMIN_ID = 805989529  # آیدی تلگرام خودت

# مسیر پوشه و فایل ذخیره داده ها
BACKUP_FOLDER = "backup"
os.makedirs(BACKUP_FOLDER, exist_ok=True)

# ================= توابع کمکی =================
def get_user_filepath(user_id, username):
    safe_username = username if username else "بدون_نام"
    # حذف کاراکترهای غیرمجاز در نام فایل
    safe_username = "".join(c for c in safe_username if c.isalnum() or c in ("_", "-"))
    return os.path.join(BACKUP_FOLDER, f"{user_id}_{safe_username}.json")

def load_user_data(user_id, username):
    filepath = get_user_filepath(user_id, username)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {"traders": {}}
    return {"traders": {}}

def save_user_data(user_id, username, data):
    filepath = get_user_filepath(user_id, username)
    with open(filepath, "w", encoding="utf-8") as f:
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

# ========== راه اندازی ربات ==========
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ========== دستورات اصلی ==========

@dp.message_handler(lambda msg: msg.text == "📊 پروفایل")
async def show_profile(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "بدون_نام"
    data = load_user_data(user_id, username)
    traders = data.get("traders", {})
    trader_count = len(traders)

    text = (
        f"📊 پروفایل شما:\n\n"
        f"👤 نام کاربری: @{username}\n"
        f"🆔 آیدی عددی: {user_id}\n"
        f"📈 تعداد تریدرهای ثبت‌شده: {trader_count}\n"
    )

    if trader_count > 0:
        text += "\n📋 لیست تریدرها:\n"
        for addr, info in traders.items():
            text += f"🏷️ {info['nickname']} → 🔗 {addr}\n"

    await message.answer(text)


@dp.message_handler(lambda msg: msg.text == "➕ افزودن تریدر")
async def add_trader_start(message: types.Message):
    await message.answer("لطفاً آدرس تریدر را ارسال کنید:")

    # ذخیره حالت اضافه کردن در حافظه موقت کاربر
    dp.current_state(user=message.from_user.id).set_state("ADDING_ADDRESS")


@dp.message_handler(lambda msg: True, state="ADDING_ADDRESS")
async def add_trader_address(message: types.Message):
    address = message.text.strip()
    user_id = str(message.from_user.id)
    username = message.from_user.username or "بدون_نام"
    data = load_user_data(user_id, username)

    # ذخیره آدرس در داده‌های موقت (مثلاً تو state یا session)
    # چون aiogram بدون FSM پیاده‌سازی نیاز داره
    await bot.send_message(user_id, "لطفاً نام مستعار (nickname) تریدر را ارسال کنید.")

    # برای سادگی، داده‌ها را موقتا در فایل ذخیره نمی‌کنیم و از حالت استفاده می‌کنیم
    # اما چون در نسخه فعلی ما FSM تعریف نشده، می‌تونیم روش دیگه‌ای بکار ببریم
    # ولی این بخش را اصلاح می‌کنم در ادامه

    # ذخیره آدرس به صورت داینامیک:
    dp.current_state(user=message.from_user.id).update_data(address=address)
    await dp.current_state(user=message.from_user.id).set_state("ADDING_NICKNAME")


@dp.message_handler(lambda msg: True, state="ADDING_NICKNAME")
async def add_trader_nickname(message: types.Message):
    nickname = message.text.strip()
    user_id = str(message.from_user.id)
    username = message.from_user.username or "بدون_نام"
    data = load_user_data(user_id, username)

    state = dp.current_state(user=message.from_user.id)
    state_data = await state.get_data()
    address = state_data.get("address")

    if not address:
        await message.answer("خطا در دریافت آدرس، لطفاً دوباره از ابتدا تلاش کنید.")
        await state.finish()
        return

    if "traders" not in data:
        data["traders"] = {}

    # اضافه کردن تریدر جدید
    data["traders"][address] = {"nickname": nickname}

    save_user_data(user_id, username, data)

    await message.answer(f"تریدر '{nickname}' با آدرس {address} با موفقیت ثبت شد.")
    await state.finish()


@dp.message_handler(lambda msg: msg.text == "🗑️ حذف تریدر")
async def delete_trader(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "بدون_نام"
    data = load_user_data(user_id, username)
    traders = data.get("traders", {})

    if not traders:
        await message.answer("هیچ تریدری برای حذف وجود ندارد.")
        return

    # ارسال لیست تریدرها با شماره
    text = "لیست تریدرها:\n"
    for i, (addr, info) in enumerate(traders.items(), 1):
        text += f"{i}. {info['nickname']} → {addr}\n"
    text += "\nلطفاً شماره تریدری که می‌خواهید حذف کنید را ارسال کنید."

    await message.answer(text)

    # ذخیره لیست آدرس‌ها برای حذف در حافظه موقت
    await dp.current_state(user=message.from_user.id).update_data(traders_list=list(traders.keys()))
    await dp.current_state(user=message.from_user.id).set_state("WAITING_FOR_DELETE_INDEX")


@dp.message_handler(lambda msg: True, state="WAITING_FOR_DELETE_INDEX")
async def delete_trader_confirm(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "بدون_نام"
    data = load_user_data(user_id, username)

    state = dp.current_state(user=message.from_user.id)
    state_data = await state.get_data()
    traders_list = state_data.get("traders_list", [])

    try:
        index = int(message.text.strip()) - 1
        if index < 0 or index >= len(traders_list):
            await message.answer("شماره وارد شده نامعتبر است، لطفاً دوباره تلاش کنید.")
            return
    except:
        await message.answer("لطفاً فقط شماره تریدر را به صورت عددی ارسال کنید.")
        return

    address_to_remove = traders_list[index]
    removed_nickname = data["traders"][address_to_remove]["nickname"]
    del data["traders"][address_to_remove]

    save_user_data(user_id, username, data)

    await message.answer(f"تریدر '{removed_nickname}' با موفقیت حذف شد.")
    await state.finish()


# دستور ادمین برای مشاهده کل داده ها
@dp.message_handler(commands=['user_data'])
async def user_data_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ شما دسترسی ندارید.")
        return

    # اینجا باید کل فایل های بکاپ رو بخوانیم و ارسال کنیم
    text = ""
    for filename in os.listdir(BACKUP_FOLDER):
        if filename.endswith(".json"):
            filepath = os.path.join(BACKUP_FOLDER, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    user_data = json.load(f)
                except:
                    continue
            user_info = filename.replace(".json", "").split("_")
            if len(user_info) >= 2:
                user_id_file, username_file = user_info[0], user_info[1]
            else:
                user_id_file, username_file = "نامشخص", "نامشخص"

            text += f"\n👤 User ID: {user_id_file}\n🔗 Username: @{username_file}\n"
            traders = user_data.get("traders", {})
            for addr, info in traders.items():
                text += f"• {info['nickname']} → {addr}\n"

    parts = split_text(text)
    for part in parts:
        await message.answer(part)


# ======== اجرای ربات ========
if __name__ == "__main__":
    from aiogram.contrib.fsm_storage.memory import MemoryStorage
    from aiogram.dispatcher import FSMContext
    from aiogram.dispatcher.filters.state import State, StatesGroup

    storage = MemoryStorage()
    dp.storage = storage

    print("ربات اجرا شد...")
    executor.start_polling(dp, skip_updates=True)
