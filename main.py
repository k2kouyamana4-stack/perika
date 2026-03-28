import discord
from discord import app_commands
from discord.ext import commands

from config import TOKEN, ADMINS
from db import init_db, get_money, add_money, get_ranking

# -----------------
# intents
# -----------------
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------
# 起動時
# -----------------
@bot.event
async def on_ready():
    init_db()
    await bot.tree.sync()
    print(f"ログイン: {bot.user}")

# -----------------
# /残高確認
# -----------------
@bot.tree.command(name="残高確認", description="自分の所持金を確認")
async def balance(interaction: discord.Interaction):

    money = get_money(str(interaction.user.id))

    await interaction.response.send_message(
        f"所持金: {money}ペリカ",
        ephemeral=True
    )

# -----------------
# /送金
# -----------------
@bot.tree.command(name="送金", description="他の人に送金")
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
# /増減（管理者）
# -----------------
@bot.tree.command(name="増減", description="管理者用")
@app_commands.describe(member="対象", amount="増減")
async def adjust(interaction: discord.Interaction, member: discord.Member, amount: int):

    if interaction.user.id not in ADMINS:
        await interaction.response.send_message("権限なし", ephemeral=True)
        return

    add_money(str(member.id), amount)

    await interaction.response.send_message(
        f"{member.mention} に {amount}ペリカ変更"
    )

# -----------------
# /ランキング
# -----------------
@bot.tree.command(name="ランキング", description="ランキング表示")
async def ranking(interaction: discord.Interaction):

    data = get_ranking()

    if not data:
        await interaction.response.send_message("データなし")
        return

    msg = "💰 所持金ランキング 💰\n"

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
