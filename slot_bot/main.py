import sys
import os
import asyncio
import random
from threading import Thread
from flask import Flask

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import discord
from discord import app_commands
from discord.ext import commands

from shared.db import get_money, add_money, get_setting, set_setting


# -----------------
# Flask
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

ADMIN_IDS = {947136029285048340, 1423839192391356496}


# -----------------
# 🎰 設定別確率
# -----------------
def get_symbol_table(setting):

    tables = {
        1: [("🍒", 55), ("🍋", 30), ("🍉", 10), ("⭐", 3), ("💎", 1.5), ("7️⃣", 0.1)],
        2: [("🍒", 50), ("🍋", 30), ("🍉", 15), ("⭐", 3.5), ("💎", 1.3), ("7️⃣", 0.2)],
        3: [("🍒", 45), ("🍋", 30), ("🍉", 18), ("⭐", 5), ("💎", 1.8), ("7️⃣", 0.3)],
        4: [("🍒", 42), ("🍋", 28), ("🍉", 20), ("⭐", 6), ("💎", 2.5), ("7️⃣", 0.5)],
        5: [("🍒", 38), ("🍋", 26), ("🍉", 20), ("⭐", 8), ("💎", 5), ("7️⃣", 1)],
        6: [("🍒", 35), ("🍋", 25), ("🍉", 20), ("⭐", 10), ("💎", 7), ("7️⃣", 2)],
    }

    return tables.get(setting, tables[3])


# -----------------
# 🎰 倍率（弱体化済み）
# -----------------
symbol_rate = {
    "🍒": 1.3,
    "🍋": 1.8,
    "🍉": 2.5,
    "⭐": 5,
    "💎": 10,
    "7️⃣": 25
}


# -----------------
# 抽選
# -----------------
def weighted_choice(table):
    pool = []
    for symbol, weight in table:
        pool.extend([symbol] * int(weight * 10))
    return random.choice(pool)


# -----------------
# 生成（演出弱体化）
# -----------------
def generate_grid(setting):

    table = get_symbol_table(setting)

    grid = [[weighted_choice(table) for _ in range(3)] for _ in range(3)]

    bonus_rate = {
        1: 0.03,
        2: 0.05,
        3: 0.08,
        4: 0.10,
        5: 0.13,
        6: 0.18
    }

    if random.random() < bonus_rate.get(setting, 0.08):
        symbol = weighted_choice(table)
        row = random.randint(0, 2)
        grid[row] = [symbol, symbol, symbol]

    return grid


# -----------------
# 倍率計算
# -----------------
def calc_multiplier(grid):

    lines = [
        [grid[0][0], grid[0][1], grid[0][2]],
        [grid[1][0], grid[1][1], grid[1][2]],
        [grid[2][0], grid[2][1], grid[2][2]],

        [grid[0][0], grid[1][0], grid[2][0]],
        [grid[0][1], grid[1][1], grid[2][1]],
        [grid[0][2], grid[1][2], grid[2][2]],

        [grid[0][0], grid[1][1], grid[2][2]],
        [grid[0][2], grid[1][1], grid[2][0]],
    ]

    score = 0

    for line in lines:
        if line[0] == line[1] == line[2]:
            score += symbol_rate.get(line[0], 1)

    return max(1, round(score, 2))


# -----------------
# スロット本体
# -----------------
def slot(user_id: str, bet: int):

    setting = get_setting()

    try:
        setting = int(setting)
    except:
        setting = 3

    if setting not in [1,2,3,4,5,6]:
        setting = 3

    add_money(user_id, -bet)

    grid = generate_grid(setting)
    multiplier = calc_multiplier(grid)

    win = int(bet * multiplier)

    # ハズレ
    if multiplier == 1:
        win = 0

    profit = win - bet

    # ★ 追い打ち（負け強化）
    if profit < 0 and random.random() < 0.05:
        extra_loss = int(bet * 0.5)
        profit -= extra_loss

    # 上限
    MAX_PROFIT = bet * 50
    if profit > MAX_PROFIT:
        profit = MAX_PROFIT
        win = bet + profit

    add_money(user_id, win + (profit - (win - bet)))  # 補正込み

    balance = get_money(user_id)

    text = "\n".join([" | ".join(row) for row in grid])

    sign = "+" if profit >= 0 else ""

    return (
        f"{text}\n"
        f"🎰 BET: {bet}ペリカ\n"
        f"⚙️ 設定: {setting}\n"
        f"🎰 x{multiplier}\n"
        f"💰 {sign}{profit}ペリカ\n"
        f"🏦 残高: {balance}ペリカ"
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

        result = slot(self.user_id, self.bet)
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

    if bet <= 0:
        return await interaction.response.send_message("1以上", ephemeral=True)

    if get_money(user_id) < bet:
        return await interaction.response.send_message("残高不足", ephemeral=True)

    result = slot(user_id, bet)

    await interaction.response.send_message(result, view=SlotView(user_id, bet))


@bot.tree.command(name="設定変更")
async def set_slot(interaction: discord.Interaction, value: int):

    if interaction.user.id not in ADMIN_IDS:
        return await interaction.response.send_message("権限がありません", ephemeral=True)

    if value not in [1,2,3,4,5,6]:
        return await interaction.response.send_message("1~6で選択してください", ephemeral=True)

    set_setting(value)
    await interaction.response.send_message(f"設定: {value}")


@bot.tree.command(name="設定確認")
async def show_setting(interaction: discord.Interaction):

    if interaction.user.id not in ADMIN_IDS:
        return await interaction.response.send_message("権限がありません", ephemeral=True)

    await interaction.response.send_message(f"{get_setting()}", ephemeral=True)


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