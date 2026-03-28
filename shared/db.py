from supabase import create_client

SUPABASE_URL = "https://qvqsuayqinimwwuqfipe.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2cXN1YXlxaW5pbXd3dXFmaXBlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDcwMjA2NCwiZXhwIjoyMDkwMjc4MDY0fQ.oh2AOx_bi1y04G-I98-SbK7OtvBP33aoV7afxmX0x4g"

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