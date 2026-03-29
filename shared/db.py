from supabase import create_client
import os

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


def get_money(user_id: str):
    res = supabase.table("users").select("money").eq("user_id", user_id).execute()

    if not res.data:
        supabase.table("users").insert({
            "user_id": user_id,
            "money": 30000
        }).execute()
        return 30000

    return res.data[0]["money"]


def add_money(user_id: str, amount: int):
    current = get_money(user_id)

    new_value = current + amount

    supabase.table("users").update({
        "money": new_value
    }).eq("user_id", user_id).execute()

    return new_value


def get_setting():
    res = supabase.table("settings").select("value").eq("key", "slot").execute()

    if not res.data:
        supabase.table("settings").insert({
            "key": "slot",
            "value": 3
        }).execute()
        return 3

    return res.data[0]["value"]


def set_setting(value: int):
    supabase.table("settings").upsert({
        "key": "slot",
        "value": value
    }).execute()