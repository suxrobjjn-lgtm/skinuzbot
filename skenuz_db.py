"""
skenuz_db.py - Universal Database Layer
Lokal SQLite + Render PostgreSQL ikkalasini ham qo'llab-quvvatlaydi.
DATABASE_URL muhit o'zgaruvchisi bo'lsa PostgreSQL, bo'lmasa SQLite ishlatiladi.
"""
import os
import time

DATABASE_URL = os.getenv("DATABASE_URL", "")

# --- PostgreSQL yoki SQLite tanlash ---
if DATABASE_URL and "postgres" in DATABASE_URL:
    import psycopg2
    import psycopg2.extras
    USE_PG = True
else:
    import sqlite3
    USE_PG = False

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skenuz.db")


def get_connection():
    if USE_PG:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def ph(n=1):
    """Placeholder: SQLite uchun ?, PostgreSQL uchun %s"""
    if USE_PG:
        return ", ".join(["%s"] * n) if n > 1 else "%s"
    else:
        return ", ".join(["?"] * n) if n > 1 else "?"


def phs(fields):
    """SET placeholders: field=? yoki field=%s"""
    sep = "%s" if USE_PG else "?"
    return ", ".join([f"{f}={sep}" for f in fields])


def _row_to_dict(row):
    if row is None:
        return None
    if USE_PG:
        return dict(row)
    return dict(row)


def _fetchall(cursor):
    rows = cursor.fetchall()
    return [_row_to_dict(r) for r in rows]


def _q(sql):
    """SQLite ? ni PostgreSQL %s ga almashtiradi"""
    if USE_PG:
        return sql.replace("?", "%s")
    return sql


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    if USE_PG:
        # PostgreSQL uchun jadvallar
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            tg_id BIGINT UNIQUE NOT NULL,
            first_name TEXT DEFAULT '',
            username TEXT DEFAULT '',
            balance REAL DEFAULT 0.00,
            trade_url TEXT DEFAULT '',
            ref_by BIGINT DEFAULT 0,
            ref_count INTEGER DEFAULT 0,
            total_opened INTEGER DEFAULT 0,
            last_daily BIGINT DEFAULT 0,
            phone TEXT DEFAULT '',
            latitude REAL DEFAULT 0.0,
            longitude REAL DEFAULT 0.0,
            is_registered INTEGER DEFAULT 0,
            welcome_reward_claimed INTEGER DEFAULT 0,
            reward_choice TEXT DEFAULT '',
            reward_card_num TEXT DEFAULT '',
            reward_passport_data TEXT DEFAULT '',
            created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW())::BIGINT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id SERIAL PRIMARY KEY,
            user_tg_id BIGINT NOT NULL,
            skin_id INTEGER NOT NULL,
            skin_name TEXT NOT NULL,
            skin_price REAL NOT NULL,
            skin_image TEXT NOT NULL,
            skin_rarity TEXT NOT NULL,
            skin_color TEXT NOT NULL,
            is_sold INTEGER DEFAULT 0,
            is_withdrawn INTEGER DEFAULT 0,
            created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW())::BIGINT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS drops_history (
            id SERIAL PRIMARY KEY,
            user_name TEXT NOT NULL,
            skin_name TEXT NOT NULL,
            skin_price REAL NOT NULL,
            skin_image TEXT NOT NULL,
            skin_color TEXT NOT NULL,
            case_name TEXT NOT NULL,
            created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW())::BIGINT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS battles (
            id SERIAL PRIMARY KEY,
            creator_tg_id BIGINT NOT NULL,
            creator_name TEXT NOT NULL,
            case_id TEXT NOT NULL,
            case_name TEXT NOT NULL,
            case_price REAL NOT NULL,
            opponent_tg_id BIGINT DEFAULT 0,
            opponent_name TEXT DEFAULT '',
            creator_drop_id INTEGER DEFAULT 0,
            opponent_drop_id INTEGER DEFAULT 0,
            winner_tg_id BIGINT DEFAULT 0,
            status TEXT DEFAULT 'waiting',
            created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW())::BIGINT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            amount REAL NOT NULL,
            uses_left INTEGER DEFAULT 100
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (
            setting_key TEXT PRIMARY KEY,
            setting_val TEXT
        )
        """)

        cursor.execute("INSERT INTO promo_codes (code, amount, uses_left) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                       ('SKENUZ', 5.0, 999))
        cursor.execute("INSERT INTO promo_codes (code, amount, uses_left) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                       ('FREECASE', 2.0, 999))
    else:
        # SQLite uchun jadvallar
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER UNIQUE NOT NULL,
            first_name TEXT,
            username TEXT,
            balance REAL DEFAULT 0.00,
            trade_url TEXT DEFAULT '',
            ref_by INTEGER DEFAULT 0,
            ref_count INTEGER DEFAULT 0,
            total_opened INTEGER DEFAULT 0,
            last_daily INTEGER DEFAULT 0,
            phone TEXT DEFAULT '',
            latitude REAL DEFAULT 0.0,
            longitude REAL DEFAULT 0.0,
            is_registered INTEGER DEFAULT 0,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
        """)

        for col, col_type in [
            ("phone", "TEXT DEFAULT ''"),
            ("latitude", "REAL DEFAULT 0.0"),
            ("longitude", "REAL DEFAULT 0.0"),
            ("is_registered", "INTEGER DEFAULT 0"),
            ("welcome_reward_claimed", "INTEGER DEFAULT 0"),
            ("reward_choice", "TEXT DEFAULT ''"),
            ("reward_card_num", "TEXT DEFAULT ''"),
            ("reward_passport_data", "TEXT DEFAULT ''"),
            ("wheel_spun", "INTEGER DEFAULT 0"),
            ("wheel_prize", "TEXT DEFAULT ''"),
            ("deposit_bonus", "INTEGER DEFAULT 0")
        ]:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
            except Exception:
                pass

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_tg_id INTEGER NOT NULL,
            skin_id INTEGER NOT NULL,
            skin_name TEXT NOT NULL,
            skin_price REAL NOT NULL,
            skin_image TEXT NOT NULL,
            skin_rarity TEXT NOT NULL,
            skin_color TEXT NOT NULL,
            is_sold INTEGER DEFAULT 0,
            is_withdrawn INTEGER DEFAULT 0,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS drops_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            skin_name TEXT NOT NULL,
            skin_price REAL NOT NULL,
            skin_image TEXT NOT NULL,
            skin_color TEXT NOT NULL,
            case_name TEXT NOT NULL,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS battles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_tg_id INTEGER NOT NULL,
            creator_name TEXT NOT NULL,
            case_id TEXT NOT NULL,
            case_name TEXT NOT NULL,
            case_price REAL NOT NULL,
            opponent_tg_id INTEGER DEFAULT 0,
            opponent_name TEXT DEFAULT '',
            creator_drop_id INTEGER DEFAULT 0,
            opponent_drop_id INTEGER DEFAULT 0,
            winner_tg_id INTEGER DEFAULT 0,
            status TEXT DEFAULT 'waiting',
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            amount REAL NOT NULL,
            uses_left INTEGER DEFAULT 100
        )
        """)

        cursor.execute("INSERT OR IGNORE INTO promo_codes (code, amount, uses_left) VALUES ('SKENUZ', 5.0, 999)")
        cursor.execute("INSERT OR IGNORE INTO promo_codes (code, amount, uses_left) VALUES ('FREECASE', 2.0, 999)")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (
            setting_key TEXT PRIMARY KEY,
            setting_val TEXT
        )
        """)

    conn.commit()
    conn.close()


def get_or_create_user(tg_id: int, first_name: str = "", username: str = "", ref_by: int = 0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_q("SELECT * FROM users WHERE tg_id = ?"), (tg_id,))
    row = cursor.fetchone()

    if not row:
        if USE_PG:
            cursor.execute("""
            INSERT INTO users (tg_id, first_name, username, balance, ref_by)
            VALUES (%s, %s, %s, 0.00, %s)
            ON CONFLICT (tg_id) DO NOTHING
            """, (tg_id, first_name or "O'yinchi", username or "", ref_by))
        else:
            cursor.execute("""
            INSERT INTO users (tg_id, first_name, username, balance, ref_by)
            VALUES (?, ?, ?, 0.00, ?)
            """, (tg_id, first_name or "O'yinchi", username or "", ref_by))

        if ref_by and ref_by != tg_id:
            cursor.execute(_q("UPDATE users SET balance = balance + 2.00, ref_count = ref_count + 1 WHERE tg_id = ?"), (ref_by,))

        conn.commit()
        cursor.execute(_q("SELECT * FROM users WHERE tg_id = ?"), (tg_id,))
        row = cursor.fetchone()

    conn.close()
    return _row_to_dict(row)


def update_balance(tg_id: int, delta: float):
    conn = get_connection()
    cursor = conn.cursor()
    if USE_PG:
        cursor.execute("UPDATE users SET balance = GREATEST(0, balance + %s) WHERE tg_id = %s", (delta, tg_id))
    else:
        cursor.execute("UPDATE users SET balance = MAX(0, balance + ?) WHERE tg_id = ?", (delta, tg_id))
    cursor.execute(_q("SELECT balance FROM users WHERE tg_id = ?"), (tg_id,))
    res = cursor.fetchone()
    conn.commit()
    conn.close()
    return res["balance"] if res else 0.0


def add_drop_to_inventory(tg_id: int, skin: dict, case_name: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        _q("INSERT INTO inventory (user_tg_id, skin_id, skin_name, skin_price, skin_image, skin_rarity, skin_color) VALUES (?, ?, ?, ?, ?, ?, ?)"),
        (tg_id, skin["id"], skin["name"], skin["price"], skin["image"], skin["rarity"], skin["color"])
    )
    if USE_PG:
        cursor.execute("SELECT lastval()")
    item_id = cursor.fetchone()[0] if USE_PG else cursor.lastrowid

    cursor.execute(_q("UPDATE users SET total_opened = total_opened + 1 WHERE tg_id = ?"), (tg_id,))
    cursor.execute(_q("SELECT first_name FROM users WHERE tg_id = ?"), (tg_id,))
    u_row = cursor.fetchone()
    user_name = u_row["first_name"] if u_row else "O'yinchi"

    cursor.execute(
        _q("INSERT INTO drops_history (user_name, skin_name, skin_price, skin_image, skin_color, case_name) VALUES (?, ?, ?, ?, ?, ?)"),
        (user_name, skin["name"], skin["price"], skin["image"], skin["color"], case_name)
    )

    conn.commit()
    conn.close()
    return item_id


def get_user_inventory(tg_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_q("SELECT * FROM inventory WHERE user_tg_id = ? AND is_sold = 0 ORDER BY id DESC"), (tg_id,))
    rows = _fetchall(cursor)
    conn.close()
    return rows


def sell_inventory_item(tg_id: int, item_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_q("SELECT * FROM inventory WHERE id = ? AND user_tg_id = ? AND is_sold = 0"), (item_id, tg_id))
    item = _row_to_dict(cursor.fetchone())
    if not item:
        conn.close()
        return None, "Item topilmadi yoki allaqachon sotilgan"

    price = item["skin_price"]
    cursor.execute(_q("UPDATE inventory SET is_sold = 1 WHERE id = ?"), (item_id,))
    cursor.execute(_q("UPDATE users SET balance = balance + ? WHERE tg_id = ?"), (price, tg_id))
    cursor.execute(_q("SELECT balance FROM users WHERE tg_id = ?"), (tg_id,))
    new_bal = _row_to_dict(cursor.fetchone())["balance"]
    conn.commit()
    conn.close()
    return new_bal, None


def sell_all_inventory(tg_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_q("SELECT SUM(skin_price) FROM inventory WHERE user_tg_id = ? AND is_sold = 0"), (tg_id,))
    res = cursor.fetchone()
    total_price = list(res.values())[0] if USE_PG else res[0]
    total_price = total_price or 0.0

    if total_price > 0:
        cursor.execute(_q("UPDATE inventory SET is_sold = 1 WHERE user_tg_id = ? AND is_sold = 0"), (tg_id,))
        cursor.execute(_q("UPDATE users SET balance = balance + ? WHERE tg_id = ?"), (total_price, tg_id))

    cursor.execute(_q("SELECT balance FROM users WHERE tg_id = ?"), (tg_id,))
    new_bal = _row_to_dict(cursor.fetchone())["balance"]
    conn.commit()
    conn.close()
    return new_bal, total_price


def get_live_drops(limit: int = 15):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_q("SELECT * FROM drops_history ORDER BY id DESC LIMIT ?"), (limit,))
    rows = _fetchall(cursor)
    conn.close()
    return rows


def update_trade_url(tg_id: int, url: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_q("UPDATE users SET trade_url = ? WHERE tg_id = ?"), (url.strip(), tg_id))
    conn.commit()
    conn.close()
    return True


def claim_daily_bonus(tg_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_q("SELECT last_daily FROM users WHERE tg_id = ?"), (tg_id,))
    row = _row_to_dict(cursor.fetchone())
    now = int(time.time())
    if row and (now - (row.get("last_daily") or 0)) < 86400:
        remaining = 86400 - (now - (row.get("last_daily") or 0))
        conn.close()
        return False, int(remaining)

    cursor.execute(_q("UPDATE users SET balance = balance + 1.00, last_daily = ? WHERE tg_id = ?"), (now, tg_id))
    cursor.execute(_q("SELECT balance FROM users WHERE tg_id = ?"), (tg_id,))
    new_bal = _row_to_dict(cursor.fetchone())["balance"]
    conn.commit()
    conn.close()
    return True, new_bal


def save_user_phone(tg_id: int, phone: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_q("UPDATE users SET phone = ?, is_registered = 1 WHERE tg_id = ?"), (phone, tg_id))
    conn.commit()
    conn.close()


def has_user_phone(tg_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_q("SELECT phone FROM users WHERE tg_id = ?"), (tg_id,))
    row = _row_to_dict(cursor.fetchone())
    conn.close()
    if not row:
        return False
    return bool(row.get("phone") and len(str(row["phone"]).strip()) > 3)


def is_user_registered(tg_id: int) -> bool:
    """Foydalanuvchi telefon raqamini yuborgan bo'lsa ro'yxatdan o'tgan hisoblanadi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_q("SELECT is_registered, phone FROM users WHERE tg_id = ?"), (tg_id,))
    row = _row_to_dict(cursor.fetchone())
    conn.close()
    if not row:
        return False
    return bool((row.get("is_registered") == 1 or row.get("phone")) and len(str(row.get("phone") or "").strip()) > 3)


def get_all_registered_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE is_registered = 1 ORDER BY id DESC")
    rows = _fetchall(cursor)
    conn.close()
    return rows


def claim_welcome_reward(tg_id: int, reward_type: str, card_num: str = "", passport_data: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_q("SELECT welcome_reward_claimed, balance FROM users WHERE tg_id = ?"), (tg_id,))
    row = _row_to_dict(cursor.fetchone())
    if not row or row.get("welcome_reward_claimed") == 1:
        conn.close()
        return False, "Siz allaqachon birinchi ro'yxatdan o'tish mukofotini olgansiz!"

    if reward_type == "diamonds":
        add_bal = 2.40
        cursor.execute(
            _q("UPDATE users SET balance = balance + ?, welcome_reward_claimed = 1, reward_choice = 'diamonds' WHERE tg_id = ?"),
            (add_bal, tg_id)
        )
    else:
        cursor.execute(
            _q("UPDATE users SET welcome_reward_claimed = 1, reward_choice = 'cash', reward_card_num = ?, reward_passport_data = ? WHERE tg_id = ?"),
            (card_num, passport_data, tg_id)
        )

    conn.commit()
    cursor.execute(_q("SELECT * FROM users WHERE tg_id = ?"), (tg_id,))
    updated = _row_to_dict(cursor.fetchone())
    conn.close()
    return True, updated if updated else {}


def spin_wheel(tg_id: int):
    """
    Omad Barabani (Fortune Wheel) aylantirish logikasi.
    7 ta sektor:
      0: 30 000 Olmos (Asosiy bosh sovrin)
      1: +50% Depozit bonusi (Birinchi depozit uchun)
      2: 5 000 Olmos
      3: +100% Depozit bonusi (Birinchi depozit uchun)
      4: 2 000 Olmos
      5: +200% Depozit bonusi (Birinchi depozit uchun)
      6: Bankrot (Omad kelmadi)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_q("SELECT wheel_spun, wheel_prize, balance, deposit_bonus FROM users WHERE tg_id = ?"), (tg_id,))
    row = _row_to_dict(cursor.fetchone())
    if not row:
        conn.close()
        return False, "Foydalanuvchi topilmadi", None, 0.0, None

    if row.get("wheel_spun") == 1:
        conn.close()
        return False, "Siz omad barabanini allaqachon aylantirgansiz!", None, row.get("balance", 0.0), row.get("wheel_prize")

    sectors = [
        {"index": 0, "type": "diamonds", "amount": 30000, "label": "30 000 Olmos", "weight": 5, "usd": 2.40},
        {"index": 1, "type": "bonus", "amount": 50, "label": "+50% Depozit bonusi", "weight": 25, "usd": 0.0},
        {"index": 2, "type": "diamonds", "amount": 5000, "label": "5 000 Olmos", "weight": 20, "usd": 0.40},
        {"index": 3, "type": "bonus", "amount": 100, "label": "+100% Depozit bonusi", "weight": 20, "usd": 0.0},
        {"index": 4, "type": "diamonds", "amount": 2000, "label": "2 000 Olmos", "weight": 20, "usd": 0.16},
        {"index": 5, "type": "bonus", "amount": 200, "label": "+200% Depozit bonusi", "weight": 5, "usd": 0.0},
        {"index": 6, "type": "bankrupt", "amount": 0, "label": "Bankrot", "weight": 5, "usd": 0.0},
    ]

    import random
    weights = [s["weight"] for s in sectors]
    chosen = random.choices(sectors, weights=weights, k=1)[0]

    add_balance = chosen["usd"]
    deposit_bonus = chosen["amount"] if chosen["type"] == "bonus" else (row.get("deposit_bonus") or 0)

    cursor.execute(
        _q("UPDATE users SET balance = balance + ?, wheel_spun = 1, wheel_prize = ?, deposit_bonus = ? WHERE tg_id = ?"),
        (add_balance, chosen["label"], deposit_bonus, tg_id)
    )
    conn.commit()

    cursor.execute(_q("SELECT balance, wheel_spun, wheel_prize, deposit_bonus FROM users WHERE tg_id = ?"), (tg_id,))
    updated_user = _row_to_dict(cursor.fetchone())
    conn.close()

    return True, "Muvaffaqiyatli", chosen, updated_user["balance"], updated_user["wheel_prize"]


def set_setting(key: str, val: str):
    conn = get_connection()
    cursor = conn.cursor()
    if USE_PG:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (setting_key TEXT PRIMARY KEY, setting_val TEXT)
        """)
        cursor.execute(
            "INSERT INTO bot_settings (setting_key, setting_val) VALUES (%s, %s) ON CONFLICT (setting_key) DO UPDATE SET setting_val = EXCLUDED.setting_val",
            (key, str(val))
        )
    else:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (setting_key TEXT PRIMARY KEY, setting_val TEXT)
        """)
        cursor.execute("INSERT OR REPLACE INTO bot_settings (setting_key, setting_val) VALUES (?, ?)", (key, str(val)))
    conn.commit()
    conn.close()


def get_setting(key: str, default: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(_q("SELECT setting_val FROM bot_settings WHERE setting_key = ?"), (key,))
        row = _row_to_dict(cursor.fetchone())
        conn.close()
        return row["setting_val"] if row else default
    except Exception:
        conn.close()
        return default
