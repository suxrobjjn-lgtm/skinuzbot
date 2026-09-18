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
from aiogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    WebAppInfo
)
from aiogram.filters import CommandStart, Command

import skenuz_db as db
import skins_data as data

# Sozlamalar
BOT_TOKEN = os.getenv("BOT_TOKEN", "8831392374:AAGL9Ks0X31ZLgmfKnsMySwpzd74AF0kLLM").strip()
PORT = int(os.getenv("PORT", 8080))
WEB_APP_URL = os.getenv("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}").rstrip("/")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- AIOGRAM BOT LOGIKASI ---
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

def get_main_keyboard():
    # Mini App tugmasi
    app_url = f"{WEB_APP_URL}/"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎮 O'YINNI BOSHLASH (Mini App)", web_app=WebAppInfo(url=app_url))
        ],
        [
            InlineKeyboardButton(text="🎁 Bepul Kunlik Keys", web_app=WebAppInfo(url=app_url)),
            InlineKeyboardButton(text="⚡ Skin Upgrader", web_app=WebAppInfo(url=app_url))
        ],
        [
            InlineKeyboardButton(text="💬 Rasmiy Kanal", url="https://t.me/kino_comfy_gr")
        ]
    ])
    return kb

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

    text = (
        f"👋 <b>Assalomu alaykum, {message.from_user.first_name}!</b>\n\n"
        f"🔥 <b>SKENUZ CS2 — Telegramdagi eng yirik keys ochish va skinlar platformasiga xush kelibsiz!</b>\n\n"
        f"🎁 Sizga boshlang'ich <b>10.00$ BEPUL BALANS</b> berildi!\n"
        f"💰 Balansingiz: <b>{user['balance']:.2f}$</b>\n\n"
        f"🎮 O'yin imkoniyatlari:\n"
        f"• 🎁 <b>Kunlik Bepul Keyslar</b>\n"
        f"• 🔪 <b>Karambit, Butterfly, AWP Dragon Lore</b> va boshqa yuzlab skinlar\n"
        f"• ⚡ <b>Skin Upgrader:</b> Arzon skinni bir zumda qimmatiga oshirish\n"
        f"• ⚔️ <b>Case Battle:</b> Real vaqtda boshqa o'yinchilar bilan jangga kirish\n"
        f"• 🎒 <b>Steamga chiqarish:</b> Yutib olingan skinlarni to'g'ridan-to'g'ri o'z Steam hisobingizga olish\n\n"
        f"👇 <b>Quyidagi tugmani bosing va o'yinga kiring:</b>"
    )

    await message.answer(text, reply_markup=get_main_keyboard())

@dp.message(Command("balance"))
async def cmd_balance(message: Message):
    user = db.get_or_create_user(message.from_user.id)
    await message.answer(
        f"💰 <b>Sizning balansingiz:</b> <code>{user['balance']:.2f}$</code>\n"
        f"Taklif qilgan do'stlaringiz: <b>{user['ref_count']}</b> ta\n\n"
        f"Balansni to'ldirish yoki keys ochish uchun Mini App ga kiring!",
        reply_markup=get_main_keyboard()
    )

# --- AIOHTTP WEB SERVER & REST API ---
routes = web.RouteTableDef()

# 1. Mini App statik sahifalariga xizmat
WEBAPP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webapp")

@routes.get("/")
async def serve_index(request):
    index_file = os.path.join(WEBAPP_DIR, "index.html")
    return web.FileResponse(index_file)

@routes.get("/app.css")
async def serve_css(request):
    return web.FileResponse(os.path.join(WEBAPP_DIR, "app.css"))

@routes.get("/app.js")
async def serve_js(request):
    return web.FileResponse(os.path.join(WEBAPP_DIR, "app.js"))

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

# 3. API: Keys ochish (Provably Fair)
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

    # Ehtimollik bo'yicha skinni aniqlash
    items = case_info["items"]
    weights = [it["weight"] for it in items]
    chosen_item = random.choices(items, weights=weights, k=1)[0]
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

    # 2. Telegram Bot Polling
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Telegram Bot polling boshlandi (@Skenuzbot)!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi.")
