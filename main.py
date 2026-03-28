import discord
from discord import app_commands
from discord.ext import commands
import json

from config import TOKEN, ADMINS

# -----------------
# intents（重要）
# -----------------
intents = discord.Intents.default()
intents.members = True  # ← 全員配布に必須

bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------
# データ管理
# -----------------
def load_data():
    try:
        with open("money.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open("money.json", "w") as f:
        json.dump(data, f, indent=4)

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
@bot.tree.command(name="残高確認", description="自分の所持金を確認")
async def balance(interaction: discord.Interaction):
    data = load_data()
    user_id = str(interaction.user.id)

    if user_id not in data:
        data[user_id] = 0
        save_data(data)

    await interaction.response.send_message(
        f"所持金: {data[user_id]}ペリカ",
        ephemeral=True
    )

# -----------------
# /送金
# -----------------
@bot.tree.command(name="送金", description="他の人にお金を送る")
@app_commands.describe(member="送る相手", amount="金額")
async def pay(interaction: discord.Interaction, member: discord.Member, amount: int):

    data = load_data()
    user1 = str(interaction.user.id)
    user2 = str(member.id)

    if user1 not in data:
        data[user1] = 0
    if user2 not in data:
        data[user2] = 0

    if amount <= 0:
        await interaction.response.send_message("金額は1以上にして", ephemeral=True)
        return

    if data[user1] < amount:
        await interaction.response.send_message("ペリカ足りない", ephemeral=True)
        return

    data[user1] -= amount
    data[user2] += amount
    save_data(data)

    await interaction.response.send_message(
        f"{member.mention} に {amount}ペリカ送金した"
    )

# -----------------
# /増減（管理者）
# -----------------
@bot.tree.command(name="増減", description="ペリカを増減する（管理者のみ）")
@app_commands.describe(member="対象ユーザー", amount="増減値")
async def adjust(interaction: discord.Interaction, member: discord.Member, amount: int):

    if interaction.user.id not in ADMINS:
        await interaction.response.send_message("権限がありません", ephemeral=True)
        return

    data = load_data()
    user_id = str(member.id)

    if user_id not in data:
        data[user_id] = 0

    data[user_id] += amount

    if data[user_id] < 0:
        data[user_id] = 0

    save_data(data)

    if amount >= 0:
        msg = f"{member.mention} に {amount}ペリカ追加した"
    else:
        msg = f"{member.mention} から {-amount}ペリカ減らした"

    await interaction.response.send_message(msg)

# -----------------
# /ランキング
# -----------------
@bot.tree.command(name="ランキング", description="所持ペリカランキング")
async def ranking(interaction: discord.Interaction):

    data = load_data()

    if not data:
        await interaction.response.send_message("データなし")
        return

    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)

    msg = "💰 所持ペリカランキング 💰\n"

    for i, (user_id, money) in enumerate(sorted_data, start=1):
        try:
            user = await bot.fetch_user(int(user_id))
            name = user.name
        except:
            name = "不明ユーザー"

        msg += f"{i}位: {name} - {money}ペリカ\n"

    await interaction.response.send_message(msg)

# -----------------
# /全員配布（サーバー全員）
# -----------------
@bot.tree.command(name="全員配布", description="サーバー全員にペリカを配る（管理者のみ）")
@app_commands.describe(amount="配る金額")
async def distribute(interaction: discord.Interaction, amount: int):

    if interaction.user.id not in ADMINS:
        await interaction.response.send_message("権限がありません", ephemeral=True)
        return

    if amount <= 0:
        await interaction.response.send_message("1以上にして", ephemeral=True)
        return

    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("サーバーで実行して", ephemeral=True)
        return

    data = load_data()
    count = 0

    for member in guild.members:
        if member.bot:
            continue

        user_id = str(member.id)

        if user_id not in data:
            data[user_id] = 0

        data[user_id] += amount
        count += 1

    save_data(data)

    await interaction.response.send_message(
        f"{count}人に {amount}ペリカ配布した"
    )
# -----------------
# 起動（keep alive）
# -----------------
bot.run(TOKEN)
