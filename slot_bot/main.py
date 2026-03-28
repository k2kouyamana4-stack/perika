import sys
import os
import discord
from discord import app_commands
from discord.ext import commands
import random
from threading import Thread

from config import TOKEN, ADMINS
from shared.db import get_money, add_money, get_setting, set_setting

# -----------------
# Flask（Render Web対応）
# -----------------
from flask import Flask

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
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# -----------------
# スロット本体
# -----------------
def slot(user_id: str, bet: int):

    setting = get_setting()

    base_rates = {
        1: 10,
        2: 15,
        3: 20,
        4: 30,
        5: 40,
        6: 55
    }

    jackpot_rates = {
        1: 1,
        2: 2,
        3: 3,
        4: 5,
        5: 7,
        6: 10
    }

    win_chance = base_rates[setting]
    jackpot_chance = jackpot_rates[setting]

    roll = random.randint(1, 100)

    if roll <= jackpot_chance:
        add_money(user_id, bet * 10)
        return f"🎰✨ペカッ！！ JACKPOT +{bet * 10}ペリカ"

    elif roll <= win_chance:
        add_money(user_id, bet)
        return f"✨ペカッ！ WIN +{bet}ペリカ"

    else:
        add_money(user_id, -bet)
        return f"ハズレ… -{bet}ペリカ"


# -----------------
# /スロット
# -----------------
@bot.tree.command(name="スロット")
async def slot_cmd(interaction: discord.Interaction, bet: int):

    user_id = str(interaction.user.id)

    if bet <= 0:
        await interaction.response.send_message("1以上にして", ephemeral=True)
        return

    if get_money(user_id) < bet:
        await interaction.response.send_message("残高不足", ephemeral=True)
        return

    result = slot(user_id, bet)

    await interaction.response.send_message(result)


# -----------------
# 管理者設定
# -----------------
@bot.tree.command(name="設定変更")
async def set_slot(interaction: discord.Interaction, value: int):

    if interaction.user.id not in ADMINS:
        await interaction.response.send_message("権限なし", ephemeral=True)
        return

    if value < 1 or value > 6:
        await interaction.response.send_message("1〜6で指定", ephemeral=True)
        return

    set_setting(value)
    await interaction.response.send_message(f"設定を {value} に変更した")


@bot.tree.command(name="設定確認")
async def show_setting(interaction: discord.Interaction):

    setting = get_setting()
    await interaction.response.send_message(f"現在の設定: {setting}")


# -----------------
# 起動
# -----------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("スロットbot起動")


bot.run(TOKEN)