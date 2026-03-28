import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import os
import discord
from discord import app_commands
from discord.ext import commands
import random
from flask import Flask
from threading import Thread

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


# -----------------
# スロット
# -----------------
def slot(user_id: str, bet: int):

    setting = get_setting()

    base_rates = {1:10, 2:15, 3:20, 4:30, 5:40, 6:55}
    jackpot_rates = {1:1, 2:2, 3:3, 4:5, 5:7, 6:10}

    roll = random.randint(1, 100)

    if roll <= jackpot_rates[setting]:
        add_money(user_id, bet * 10)
        return f"🎰✨JACKPOT +{bet*10}"

    elif roll <= base_rates[setting]:
        add_money(user_id, bet)
        return f"✨WIN +{bet}"

    else:
        add_money(user_id, -bet)
        return f"LOSE -{bet}"


# -----------------
# /スロット
# -----------------
@bot.tree.command(name="スロット")
async def slot_cmd(interaction: discord.Interaction, bet: int):

    user_id = str(interaction.user.id)

    if bet <= 0:
        await interaction.response.send_message("1以上", ephemeral=True)
        return

    if get_money(user_id) < bet:
        await interaction.response.send_message("残高不足", ephemeral=True)
        return

    result = slot(user_id, bet)
    await interaction.response.send_message(result)


# -----------------
# 設定
# -----------------
@bot.tree.command(name="設定変更")
async def set_slot(interaction: discord.Interaction, value: int):

    if interaction.user.id not in [947136029285048340, 1423839192391356496]:
        await interaction.response.send_message("権限なし", ephemeral=True)
        return

    set_setting(value)
    await interaction.response.send_message(f"設定: {value}")


@bot.tree.command(name="設定確認")
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