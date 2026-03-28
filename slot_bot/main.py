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

Thread(target=run_web).start()

# -----------------
# Bot
# -----------------
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

ADMIN_IDS = {947136029285048340, 1423839192391356496}

# -----------------
# 絵柄
# -----------------
SYMBOLS = {
    1: "🍒",
    2: "🍋",
    3: "🍉",
    4: "⭐",
    5: "💎",
    6: "7️⃣"
}

ALL_SYMBOLS = list(SYMBOLS.values())

# -----------------
# 3×3生成
# -----------------
def generate_grid():
    return [[random.choice(ALL_SYMBOLS) for _ in range(3)] for _ in range(3)]

# -----------------
# 8ライン判定
# -----------------
def calc_multiplier(grid):

    lines = [
        # 横
        [grid[0][0], grid[0][1], grid[0][2]],
        [grid[1][0], grid[1][1], grid[1][2]],
        [grid[2][0], grid[2][1], grid[2][2]],

        # 縦
        [grid[0][0], grid[1][0], grid[2][0]],
        [grid[0][1], grid[1][1], grid[2][1]],
        [grid[0][2], grid[1][2], grid[2][2]],

        # 斜め
        [grid[0][0], grid[1][1], grid[2][2]],
        [grid[0][2], grid[1][1], grid[2][0]],
    ]

    symbol_rate = {
        "🍒": 2,
        "🍋": 3,
        "🍉": 5,
        "⭐": 8,
        "💎": 15,
        "7️⃣": 30
    }

    score = 0

    for line in lines:
        if line[0] == line[1] == line[2]:
            symbol = line[0]
            score += symbol_rate.get(symbol, 1)

    return max(1, score)

# -----------------
# スロット本体
# -----------------
def slot(user_id: str, bet: int):

    setting = get_setting()

    if setting not in SYMBOLS:
        return "1~6で選択してください"

    grid = generate_grid()

    multiplier = calc_multiplier(grid)

    add_money(user_id, bet * (multiplier - 1))

    text = "\n".join([" | ".join(row) for row in grid])

    return f"{text}\n🎰 x{multiplier}"

# -----------------
# ボタン付きスロット
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
# /スロット
# -----------------
@bot.tree.command(name="スロット", description="スロット")
async def slot_cmd(interaction: discord.Interaction, bet: int):

    user_id = str(interaction.user.id)

    if bet <= 0:
        return await interaction.response.send_message("1以上", ephemeral=True)

    if get_money(user_id) < bet:
        return await interaction.response.send_message("残高不足", ephemeral=True)

    result = slot(user_id, bet)

    await interaction.response.send_message(
        result,
        view=SlotView(user_id, bet)
    )

# -----------------
# /連続スロット
# -----------------
@bot.tree.command(name="連続スロット", description="連続スロット")
async def auto_slot(interaction: discord.Interaction, bet: int, times: int):

    user_id = str(interaction.user.id)

    if times < 1 or times > 10:
        return await interaction.response.send_message("1~10", ephemeral=True)

    if get_money(user_id) < bet * times:
        return await interaction.response.send_message("残高不足", ephemeral=True)

    logs = []

    for i in range(times):
        logs.append(slot(user_id, bet))

    await interaction.response.send_message("\n\n".join(logs))

# -----------------
# 設定変更
# -----------------
@bot.tree.command(name="設定変更", description="設定変更")
async def set_slot(interaction: discord.Interaction, value: int):

    if value not in [1,2,3,4,5,6]:
        return await interaction.response.send_message("1~6で選択してください", ephemeral=True)

    set_setting(value)
    await interaction.response.send_message(f"設定: {value}")

# -----------------
# 設定確認
# -----------------
@bot.tree.command(name="設定確認w")
async def show_setting(interaction: discord.Interaction):

    await interaction.response.send_message(f"{get_setting()}")

# -----------------
# 起動
# -----------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("slot bot ready")

bot.run(TOKEN)