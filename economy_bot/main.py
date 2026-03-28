import discord
from discord import app_commands
from discord.ext import commands

from flask import Flask
from threading import Thread

import asyncio
from datetime import datetime

from config import TOKEN
from shared.db import get_money, add_money, get_ranking


# -----------------
# Flask（Render対策）
# -----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive"

def run_web():
    app.run(host="0.0.0.0", port=10000)

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
# 起動
# -----------------
bot.run(TOKEN)