import os

# -----------------
# Discord
# -----------------
TOKEN = os.getenv("DISCORD_TOKEN")

# 管理者ID（setで高速＆安全）
ADMIN_IDS = {
    947136029285048340,
    1423839192391356496
}


# -----------------
# Supabase
# -----------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")