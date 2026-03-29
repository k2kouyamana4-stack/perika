import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import discord
from discord import app_commands
from discord.ext import commands

from flask import Flask
from threading import Thread

import asyncio
from datetime import datetime

from config import TOKEN, ADMINS
from shared.db import get_money, add_money, get_ranking


# -----------------
# Flask（Render対策）
# -----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_web).start()


# -----------------
# Discord Bot
# -----------------
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# -----------------
# 起動時
# -----------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"ログイン: {bot.user}")


# -----------------
# /残高確認
# -----------------
@bot.tree.command(name="残高確認")
async def balance(interaction: discord.Interaction):
    money = get_money(str(interaction.user.id))

    await interaction.response.send_message(
        f"所持金: {money}ペリカ",
        ephemeral=True
    )


# -----------------
# /送金
# -----------------
@bot.tree.command(name="送金")
@app_commands.describe(member="相手", amount="金額")
async def pay(interaction: discord.Interaction, member: discord.Member, amount: int):

    if amount <= 0:
        await interaction.response.send_message("1以上にして", ephemeral=True)
        return

    sender = str(interaction.user.id)
    target = str(member.id)

    if get_money(sender) < amount:
        await interaction.response.send_message("ペリカ足りない", ephemeral=True)
        return

    add_money(sender, -amount)
    add_money(target, amount)

    await interaction.response.send_message(
        f"{member.mention} に {amount}ペリカ送金した"
    )


# -----------------
# /ランキング
# -----------------
@bot.tree.command(name="ランキング")
async def ranking(interaction: discord.Interaction):

    data = get_ranking()

    msg = "💰ランキング💰\n"

    for i, (user_id, money) in enumerate(data, start=1):
        try:
            user = await bot.fetch_user(int(user_id))
            name = user.name
        except:
            name = "不明"

        msg += f"{i}位: {name} - {money}ペリカ\n"

    await interaction.response.send_message(msg)


# -----------------
# /管理残高（管理者のみ）
# -----------------
@bot.tree.command(name="管理残高")
@app_commands.describe(member="対象ユーザー")
async def admin_balance(interaction: discord.Interaction, member: discord.Member):

    if interaction.user.id not in ADMINS:
        await interaction.response.send_message("権限がありません", ephemeral=True)
        return

    money = get_money(str(member.id))

    await interaction.response.send_message(
        f"{member.mention} の残高: {money}ペリカ",
        ephemeral=True
    )


# -----------------
# /管理調整（増減コマンド）
# -----------------
@bot.tree.command(name="管理調整")
@app_commands.describe(
    member="対象ユーザー",
    amount="増減金額（マイナスで減少）"
)
async def admin_adjust(interaction: discord.Interaction, member: discord.Member, amount: int):

    if interaction.user.id not in ADMINS:
        await interaction.response.send_message("権限がありません", ephemeral=True)
        return

    target = str(member.id)
    add_money(target, amount)

    result = "増加" if amount >= 0 else "減少"

    await interaction.response.send_message(
        f"{member.mention} の残高を {amount}ペリカ（{result}）調整しました",
        ephemeral=True
    )


# -----------------
# /全残高一覧（管理者のみ）
# -----------------
@bot.tree.command(name="全残高一覧")
async def all_balance(interaction: discord.Interaction):

    if interaction.user.id not in ADMINS:
        await interaction.response.send_message("権限がありません", ephemeral=True)
        return

    data = get_ranking()

    if not data:
        await interaction.response.send_message("データがありません", ephemeral=True)
        return

    msg = "💰全ユーザー残高一覧💰\n"

    for i, (user_id, money) in enumerate(data, start=1):
        try:
            user = await bot.fetch_user(int(user_id))
            name = user.name
        except:
            name = "不明"

        msg += f"{i}. {name} - {money}ペリカ\n"

    await interaction.response.send_message(msg, ephemeral=True)


# -----------------
# 起動
# -----------------
bot.run(TOKEN)