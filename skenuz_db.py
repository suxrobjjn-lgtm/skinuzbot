import sqlite3
import os
import time

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skenuz.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Foydalanuvchilar jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER UNIQUE NOT NULL,
        first_name TEXT,
        username TEXT,
        balance REAL DEFAULT 10.00,
        trade_url TEXT DEFAULT '',
        ref_by INTEGER DEFAULT 0,
        ref_count INTEGER DEFAULT 0,
        total_opened INTEGER DEFAULT 0,
        last_daily INTEGER DEFAULT 0,
        created_at INTEGER DEFAULT (strftime('%s', 'now'))
    )
    """)

    # 2. Foydalanuvchi inventari (yutilgan skinlar)
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

    # 3. Ochilgan keyslar tarixi (Live Drop uchun)
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

    # 4. Case Battle xonalari
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
        status TEXT DEFAULT 'waiting', -- waiting, finished
        created_at INTEGER DEFAULT (strftime('%s', 'now'))
    )
    """)

    # 5. Promokodlar
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS promo_codes (
        code TEXT PRIMARY KEY,
        amount REAL NOT NULL,
        uses_left INTEGER DEFAULT 100
    )
    """)

    # Boshlang'ich test promokodlar
    cursor.execute("INSERT OR IGNORE INTO promo_codes (code, amount, uses_left) VALUES ('SKENUZ', 5.0, 999)")
    cursor.execute("INSERT OR IGNORE INTO promo_codes (code, amount, uses_left) VALUES ('FREECASE', 2.0, 999)")

    conn.commit()
    conn.close()

def get_or_create_user(tg_id: int, first_name: str = "", username: str = "", ref_by: int = 0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    row = cursor.fetchone()

    if not row:
        # Yangi foydalanuvchiga bonus 10$ start balansi beriladi!
        cursor.execute("""
        INSERT INTO users (tg_id, first_name, username, balance, ref_by) 
        VALUES (?, ?, ?, 10.00, ?)
        """, (tg_id, first_name or "O'yinchi", username or "", ref_by))
        
        if ref_by and ref_by != tg_id:
            # Referal egasiga bonus 2.00$
            cursor.execute("UPDATE users SET balance = balance + 2.00, ref_count = ref_count + 1 WHERE tg_id = ?", (ref_by,))

        conn.commit()
        cursor.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        row = cursor.fetchone()

    conn.close()
    return dict(row)

def update_balance(tg_id: int, delta: float):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = MAX(0, balance + ?) WHERE tg_id = ?", (delta, tg_id))
    cursor.execute("SELECT balance FROM users WHERE tg_id = ?", (tg_id,))
    res = cursor.fetchone()
    conn.commit()
    conn.close()
    return res[0] if res else 0.0

def add_drop_to_inventory(tg_id: int, skin: dict, case_name: str = ""):
    conn = get_connection()
    cursor = conn.cursor()

    # Inventarga qo'shish
    cursor.execute("""
    INSERT INTO inventory (user_tg_id, skin_id, skin_name, skin_price, skin_image, skin_rarity, skin_color)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (tg_id, skin["id"], skin["name"], skin["price"], skin["image"], skin["rarity"], skin["color"]))
    item_id = cursor.lastrowid

    # Ochilgan keyslar statistikasini oshirish
    cursor.execute("UPDATE users SET total_opened = total_opened + 1 WHERE tg_id = ?", (tg_id,))

    # Live drop lentasiga qo'shish
    cursor.execute("SELECT first_name FROM users WHERE tg_id = ?", (tg_id,))
    u_row = cursor.fetchone()
    user_name = u_row[0] if u_row else "O'yinchi"

    cursor.execute("""
    INSERT INTO drops_history (user_name, skin_name, skin_price, skin_image, skin_color, case_name)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_name, skin["name"], skin["price"], skin["image"], skin["color"], case_name))

    conn.commit()
    conn.close()
    return item_id

def get_user_inventory(tg_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE user_tg_id = ? AND is_sold = 0 ORDER BY id DESC", (tg_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def sell_inventory_item(tg_id: int, item_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE id = ? AND user_tg_id = ? AND is_sold = 0", (item_id, tg_id))
    item = cursor.fetchone()
    if not item:
        conn.close()
        return None, "Item topilmadi yoki allaqachon sotilgan"

    price = item["skin_price"]
    cursor.execute("UPDATE inventory SET is_sold = 1 WHERE id = ?", (item_id,))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE tg_id = ?", (price, tg_id))
    cursor.execute("SELECT balance FROM users WHERE tg_id = ?", (tg_id,))
    new_bal = cursor.fetchone()[0]

    conn.commit()
    conn.close()
    return new_bal, None

def sell_all_inventory(tg_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(skin_price) FROM inventory WHERE user_tg_id = ? AND is_sold = 0", (tg_id,))
    total_price = cursor.fetchone()[0] or 0.0

    if total_price > 0:
        cursor.execute("UPDATE inventory SET is_sold = 1 WHERE user_tg_id = ? AND is_sold = 0", (tg_id,))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE tg_id = ?", (total_price, tg_id))
    
    cursor.execute("SELECT balance FROM users WHERE tg_id = ?", (tg_id,))
    new_bal = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return new_bal, total_price

def get_live_drops(limit: int = 15):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drops_history ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_trade_url(tg_id: int, url: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET trade_url = ? WHERE tg_id = ?", (url.strip(), tg_id))
    conn.commit()
    conn.close()
    return True

def claim_daily_bonus(tg_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT last_daily FROM users WHERE tg_id = ?", (tg_id,))
    row = cursor.fetchone()
    now = int(time.time())
    if row and (now - row[0]) < 86400:
        remaining = 86400 - (now - row[0])
        conn.close()
        return False, int(remaining)

    # 1$ kunlik bonus
    cursor.execute("UPDATE users SET balance = balance + 1.00, last_daily = ? WHERE tg_id = ?", (now, tg_id))
    cursor.execute("SELECT balance FROM users WHERE tg_id = ?", (tg_id,))
    new_bal = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return True, new_bal
