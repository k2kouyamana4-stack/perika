from supabase import create_client
import os

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# =========================
# 残高取得
# =========================
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


# =========================
# 残高加算（RPC）
# =========================
def add_money(user_id: str, amount: int):
    supabase.rpc("add_money", {
        "uid": user_id,
        "amt": amount
    }).execute()


# =========================
# スロット設定取得
# =========================
def get_setting():
    res = supabase.table("settings") \
        .select("value") \
        .eq("key", "slot") \
        .execute()

    if not res.data:
        supabase.table("settings").insert({
            "key": "slot",
            "value": "3"
        }).execute()
        return 3

    return int(res.data[0]["value"])


# =========================
# スロット設定変更
# =========================
def set_setting(value: str):
    supabase.table("settings").upsert({
        "key": "slot",
        "value": str(value)
    }).execute()


# =========================
# EV取得
# =========================
def get_ev_setting():
    res = supabase.table("settings") \
        .select("value") \
        .eq("key", "ev") \
        .execute()

    if not res.data:
        supabase.table("settings").insert({
            "key": "ev",
            "value": "3"
        }).execute()
        return 3

    return float(res.data[0]["value"])


# =========================
# mode取得
# =========================
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


# =========================
# mode変更
# =========================
def set_mode(value: str):
    supabase.table("settings").upsert({
        "key": "mode",
        "value": value
    }).execute()


# =========================
# 汎用設定取得（EV範囲用）
# =========================
def get_setting(key: str):
    res = supabase.table("settings") \
        .select("value") \
        .eq("key", key) \
        .execute()

    if not res.data:
        return None

    return res.data[0]["value"]