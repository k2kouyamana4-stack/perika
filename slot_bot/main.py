import sys
import os
import random
from threading import Thread
from flask import Flask

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import discord
from discord.ext import commands

from shared.db import get_money, add_money, get_setting, set_setting


# -----------------
# Flask（Render対策）
# -----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "alive"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# -----------------
# Bot
# -----------------
TOKEN = os.getenv("DISCORD_TOKEN")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

ADMIN_IDS = {947136029285048340, 1423839192391356496}


# -----------------
# スロット
# -----------------
def get_symbol_table(setting):
    tables = {
        1: [("🍒", 60), ("🍋", 30), ("🍉", 7), ("⭐", 2), ("💎", 0.5), ("7️⃣", 0.05)],
        2: [("🍒", 55), ("🍋", 30), ("🍉", 10), ("⭐", 3), ("💎", 0.8), ("7️⃣", 0.1)],
        3: [("🍒", 52), ("🍋", 32), ("🍉", 13), ("⭐", 2.5), ("💎", 1), ("7️⃣", 0.15)],
        4: [("🍒", 48), ("🍋", 30), ("🍉", 15), ("⭐", 4), ("💎", 1.5), ("7️⃣", 0.25)],
        5: [("🍒", 43), ("🍋", 28), ("🍉", 18), ("⭐", 6), ("💎", 3), ("7️⃣", 0.6)],
        6: [("🍒", 38), ("🍋", 25), ("🍉", 20), ("⭐", 9), ("💎", 5), ("7️⃣", 1.5)],
    }
    return tables.get(setting, tables[3])


symbol_rate = {
    "🍒": 1.05,
    "🍋": 1.3,
    "🍉": 1.9,
    "⭐": 3.2,
    "💎": 5.5,
    "7️⃣": 16
}


def weighted_choice(table):
    pool = []
    for s, w in table:
        pool.extend([s] * int(w * 10))
    return random.choice(pool)


def generate_grid(setting):
    table = get_symbol_table(setting)
    grid = [[weighted_choice(table) for _ in range(3)] for _ in range(3)]

    bonus_rate = {
        1: 0.010,
        2: 0.014,
        3: 0.030,
        4: 0.028,
        5: 0.038,
        6: 0.055
    }

    if random.random() < bonus_rate.get(setting, 0.02):
        s = weighted_choice(table)
        grid[1] = [s, s, s]

    return grid


def calc_multiplier(grid):
    line = grid[1]
    if line[0] == line[1] == line[2]:
        return symbol_rate.get(line[0], 1)
    return 1


# -----------------
# スロット本体（完全安定版）
# -----------------
def run_slot(user_id: str, bet: int):

    setting = int(get_setting())
    balance = get_money(user_id)

    if balance < bet:
        return "残高不足"

    # ★重要：先に引く
    add_money(user_id, -bet)

    grid = generate_grid(setting)
    multiplier = calc_multiplier(grid)

    win = int(bet * multiplier)

    # ★追加分だけ入れる
    add_money(user_id, win)

    new_balance = get_money(user_id)

    profit = win - bet

    text = "\n".join([" | ".join(row) for row in grid])
    sign = "+" if profit >= 0 else ""

    return (
        f"{text}\n"
        f"🎰 BET: {bet}\n"
        f"🎰 x{round(multiplier,2)}\n"
        f"💰 {sign}{profit}\n"
        f"🏦 {new_balance}"
    )


# -----------------
# UI
# -----------------
class SlotView(discord.ui.View):

    def __init__(self, user_id: str, bet: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.bet = bet

    @discord.ui.button(label="もう一回", style=discord.ButtonStyle.green)
    async def again(self, interaction: discord.Interaction, button: discord.ui.Button):

        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("他人は操作できない", ephemeral=True)

        result = run_slot(self.user_id, self.bet)
        await interaction.response.edit_message(content=result, view=self)

    @discord.ui.button(label="やめる", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="終了", view=None)
        self.stop()


# -----------------
# コマンド
# -----------------
@bot.tree.command(name="スロット")
async def slot_cmd(interaction: discord.Interaction, bet: int):

    user_id = str(interaction.user.id)

    await interaction.response.defer()

    if bet <= 0:
        return await interaction.followup.send("1以上")

    if get_money(user_id) < bet:
        return await interaction.followup.send("残高不足")

    result = run_slot(user_id, bet)

    await interaction.followup.send(result, view=SlotView(user_id, bet))


@bot.tree.command(name="設定変更")
async def set_slot(interaction: discord.Interaction, value: int):

    await interaction.response.defer(ephemeral=True)

    if interaction.user.id not in ADMIN_IDS:
        return await interaction.followup.send("権限なし")

    set_setting(value)
    await interaction.followup.send(f"設定: {value}")


@bot.tree.command(name="設定確認")
async def show_setting(interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=True)

    if interaction.user.id not in ADMIN_IDS:
        return await interaction.followup.send("権限なし")

    await interaction.followup.send(str(get_setting()))


# -----------------
# 起動
# -----------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("slot bot ready")


def run_bot():
    bot.run(TOKEN)


if __name__ == "__main__":
    Thread(target=run_web).start()
    run_bot()