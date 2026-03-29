import sys
import os
import random
from threading import Thread
from flask import Flask
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import discord
from discord.ext import commands

from shared.db import get_money, add_money, get_setting


# -----------------
# ログ設定（Render安定）
# -----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------
# Flask（Render用）
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

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# -----------------
# スロット設定
# -----------------
def get_symbol_table(setting):
    return {
        1: [("🍒", 60), ("🍋", 30), ("🍉", 7), ("⭐", 2)],
        2: [("🍒", 55), ("🍋", 30), ("🍉", 10), ("⭐", 3)],
        3: [("🍒", 52), ("🍋", 32), ("🍉", 13), ("⭐", 2.5)],
        4: [("🍒", 48), ("🍋", 30), ("🍉", 15), ("⭐", 4)],
        5: [("🍒", 43), ("🍋", 28), ("🍉", 18), ("⭐", 6)],
        6: [("🍒", 38), ("🍋", 25), ("🍉", 20), ("⭐", 9)],
    }.get(setting, [("🍒", 52), ("🍋", 32), ("🍉", 13), ("⭐", 2.5)])


symbol_rate = {
    "🍒": 1.1,
    "🍋": 1.3,
    "🍉": 1.8,
    "⭐": 3.0
}


def weighted_choice(table):
    pool = []
    for s, w in table:
        pool.extend([s] * int(w * 10))
    return random.choice(pool)


def generate_grid(setting):
    table = get_symbol_table(setting)
    return [[weighted_choice(table) for _ in range(3)] for _ in range(3)]


def calc_multiplier(grid):
    line = grid[1]
    if line[0] == line[1] == line[2]:
        return symbol_rate.get(line[0], 1)
    return 1


# -----------------
# スロット本体（修正版）
# -----------------
def run_slot(user_id: str, bet: int):

    setting = int(get_setting())
    balance = get_money(user_id)

    logger.info(f"BEFORE: {balance}")

    if balance < bet:
        return "残高不足"

    grid = generate_grid(setting)
    multiplier = calc_multiplier(grid)

    win = int(bet * multiplier)

    # ★重要修正：1回で更新（バグ防止）
    profit = win - bet
    add_money(user_id, profit)

    new_balance = get_money(user_id)

    logger.info(f"AFTER: {new_balance}")

    text = "\n".join([" | ".join(r) for r in grid])
    sign = "+" if profit >= 0 else ""

    return (
        f"{text}\n"
        f"BET:{bet}\n"
        f"x{round(multiplier,2)}\n"
        f"{sign}{profit}\n"
        f"残高:{new_balance}"
    )


# -----------------
# UI
# -----------------
class SlotView(discord.ui.View):

    def __init__(self, user_id, bet):
        super().__init__()
        self.user_id = user_id
        self.bet = bet

    @discord.ui.button(label="もう一回", style=discord.ButtonStyle.green)
    async def again(self, interaction: discord.Interaction, button: discord.ui.Button):

        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("他人不可", ephemeral=True)

        result = run_slot(self.user_id, self.bet)
        await interaction.response.edit_message(content=result, view=self)


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


# -----------------
# 起動
# -----------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("READY")


def run_bot():
    bot.run(TOKEN)


if __name__ == "__main__":
    Thread(target=run_web).start()
    run_bot()