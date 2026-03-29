from supabase import create_client
import os

# -----------------
# Supabase接続
# -----------------
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)


# =========================
# ユーザー残高取得
# =========================
def get_money(user_id: str):
    res = supabase.table("users") \
        .select("money") \
        .eq("user_id", user_id) \
        .execute()

    if res.data:
        return res.data[0]["money"]

    # 初回作成
    supabase.table("users").insert({
        "user_id": user_id,
        "money": 30000
    }).execute()

    return 30000


# =========================
# 残高増減（安全版）
# =========================
def add_money(user_id: str, amount: int):

    # RPCで安全更新（推奨）
    try:
        supabase.rpc("add_money", {
            "uid": user_id,
            "amt": amount
        }).execute()
    except Exception:
        # フォールバック（RPCない場合）
        res = supabase.table("users") \
            .select("money") \
            .eq("user_id", user_id) \
            .single() \
            .execute()

        current = res.data["money"]

        supabase.table("users") \
            .update({"money": current + amount}) \
            .eq("user_id", user_id) \
            .execute()


# =========================
# ランキング
# =========================
def get_ranking(limit: int = 10):
    res = supabase.table("users") \
        .select("user_id, money") \
        .order("money", desc=True) \
        .limit(limit) \
        .execute()

    return res.data


# =========================
# スロット設定取得
# =========================
def get_setting():
    res = supabase.table("settings") \
        .select("value") \
        .eq("key", "slot") \
        .execute()

    if res.data:
        return res.data[0]["value"]

    supabase.table("settings").insert({
        "key": "slot",
        "value": 3
    }).execute()

    return 3


# =========================
# スロット設定変更
# =========================
def set_setting(value: int):
    supabase.table("settings").upsert({
        "key": "slot",
        "value": value
    }).execute()