from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# 通貨系
# -------------------------

def get_money(user_id: str):
    res = supabase.table("users").select("money").eq("user_id", user_id).execute()

    if not res.data:
        supabase.table("users").insert({
            "user_id": user_id,
            "money": 30000
        }).execute()
        return 30000

    return int(res.data[0]["money"])


def add_money(user_id: str, amount: int):
    current = get_money(user_id)

    supabase.table("users").upsert({
        "user_id": user_id,
        "money": current + amount
    }).execute()


def get_ranking(limit: int = 10):
    res = (
        supabase.table("users")
        .select("user_id, money")
        .order("money", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data


# -------------------------
# スロット設定
# -------------------------

def get_setting():
    res = supabase.table("settings").select("value").eq("key", "slot_setting").execute()

    if not res.data:
        supabase.table("settings").insert({
            "key": "slot_setting",
            "value": 3
        }).execute()
        return 3

    return int(res.data[0]["value"])


def set_setting(value: int):
    supabase.table("settings").upsert({
        "key": "slot_setting",
        "value": value
    }).execute()