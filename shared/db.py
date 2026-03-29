from supabase import create_client
import os

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


# -----------------
# 残高取得
# -----------------
def get_money(user_id: str):
    res = supabase.table("users") \
        .select("money") \
        .eq("user_id", user_id) \
        .execute()

    if not res.data:
        supabase.table("users").insert({
            "user_id": user_id,
            "money": 30000
        }).execute()
        return 30000

    return res.data[0]["money"]


# -----------------
# 残高加算（最重要：RPC版）
# -----------------
def add_money(user_id: str, amount: int):
    supabase.rpc("add_money", {
        "uid": user_id,
        "amt": amount
    }).execute()


# -----------------
# 設定取得
# -----------------
def get_setting():
    res = supabase.table("settings") \
        .select("value") \
        .eq("key", "slot") \
        .execute()

    if not res.data:
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

    # -----------------
# EV取得（新規追加）
# -----------------
def get_ev_setting():
    res = supabase.table("settings") \
        .select("value") \
        .eq("key", "ev") \
        .execute()

    if not res.data:
        supabase.table("settings").insert({
            "key": "ev",
            "value": 3
        }).execute()
        return 3

    return int(res.data[0]["value"])

# -----------------
# モード取得（新規追加）
# -----------------
def get_mode():
    res = supabase.table("settings") \
        .select("value") \
        .eq("key", "mode") \
        .execute()

    if not res.data:
        supabase.table("settings").insert({
            "key": "mode",
            "value": "fixg"
        }).execute()
        return "fixg"

    return res.data[0]["value"]

def get_ev_setting():
    res = supabase.table("settings") \
        .select("value") \
        .eq("key", "ev") \
        .execute()

    if not res.data:
        supabase.table("settings").insert({
            "key": "ev",
            "value": 3
        }).execute()
        return 3

    return int(res.data[0]["value"])