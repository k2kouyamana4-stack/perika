import sys
import os
import random
from threading import Thread
from flask import Flask

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import discord
from discord.ext import commands

from shared.db import (
    get_money,
    add_money,
    get_setting,
    set_setting,
    get_ev_setting,
    get_mode,
    set_mode
)

# =========================
# Flask（Render対策）
# =========================
app = Flask(__name__)

@app.route("/")
def home():
    return "alive"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# =========================
# Bot
# =========================
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

ADMIN_IDS = {947136029285048340, 1423839192391356496}


# =========================
# スロット設定
# =========================
def get_symbol_table(setting):
    return {
        1: [("🍒", 85), ("🍋", 14), ("🍉", 0.8), ("⭐", 0.15), ("💎", 0.04), ("7️⃣", 0.01)],
        2: [("🍒", 83), ("🍋", 15), ("🍉", 1), ("⭐", 0.2), ("💎", 0.05), ("7️⃣", 0.02)],
        3: [("🍒", 80), ("🍋", 17), ("🍉", 2), ("⭐", 0.5), ("💎", 0.1), ("7️⃣", 0.03)],
        4: [("🍒", 78), ("🍋", 18), ("🍉", 2.5), ("⭐", 0.7), ("💎", 0.15), ("7️⃣", 0.05)],
        5: [("🍒", 75), ("🍋", 20), ("🍉", 3), ("⭐", 1), ("💎", 0.2), ("7️⃣", 0.08)],
        6: [("🍒", 72), ("🍋", 21), ("🍉", 4), ("⭐", 1.5), ("💎", 0.3), ("7️⃣", 0.1)],
    }.get(setting, [("🍒", 80), ("🍋", 17), ("🍉", 2), ("⭐", 0.5), ("💎", 0.1), ("7️⃣", 0.03)])


symbol_rate = {
    "🍒": 0.95,
    "🍋": 1.1,
    "🍉": 1.4,
    "⭐": 2.0,
    "💎": 3.5,
    "7️⃣": 8.0
}


def weighted_choice(table):
    pool = []
    for s, w in table:
        pool.extend([s] * int(w * 10))
    return random.choice(pool)


def generate_grid(setting):
    table = get_symbol_table(setting)
    return [[weighted_choice(table) for _ in range(3)] for _ in range(3)]


LINES = [
    (0,0,0),
    (1,1,1),
    (2,2,2),
    (0,1,2),
    (2,1,0),
    (0,1,0),
    (2,1,2),
    (0,2,1),
]


def calc_multiplier(grid):
    total = 0
    for a,b,c in LINES:
        if grid[a][0] == grid[b][1] == grid[c][2]:
            total += symbol_rate.get(grid[a][0], 1)
    return total


# =========================
# スロット実行
# =========================
def run_slot(user_id: str, bet: int):

    setting = get_setting()
    balance = get_money(user_id)

    if balance < bet:
        return None

    add_money(user_id, -bet)

    grid = generate_grid(setting)
    multiplier = calc_multiplier(grid)

    # =========================
    # EV（範囲対応）
    # =========================
    ev_min = float(get_setting("ev_min"))
    ev_max = float(get_setting("ev_max"))
    ev = random.uniform(ev_min, ev_max)
    # =========================

    mode = get_mode()

    variance = {
        "rang": 1.8,
        "fixg": 0.9
    }.get(mode, 1.0)

    win = int(bet * multiplier * ev * variance)

    add_money(user_id, win)

    new_balance = get_money(user_id)

    profit = win - bet

    text = "\n".join([" | ".join(r) for r in grid])
    sign = "+" if profit >= 0 else ""

    return (
        f"{text}\n"
        f"BET:{bet}\n"
        f"x{round(multiplier,2)}\n"
        f"{sign}{profit}\n"
        f"残高:{new_balance}"
    )


# =========================
# UI
# =========================
class SlotView(discord.ui.View):

    def __init__(self, user_id, bet):
        super().__init__()
        self.user_id = int(user_id)
        self.bet = bet

    @discord.ui.button(label="もう一回", style=discord.ButtonStyle.green)
    async def again(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("他人不可", ephemeral=True)

        result = run_slot(self.user_id, self.bet)
        await interaction.response.edit_message(content=result, view=self)

    @discord.ui.button(label="やめる", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.edit_message(content="終了", view=None)
        self.stop()


# =========================
# スロットコマンド
# =========================
@bot.tree.command(name="スロット")
async def slot_cmd(interaction: discord.Interaction, bet: int):

    user_id = str(interaction.user.id)

    await interaction.response.defer()

    if bet <= 0:
        return await interaction.followup.send("1以上")

    if get_money(user_id) < bet:
        return await interaction.followup.send("❌ 残高不足")

    result = run_slot(user_id, bet)

    if result is None:
        return await interaction.followup.send("❌ 残高不足")

    await interaction.followup.send(result, view=SlotView(user_id, bet))


# =========================
# EV確認
# =========================
@bot.tree.command(name="ev確認")
async def ev_view(interaction: discord.Interaction):

    if interaction.user.id not in ADMIN_IDS:
        return await interaction.response.send_message("❌ 管理者のみ", ephemeral=True)

    ev_min = get_setting("ev_min")
    ev_max = get_setting("ev_max")
    mode = get_mode()

    await interaction.response.send_message(
        f"🎰 EV: {ev_min} ~ {ev_max}\nMODE: {mode}"
    )


# =========================
# モード変更
# =========================
@bot.tree.command(name="モード変更")
async def mode_change(interaction: discord.Interaction, mode: str):

    if interaction.user.id not in ADMIN_IDS:
        return await interaction.response.send_message("❌ 管理者のみ", ephemeral=True)

    if mode not in ["rang", "fixg"]:
        return await interaction.response.send_message("rang / fixg のみ", ephemeral=True)

    set_mode(mode)

    await interaction.response.send_message(f"✅ モード変更: {mode}")


# =========================
# 起動
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("READY")


def run_bot():
    bot.run(TOKEN)


if __name__ == "__main__":
    Thread(target=run_web).start()
    run_bot()