import sys
import os
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


# -----------------
# Bot
# -----------------
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

ADMIN_IDS = {947136029285048340, 1423839192391356496}


# -----------------
# 設定別確率
# -----------------
def get_symbol_table(setting):
    tables = {
        1: [("🍒", 60), ("🍋", 30), ("🍉", 7), ("⭐", 2), ("💎", 0.5), ("7️⃣", 0.05)],
        2: [("🍒", 55), ("🍋", 30), ("🍉", 10), ("⭐", 3), ("💎", 0.8), ("7️⃣", 0.1)],
        3: [("🍒", 52), ("🍋", 32), ("🍉", 13), ("⭐", 2.5), ("💎", 1), ("7️⃣", 0.15)],
        4: [("🍒", 48), ("🍋", 30), ("🍉", 15), ("⭐", 4), ("💎", 1.5), ("7️⃣", 0.25)],
        5: [("🍒", 43), ("🍋", 28), ("🍉", 18), ("⭐", 6), ("💎", 3), ("7️⃣", 0.6)],
        6: [("🍒", 38), ("🍋", 25), ("🍉", 20), ("⭐", 9), ("💎", 5), ("7️⃣", 1.5)],
    }
    return tables.get(setting, tables[3])


# -----------------
# 倍率
# -----------------
symbol_rate = {
    "🍒": 1.05,
    "🍋": 1.3,
    "🍉": 1.9,
    "⭐": 3.2,
    "💎": 5.5,
    "7️⃣": 16
}


# -----------------
# 抽選
# -----------------
def weighted_choice(table):
    pool = []
    for symbol, weight in table:
        pool.extend([symbol] * int(weight * 10))
    return random.choice(pool)


# -----------------
# 生成
# -----------------
def generate_grid(setting):
    table = get_symbol_table(setting)
    grid = [[weighted_choice(table) for _ in range(3)] for _ in range(3)]

    bonus_rate = {
        1: 0.010,
        2: 0.014,
        3: 0.030,
        4: 0.028,
        5: 0.038,
        6: 0.055
    }

    if random.random() < bonus_rate.get(setting, 0.02):
        symbol = weighted_choice(table)
        grid[1] = [symbol, symbol, symbol]

    return grid


# -----------------
# 倍率計算（修正版）
# -----------------
def calc_multiplier(grid):
    line = grid[1]

    if line[0] == line[1] == line[2]:
        return symbol_rate.get(line[0], 1)

    return 1


# -----------------
# スロット本体（修正版）
# -----------------
def slot(user_id: str, bet: int):

    setting = get_setting()

    try:
        setting = int(setting)
    except:
        setting = 3

    if setting not in [1,2,3,4,5,6]:
        setting = 3

    balance = get_money(user_id)

    if balance < bet:
        return "残高不足"

    grid = generate_grid(setting)
    multiplier = calc_multiplier(grid)

    win = int(bet * multiplier)

    profit = win - bet

    # 追加ペナルティ（任意要素）
    if profit < 0 and random.random() < 0.05:
        profit -= int(bet * 0.3)

    MAX_PROFIT = bet * 30
    if profit > MAX_PROFIT:
        profit = MAX_PROFIT

    add_money(user_id, profit)

    new_balance = get_money(user_id)

    text = "\n".join([" | ".join(row) for row in grid])
    sign = "+" if profit >= 0 else ""

    return (
        f"{text}\n"
        f"🎰 BET: {bet}ペリカ\n"
        f"🎰 x{round(multiplier,2)}\n"
        f"💰 {sign}{profit}ペリカ\n"
        f"🏦 残高: {new_balance}ペリカ"
    )


# -----------------
# UI
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
# コマンド（全部defer済み）
# -----------------
@bot.tree.command(name="スロット")
async def slot_cmd(interaction: discord.Interaction, bet: int):

    user_id = str(interaction.user.id)

    if bet <= 0:
        return await interaction.response.send_message("1以上", ephemeral=True)

    if get_money(user_id) < bet:
        return await interaction.response.send_message("残高不足", ephemeral=True)

    await interaction.response.defer()

    result = slot(user_id, bet)

    await interaction.followup.send(result, view=SlotView(user_id, bet))


@bot.tree.command(name="設定変更")
async def set_slot(interaction: discord.Interaction, value: int):

    await interaction.response.defer(ephemeral=True)

    if interaction.user.id not in ADMIN_IDS:
        return await interaction.followup.send("権限がありません")

    if value not in [1,2,3,4,5,6]:
        return await interaction.followup.send("1~6で選択してください")

    set_setting(value)
    await interaction.followup.send(f"設定: {value}")


@bot.tree.command(name="設定確認")
async def show_setting(interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=True)

    if interaction.user.id not in ADMIN_IDS:
        return await interaction.followup.send("権限がありません")

    await interaction.followup.send(f"{get_setting()}")


# -----------------
# テストスロット（修正版）
# -----------------
@bot.tree.command(name="テストスロット")
@app_commands.describe(bet="ベット額", times="回数（最大1000）")
async def test_slot(interaction: discord.Interaction, bet: int, times: int):

    if interaction.user.id not in ADMIN_IDS:
        return await interaction.response.send_message("権限がありません", ephemeral=True)

    await interaction.response.defer(ephemeral=True)

    total_profit = 0
    hit_count = 0

    setting = int(get_setting())

    for _ in range(times):
        grid = generate_grid(setting)
        multiplier = calc_multiplier(grid)

        win = int(bet * multiplier)

        if multiplier > 1:
            hit_count += 1

        profit = win - bet

        if profit < 0 and random.random() < 0.05:
            profit -= int(bet * 0.3)

        total_profit += profit

    avg = total_profit / times

    await interaction.followup.send(
        f"🎰 テスト結果\n"
        f"回数: {times}\n"
        f"BET: {bet}\n"
        f"設定: {setting}\n\n"
        f"総収支: {total_profit}ペリカ\n"
        f"平均: {round(avg,2)}ペリカ/回\n"
        f"当たり回数: {hit_count}回\n"
        f"当たり率: {round(hit_count/times*100,1)}%"
    )


# -----------------
# 起動
# -----------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("slot bot ready")


def run_bot():
    bot.run(TOKEN)


if __name__ == "__main__":
    Thread(target=run_web).start()
    run_bot()