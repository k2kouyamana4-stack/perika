import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import discord
from discord import app_commands
from discord.ext import commands

from flask import Flask
from threading import Thread

from config import TOKEN, ADMINS
from shared.db import get_money, add_money


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
# ページUI（全員版）
# -----------------
class BalanceView(discord.ui.View):

    def __init__(self, members, author_id):
        super().__init__(timeout=120)
        self.members = members
        self.author_id = author_id
        self.page = 0
        self.per_page = 10

    def get_page_content(self):

        start = self.page * self.per_page
        end = start + self.per_page
        chunk = self.members[start:end]

        max_page = (len(self.members) - 1) // self.per_page + 1

        msg = f"💰全ユーザー残高一覧（{self.page+1}/{max_page}ページ）💰\n\n"

        for i, member in enumerate(chunk, start=start+1):
            money = get_money(str(member.id))
            msg += f"{i}. {member.mention} - {money}ペリカ\n"

        return msg

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.author_id

    @discord.ui.button(label="←", style=discord.ButtonStyle.gray)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.page > 0:
            self.page -= 1

        await interaction.response.edit_message(
            content=self.get_page_content(),
            view=self
        )

    @discord.ui.button(label="→", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):

        max_page = (len(self.members) - 1) // self.per_page

        if self.page < max_page:
            self.page += 1

        await interaction.response.edit_message(
            content=self.get_page_content(),
            view=self
        )


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
        return await interaction.response.send_message("1以上にして", ephemeral=True)

    sender = str(interaction.user.id)
    target = str(member.id)

    if get_money(sender) < amount:
        return await interaction.response.send_message("ペリカ足りない", ephemeral=True)

    add_money(sender, -amount)
    add_money(target, amount)

    await interaction.response.send_message(
        f"{member.mention} に {amount}ペリカ送金した"
    )


# -----------------
# /ランキング（DB版）
# -----------------
@bot.tree.command(name="ランキング")
async def ranking(interaction: discord.Interaction):

    data = sorted(
        [(m.id, get_money(str(m.id))) for m in interaction.guild.members if not m.bot],
        key=lambda x: x[1],
        reverse=True
    )

    msg = "💰ランキング💰\n"

    for i, (user_id, money) in enumerate(data[:10], start=1):
        try:
            user = await bot.fetch_user(user_id)
            name = user.name
        except:
            name = "不明"

        msg += f"{i}位: {name} - {money}ペリカ\n"

    await interaction.response.send_message(msg)


# -----------------
# /管理残高
# -----------------
@bot.tree.command(name="管理残高")
async def admin_balance(interaction: discord.Interaction, member: discord.Member):

    if interaction.user.id not in ADMINS:
        return await interaction.response.send_message("権限がありません", ephemeral=True)

    money = get_money(str(member.id))

    await interaction.response.send_message(
        f"{member.mention} の残高: {money}ペリカ",
        ephemeral=True
    )


# -----------------
# /管理調整
# -----------------
@bot.tree.command(name="管理調整")
async def admin_adjust(interaction: discord.Interaction, member: discord.Member, amount: int):

    if interaction.user.id not in ADMINS:
        return await interaction.response.send_message("権限がありません", ephemeral=True)

    add_money(str(member.id), amount)

    result = "増加" if amount >= 0 else "減少"

    await interaction.response.send_message(
        f"{member.mention} の残高を {amount}ペリカ（{result}）調整しました",
        ephemeral=True
    )


# -----------------
# /全残高一覧（完全全員版）
# -----------------
@bot.tree.command(name="全残高一覧")
async def all_balance(interaction: discord.Interaction):

    if interaction.user.id not in ADMINS:
        return await interaction.response.send_message("権限がありません", ephemeral=True)

    guild = interaction.guild
    if guild is None:
        return await interaction.response.send_message("サーバー内で実行してください", ephemeral=True)

    members = [m for m in guild.members if not m.bot]

    view = BalanceView(members, interaction.user.id)

    await interaction.response.send_message(
        view.get_page_content(),
        view=view,
        ephemeral=True
    )


# -----------------
# /全員増減（完全全員）
# -----------------
@bot.tree.command(name="全員増減")
async def all_adjust(interaction: discord.Interaction, amount: int):

    if interaction.user.id not in ADMINS:
        return await interaction.response.send_message("権限がありません", ephemeral=True)

    guild = interaction.guild
    if guild is None:
        return await interaction.response.send_message("サーバー内で実行してください", ephemeral=True)

    count = 0

    for member in guild.members:
        if member.bot:
            continue

        add_money(str(member.id), amount)
        count += 1

    sign = "+" if amount >= 0 else ""

    await interaction.response.send_message(
        f"全員に {sign}{amount}ペリカ\n対象: {count}人",
        ephemeral=True
    )


# -----------------
# /全員リセット（完全版）
# -----------------
@bot.tree.command(name="全員リセット")
async def all_reset(interaction: discord.Interaction):

    if interaction.user.id not in ADMINS:
        return await interaction.response.send_message("権限がありません", ephemeral=True)

    guild = interaction.guild
    if guild is None:
        return await interaction.response.send_message("サーバー内で実行してください", ephemeral=True)

    count = 0

    for member in guild.members:
        if member.bot:
            continue

        money = get_money(str(member.id))
        add_money(str(member.id), -money)
        count += 1

    await interaction.response.send_message(
        f"全員の残高を0にしました\n対象: {count}人",
        ephemeral=True
    )


# -----------------
# 起動
# -----------------
bot.run(TOKEN)