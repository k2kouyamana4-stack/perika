import sqlite3

DB_NAME = "money.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        money INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


def get_money(user_id: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT money FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()

    conn.close()
    return result[0] if result else 0


def add_money(user_id: str, amount: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    INSERT INTO users (user_id, money)
    VALUES (?, ?)
    ON CONFLICT(user_id)
    DO UPDATE SET money = money + ?
    """, (user_id, amount, amount))

    conn.commit()
    conn.close()


def get_ranking(limit=10):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT user_id, money
    FROM users
    ORDER BY money DESC
    LIMIT ?
    """, (limit,))

    data = c.fetchall()
    conn.close()

    return data
