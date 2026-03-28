import sqlite3
from supabase import create_client

# Supabase設定
SUPABASE_URL = "https://qvqsuayqinimwwuqfipe.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2cXN1YXlxaW5pbXd3dXFmaXBlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDcwMjA2NCwiZXhwIjoyMDkwMjc4MDY0fQ.oh2AOx_bi1y04G-I98-SbK7OtvBP33aoV7afxmX0x4g"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ローカルDB
conn = sqlite3.connect("money.db")
c = conn.cursor()

c.execute("SELECT user_id, money FROM users")
rows = c.fetchall()

for user_id, money in rows:
    supabase.table("users").upsert({
        "user_id": user_id,
        "money": money
    }).execute()

print("移行完了")