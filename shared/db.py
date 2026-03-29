from supabase import create_client
import os

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)


# -----------------
# ユーザー残高取得
# -----------------
def get_money(user_id: str):
    res = supabase.table("users").select("money").eq("user_id", user_id).execute()

    if len(res.data) == 0:
        supabase.table("users").insert({
            "user_id": user_id,
            "money": 30000
        }).execute()
        return 30000

    return res.data[0]["money"]


# -----------------
# 加算（最重要）
# -----------------
def add_money(user_id: str, amount: int):
    current = get_money(user_id)
    new_value = current + amount

    supabase.table("users").update({
        "money": new_value
    }).eq("user_id", user_id).execute()

    return new_value


# -----------------
# 設定取得
# -----------------
def get_setting():
    res = supabase.table("settings").select("value").eq("key", "slot").execute()

    if len(res.data) == 0:
        supabase.table("settings").insert({
            "key": "slot",
            "value": 3
        }).execute()
        return 3

    return res.data[0]["value"]


# -----------------
# 設定変更
# -----------------
def set_setting(value: int):
    supabase.table("settings").upsert({
        "key": "slot",
        "value": value
    }).execute()