import json, os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup

API_TOKEN = "7755592258:AAHhbD8C-l8gG3C3TaKTh5649kA1AVgakqQ"
ADMIN_USERNAME = "hosseinreyhani74"
DATA_FOLDER = "data"
DATA_PATH = os.path.join(DATA_FOLDER, "users.json")

# ساخت دیتا فولدر
if os.path.exists(DATA_FOLDER) and not os.path.isdir(DATA_FOLDER):
    os.remove(DATA_FOLDER)
os.makedirs(DATA_FOLDER, exist_ok=True)

if not os.path.exists(DATA_PATH):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump({}, f)

def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(d):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add("➕ افزودن تریدر").add("🗑 حذف تریدر")
menu.add("📋 لیست تریدرها").add("📊 پروفایل")

user_state = {}

@dp.message_handler(commands=["start"])
async def start_bot(msg: types.Message):
    user_state.pop(msg.from_user.id, None)
    await msg.answer("سلام! گزینه‌ای رو از منو انتخاب کن:", reply_markup=menu)

@dp.message_handler(lambda m: m.text == "➕ افزودن تریدر")
async def step1(m):
    user_state[m.from_user.id] = {"step": "addr"}
    await m.answer("آیدی تریدر رو وارد کن:")

@dp.message_handler(lambda m: m.text == "🗑 حذف تریدر")
async def step_del(m):
    data = load_data()
    uid = str(m.from_user.id)
    if uid not in data or not data[uid]["traders"]:
        await m.answer("شما هنوز تریدری ثبت نکردی.")
        return
    user_state[m.from_user.id] = {"step": "del"}
    ids = "\n".join([f"{t['nickname']} → {addr}" for addr, t in data[uid]["traders"].items()])
    await m.answer("کدوم رو حذف کنم؟\n" + ids)

@dp.message_handler(lambda m: m.text == "📋 لیست تریدرها")
async def list_tr(m):
    data = load_data()
    uid = str(m.from_user.id)
    if uid not in data or not data[uid]["traders"]:
        await m.answer("هیچ تریدری ثبت نشده.")
        return
    lst = "لیست تریدرهات:\n"
    for a, t in data[uid]["traders"].items():
        lst += f"• {t['nickname']} → {a}\n"
    await m.answer(lst)

@dp.message_handler(lambda m: m.text == "📊 پروفایل")
async def profile(m):
    data = load_data()
    uid = str(m.from_user.id)
    if uid not in data:
        await m.answer("هنوز اطلاعاتی ذخیره نکردی.")
        return
    tr = data[uid]["traders"]
    total = len(tr)
    bots = sum(1 for v in tr.values() if v.get("is_bot"))
    real = total - bots
    alert = data[uid].get("alert_value", "مشخص نشده")
    await m.answer(f"📊 پروفایل:\nکل: {total}\nربات: {bots}\nواقعی: {real}\nهشدار از: {alert}")

@dp.message_handler(commands=["admin"])
async def admin_cmd(m):
    if m.from_user.username != ADMIN_USERNAME:
        await m.answer("دسترسی نداری.")
        return
    data = load_data()
    txt = "👥 همه کاربران و تریدرها:\n"
    for uid, info in data.items():
        txt += f"\nUser {uid}:\n"
        for a, t in info["traders"].items():
            txt += f"• {t['nickname']} → {a}\n"
    await m.answer(txt or "داده‌ای نیست")

@dp.message_handler()
async def all_msg(m):
    uid = str(m.from_user.id)
    st = user_state.get(m.from_user.id)
    data = load_data()
    if uid not in data:
        data[uid] = {"traders": {}, "alert_value": 100000}

    if st:
        if st["step"] == "addr":
            user_state[m.from_user.id] = {"step": "nick", "addr": m.text.strip()}
            await m.answer("اسم مستعار تریدر رو وارد کن:")
        elif st["step"] == "nick":
            addr = st["addr"]
            nick = m.text.strip()
            is_bot = "bot" in nick.lower() or "bot" in addr.lower()
            data[uid]["traders"][addr] = {"nickname": nick, "is_bot": is_bot}
            save_data(data)
            user_state.pop(m.from_user.id)
            await m.answer("✅ تریدر ذخیره شد.")
        elif st["step"] == "del":
            addr = m.text.strip()
            if addr in data[uid]["traders"]:
                del data[uid]["traders"][addr]
                save_data(data)
                user_state.pop(m.from_user.id)
                await m.answer("✅ حذف شد.")
            else:
                await m.answer("❌ پیدا نشد.")
    else:
        await m.answer("لطفا از منو گزینه انتخاب کن.")
