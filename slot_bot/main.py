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
# Flask（Web対応）
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

# -----------------
# スロット本体
# -----------------
def slot(user_id: str, bet: int):

    setting = get_setting()

    base_rates = {1:10, 2:15, 3:20, 4:30, 5:40, 6:55}
    jackpot_rates = {1:1, 2:2, 3:3, 4:5, 5:7, 6:10}

    roll = random.randint(1, 100)

    symbol = SYMBOLS.get(setting, "❓")

    if roll <= jackpot_rates[setting]:
        add_money(user_id, bet * 10)
        return f"{symbol}{symbol}{symbol} 🎰 JACKPOT +{bet*10}"

    elif roll <= base_rates[setting]:
        add_money(user_id, bet)
        return f"{symbol}{symbol}{symbol} ✨ WIN +{bet}"

    else:
        add_money(user_id, -bet)
        return f"{symbol}{symbol}{symbol} 💥 LOSE -{bet}"

# -----------------
# /スロット
# -----------------
@bot.tree.command(name="スロット", description="スロットを回す")
@app_commands.describe(bet="賭け金（1以上）")
async def slot_cmd(interaction: discord.Interaction, bet: int):

    user_id = str(interaction.user.id)

    if bet <= 0:
        await interaction.response.send_message("1以上にして", ephemeral=True)
        return

    if get_money(user_id) < bet:
        await interaction.response.send_message("残高不足", ephemeral=True)
        return

    result = slot(user_id, bet)
    balance = get_money(user_id)

    await interaction.response.send_message(f"{result}\n💰残高: {balance}")

# -----------------
# /スロット連続（連続回転）
# -----------------
@bot.tree.command(name="スロット連続", description="連続スロット（最大10回）")
@app_commands.describe(bet="1回の賭け金", times="回数（1〜10）")
async def auto_slot(interaction: discord.Interaction, bet: int, times: int):

    user_id = str(interaction.user.id)

    if bet <= 0:
        await interaction.response.send_message("1以上にして", ephemeral=True)
        return

    if times < 1 or times > 10:
        await interaction.response.send_message("回数は1〜10", ephemeral=True)
        return

    if get_money(user_id) < bet * times:
        await interaction.response.send_message("残高不足", ephemeral=True)
        return

    await interaction.response.send_message("🎰 回転開始...")

    logs = []

    for i in range(times):
        result = slot(user_id, bet)
        logs.append(f"{i+1}: {result}")
        await asyncio.sleep(1)

    await interaction.followup.send("\n".join(logs))

# -----------------
# 設定変更（管理者）
# -----------------
@bot.tree.command(name="slot_setting", description="スロット倍率設定変更（管理者用）")
async def set_slot(interaction: discord.Interaction, value: int):

    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("権限なし", ephemeral=True)
        return

    set_setting(value)
    await interaction.response.send_message(f"設定: {value}")

# -----------------
# 設定確認
# -----------------
@bot.tree.command(name="slot_setting_view", description="スロット設定確認")
async def show_setting(interaction: discord.Interaction):

    await interaction.response.send_message(f"現在: {get_setting()}")

# -----------------
# 起動
# -----------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("slot bot ready")

bot.run(TOKEN)