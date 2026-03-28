from supabase import create_client

SUPABASE_URL = "あなたのURL"
SUPABASE_KEY = "あなたのKEY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def ensure_user(user_id: str):
    res = supabase.table("users").select("user_id").eq("user_id", user_id).execute()

    if not res.data:
        supabase.table("users").insert({
            "user_id": user_id,
            "money": 1000
        }).execute()


def get_money(user_id: str):
    ensure_user(user_id)

    res = supabase.table("users").select("money").eq("user_id", user_id).execute()
    return res.data[0]["money"]


def add_money(user_id: str, amount: int):
    ensure_user(user_id)

    current = get_money(user_id)
    new_balance = current + amount

    supabase.table("users") \
        .update({"money": new_balance}) \
        .eq("user_id", user_id) \
        .execute()

    return new_balance


def get_ranking(limit=10):
    res = supabase.table("users") \
        .select("user_id, money") \
        .order("money", desc=True) \
        .limit(limit) \
        .execute()

    return res.data
