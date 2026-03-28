import json
import sqlite3

DB_NAME = "money.db"

# DB初期化
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    money INTEGER DEFAULT 0
)
""")

conn.commit()

# JSON読み込み
with open("money.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 移行
for user_id, money in data.items():
    c.execute("""
    INSERT INTO users (user_id, money)
    VALUES (?, ?)
    ON CONFLICT(user_id)
    DO UPDATE SET money = ?
    """, (user_id, money, money))

conn.commit()
conn.close()

print("移行完了")
