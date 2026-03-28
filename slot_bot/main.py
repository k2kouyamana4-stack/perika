import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import discord
from discord import app_commands
from discord.ext import commands
import random

from config import TOKEN, ADMINS
from shared.db import get_money, add_money, get_setting, set_setting

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())


# -----------------
# スロット本体（ジャグラー風）
# -----------------
def slot(user_id: str, bet: int):

    setting = get_setting()

    # 設定が高いほど当たりやすい
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

    # ジャグラー風演出
    if roll <= jackpot_chance:
        add_money(user_id, bet * 10)
        return "🎰✨ペカッ！！ JACKPOT +{}ペリカ".format(bet * 10)

    elif roll <= win_chance:
        add_money(user_id, bet)
        return "✨ペカッ！ WIN +{}ペリカ".format(bet)

    else:
        add_money(user_id, -bet)
        return "ハズレ… -{}ペリカ".format(bet)


# -----------------
# /スロット
# -----------------
@bot.tree.command(name="スロット")
@app_commands.describe(bet="掛け金")
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
# /設定変更（管理者のみ）
# -----------------
@bot.tree.command(name="設定変更")
@app_commands.describe(value="1〜6")
async def set_slot(interaction: discord.Interaction, value: int):

    if interaction.user.id not in ADMINS:
        await interaction.response.send_message("権限なし", ephemeral=True)
        return

    if value < 1 or value > 6:
        await interaction.response.send_message("1〜6で指定", ephemeral=True)
        return

    set_setting(value)

    await interaction.response.send_message(f"設定を {value} に変更した")


# -----------------
# 現在設定確認
# -----------------
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