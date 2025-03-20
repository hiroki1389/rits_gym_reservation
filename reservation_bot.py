import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

import discord
from discord.ext import commands
from discord.ui import Select, View

import gspread
from google.oauth2.service_account import Credentials

# .envファイルの読み込み
load_dotenv()

# Google Sheets API 認証設定
USERS_SHEET_ID = os.getenv("USERS_SHEET_ID")
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Google Sheetsの認証
CREDENTIALS_FILE = "./credentials.json"
credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPE)
gc = gspread.authorize(credentials)
sh = gc.open_by_key(USERS_SHEET_ID)
users = sh.worksheet("Users")
reservations = sh.worksheet("Reservations")

# Discord Botの設定
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='', intents=intents)

# ユーザ登録のチェック
def check_user_registered(user_id, users_data):
    for i, row in enumerate(users_data[1:], start=2):
        if row[0] == str(user_id):
            return i
    return -1

# ユーザ登録コマンド
@bot.tree.command(name="setup", description="セットアップを行います")
async def setup(interaction: discord.Interaction, name: str, email: str, permit_id: int, faculty: str):
    users_data = users.get_all_values()
    user_id = interaction.user.id
    if check_user_registered(user_id, users_data) == -1:
        users.append_row([str(user_id), name, email, permit_id, faculty])
        message = f"登録が完了しました！\n\
                名前: {name}\n\
                メールアドレス: {email}\n\
                利用許可証番号: {permit_id}\n\
                学部: {faculty}"
    else:
        message = "あなたはすでに登録されています．"
    await interaction.response.send_message(message)

# ユーザ情報更新コマンド
@bot.tree.command(name="update", description="情報を更新します")
async def update(interaction: discord.Interaction, name: str, email: str, permit_id: int, faculty: str):
    users_data = users.get_all_values()
    user_id = interaction.user.id
    line_num = check_user_registered(user_id, users_data)
    if line_num == -1:
        message = "あなたは登録されていません．"
    else:
        users.update(f'B{line_num}:E{line_num}', [[name, email, permit_id, faculty]])
        message = f"ユーザー情報を更新しました！\n\
                名前: {name}\n\
                メールアドレス: {email}\n\
                利用許可証番号: {permit_id}\n\
                学部: {faculty}"

    await interaction.response.send_message(message)

# ユーザ情報削除コマンド
@bot.tree.command(name="delete", description="情報を削除します")
async def delete(interaction: discord.Interaction):
    users_data = users.get_all_values()
    user_id = interaction.user.id
    line_num = check_user_registered(user_id, users_data)
    if line_num == -1:
        message = "あなたは登録されていません．"
    else:
        users.delete_rows(line_num)
        message = "ユーザー情報を削除しました．"
    await interaction.response.send_message(message)

# 予約可能日時表示コマンド
@bot.tree.command(name="reserve", description="指定された日数分までで予約可能な日時を表示します")
async def reserve(interaction: discord.Interaction, day: int):
    users_data = users.get_all_values()
    user_id = interaction.user.id
    line_num = check_user_registered(user_id, users_data)
    if line_num == -1:
        message = "あなたは登録されていません．"
    else:
        reservation_candidates = []
        current_date = datetime.now().strftime("%m/%d/%Y")
        end_date = current_date + timedelta(days=day)

        #######
        ### 予約サイトをスクレイピングして予約可能日を全部取得する関数を実行
        ### if current_date <= reservation_date <= end_date:
        #######

        #######
        ### ユーザにセレクトメニューを表示する
        ### for i in reservation_candidates:
        #######

        #######
        ### ユーザの入力を受けて予約をHTTP通信で実行
        date = '8/9/2025'
        time = '13:00'
        name = reservations.cell(line_num, 1).value
        email = reservations.cell(line_num, 2).value
        permit_id = reservations.cell(line_num, 3).value
        faculty = reservations.cell(line_num, 4).value
        #######

        reservations.append_row([str(user_id), date, time])
        message = "予約を追加しました．"
    await interaction.response.send_message(message)

# 予約キャンセルコマンド
@bot.tree.command(name="cancel", description="任意の予約をキャンセルできます")
async def cancel(interaction: discord.Interaction):
    reservations_data = reservations.get_all_values()[1:]
    user_id = interaction.user.id 

    user_reservations = []
    current_date = datetime.now()
    for row in reservations_data:
        if row[0] == str(user_id):
            reservation_date = datetime.strptime(row[1], "%m/%d/%Y")
            if reservation_date >= current_date:
                user_reservations.append((row[1], row[2]))

    if not user_reservations:
        message = "現在，登録されている予約はありません．"
        await interaction.response.send_message(message)
        return

    # 予約一覧を表示するメッセージ
    message = "**あなたの予約一覧:**\n"
    options = []
    for i, (date, time) in enumerate(user_reservations, 1):
        message += f"{i}. {date} {time}\n"
        options.append(discord.SelectOption(label=f"{date} {time}", value=str(i - 1)))

    message += "どれを削除しますか？"

    # ユーザーに予約を選ばせるためのセレクトメニュー
    select = Select(placeholder="削除する予約を選んでください", options=options)

    # セレクトメニューの選択を受けて処理を行う
    async def select_callback(interaction: discord.Interaction):
        selected_option = select.values[0]  # 選ばれた予約
        reservation_to_delete = user_reservations[int(selected_option)]
        

        #######
        ### 選ばれた予約を元にHTTP通信で予約キャンセルを実行
        #######

        # 予約データの削除処理
        reservations_data = reservations.get_all_values()
        for i, row in enumerate(reservations_data):
            if row[0] == str(user_id) and row[1] == reservation_to_delete[0] and row[2] == reservation_to_delete[1]:
                # 予約を削除
                reservations.delete_rows(i+1)
                break

        await interaction.response.send_message(f"{reservation_to_delete[0]} {reservation_to_delete[1]} の予約をキャンセルしました。")

    # セレクトメニューをビューに追加
    view = View()
    view.add_item(select)
    
    # 予約一覧とセレクトメニューを送信
    await interaction.response.send_message(message, view=view)
    select.callback = select_callback

# ボットが起動した時に呼ばれるイベント
@bot.event
async def on_ready():
    print("on_readyが呼ばれました")
    try:
        print(f'ログインしました: {bot.user}')  # ログイン後のメッセージ
        # コマンドを同期する処理
        await bot.tree.sync()
        print("スラッシュコマンドを同期しました")
    except Exception as e:
        print(f"コマンド同期時にエラーが発生しました: {e}")

# ボットを起動
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(DISCORD_BOT_TOKEN)