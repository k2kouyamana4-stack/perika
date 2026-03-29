from supabase import create_client
import os

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)


# -----------------
# 所持金取得
# -----------------
def get_money(user_id: str):
    res = supabase.table("users").select("*").eq("user_id", user_id).execute()

    if res.data:
        return res.data[0]["money"]

    supabase.table("users").insert({
        "user_id": user_id,
        "money": 30000
    }).execute()

    return 30000


# -----------------
# 所持金変更
# -----------------
def add_money(user_id: str, amount: int):
    current = get_money(user_id)
    new_money = current + amount

    supabase.table("users").update({
        "money": new_money
    }).eq("user_id", user_id).execute()


# -----------------
# ランキング
# -----------------
def get_ranking(limit=10):
    res = supabase.table("users") \
        .select("*") \
        .order("money", desc=True) \
        .limit(limit) \
        .execute()

    return res.data


# -----------------
# 設定（スロット倍率）
# -----------------
def get_setting():
    res = supabase.table("settings").select("*").eq("key", "slot").execute()

    if res.data:
        return res.data[0]["value"]

    supabase.table("settings").insert({
        "key": "slot",
        "value": 1
    }).execute()

    return 1


def set_setting(value: int):
    supabase.table("settings").upsert({
        "key": "slot",
        "value": value
    }).execute()