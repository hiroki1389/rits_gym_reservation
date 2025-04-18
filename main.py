import os
import time
from datetime import datetime, timedelta
import pytz
import shutil

import discord
from discord.ext import commands
from discord.ui import Select as DiscordSelect, View

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.select import Select as SeleniumSelect
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc

import gspread
from google.oauth2.service_account import Credentials

from server import keep_alive

# Secretsから環境変数を取得
project_id = os.environ["GOOGLE_PROJECT_ID"]
private_key_id = os.environ["GOOGLE_PRIVATE_KEY_ID"]
private_key = os.environ["GOOGLE_PRIVATE_KEY"].replace("\\n", "\n")
client_email = os.environ["GOOGLE_CLIENT_EMAIL"]
client_id = os.environ["GOOGLE_CLIENT_ID"]

# 認証情報を作成
credentials_info = {
    "type": "service_account",
    "project_id": project_id,
    "private_key_id": private_key_id,
    "private_key": private_key,
    "client_email": client_email,
    "client_id": client_id,
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url":
    "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "your_client_x509_cert_url_here",
    "universe_domain": "googleapis.com"
}

# Google Sheets API 認証設定
USERS_SHEET_ID = os.environ["USERS_SHEET_ID"]
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

credentials = Credentials.from_service_account_info(credentials_info, scopes=SCOPE)
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
@bot.tree.command(name="setup", description="ユーザ情報の登録を行います")
async def setup(interaction: discord.Interaction, name: str, email: str, permit_id: int, faculty: str):
    user_id = interaction.user.id
    users_data = users.get_all_values()
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
@bot.tree.command(name="update", description="ユーザ情報を更新します")
async def update(interaction: discord.Interaction, name: str, email: str, permit_id: int, faculty: str):
    user_id = interaction.user.id
    users_data = users.get_all_values()
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
@bot.tree.command(name="delete", description="ユーザ情報を削除します")
async def delete(interaction: discord.Interaction):
    user_id = interaction.user.id
    users_data = users.get_all_values()
    line_num = check_user_registered(user_id, users_data)
    if line_num == -1:
        message = "あなたは登録されていません．"
    else:
        users.delete_rows(line_num)
        message = "ユーザー情報を削除しました．"
    await interaction.response.send_message(message)


# 予約コマンド
@bot.tree.command(name="reserve", description="予約します")
async def reserve(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    users_data = users.get_all_values()
    user_id = interaction.user.id
    line_num = check_user_registered(user_id, users_data)
    if line_num == -1:
        message = "あなたは登録されていません．"
        await interaction.followup.send(message)
        return

    # 予約ページ
    reservation_url = "https://select-type.com/rsv/?id=KatPteH9vEg"

    # Replit 環境ではパスを自動検索して指定
    chrome_path = shutil.which("chromium")
    chromedriver_path = shutil.which("chromedriver")

    options = Options()
    options.binary_location = chrome_path
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(reservation_url)

    #ジムの選択
    campus_num = "196393"  # OICの番号
    # campus_num_kic = "196390"# 気が向いたらKICとかもユーザに登録時にさせてもいいかも
    dropdown = driver.find_element(By.NAME, 'c_id')
    select_campus = SeleniumSelect(dropdown)
    select_campus.select_by_value(campus_num)

    # 今日の日付および年，月，7日後の日付を取得
    tokyo = pytz.timezone('Asia/Tokyo')
    today = datetime.now(tokyo).date()
    print(datetime.now(tokyo))
    current_month = today.month
    current_year = today.year
    seven_days_later = today + timedelta(days=7)

    # 共通の予約処理
    async def process_reservation(interaction: discord.Interaction, month_choice: str, driver):

        # 来月に切り替え
        if month_choice == "next":
            next_month = current_month + 1
            if next_month > 12:
                next_month = 1
                current_year += 1
            driver.execute_script("javascript:rsv.jumpNmCal();")

            # ページが変わるのを待つ
            time.sleep(1)  # なんかwebdriver上手くいかんからこれで一旦妥協
            # wait_month = WebDriverWait(driver, 10)
            # wait_month.until(EC.text_to_be_present_in_element( (By.CLASS_NAME, 'chg-text1 cl-display-date'), f'{current_year}年{next_month}月'))
            # wait_month.until(EC.presence_of_element_located((By.CLASS_NAME, 'chg-text1 cl-display-date')))

        #予約可能日の表示と選択
        element = driver.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div/div[2]/div[5]/table/tbody")
        tdlist = element.find_elements(By.TAG_NAME, 'td')
        day_options = []
        day_candidates = []
        index = 0
        message = "**予約可能日一覧**\n"
        for elem in tdlist:
            if '●' in elem.text:
                id_str = elem.find_elements(By.TAG_NAME, 'a')[0].get_attribute('id')  # 例: "2025-3-31_td_cls"
                ymd = id_str.replace('_td_cls', '')  # → "2025-3-31"
                date = ymd.replace('-', '/')  # "2025/3/31"
                # 日付を比較する
                date_obj = datetime.strptime(ymd, "%Y-%m-%d").date()  # 文字列を日付オブジェクトに変換

                # 今日から7日後の日付範囲内であれば表示
                if today <= date_obj <= seven_days_later:
                    message += f"{date}\n"
                    day_options.append(discord.SelectOption(label=f"{date}", value=str(index)))
                    day_candidates.append(elem)
                    index += 1
        # 予約可能日がなかったら終了
        if not day_options:
            await interaction.followup.send('予約可能日がありませんでした。')
            driver.quit()
            return

        message += "----------\n何日に予約しますか？"
        select_menu_day = DiscordSelect(placeholder="予約する日付を選んでください", options=day_options)

        # セレクトメニューの選択を受けて処理を行う
        async def select_callback_day(interaction: discord.Interaction):
            # セレクトボタンの無効化
            select_menu_day.disabled = True
            await interaction.message.edit(view=day_view)

            await interaction.response.defer(thinking=True)
            index = int(select_menu_day.values[0])
            day_candidates[index].click()
            date = day_candidates[index].find_elements(By.TAG_NAME, 'a')[0].get_attribute('id').replace('_td_cls', '').replace('-', '/')
            await interaction.user.send(f"あなたが選択したオプションは: {date} です")

            # 日付選択からHTMlが動的に変わるから，時刻一覧が表示されるまで最大10秒待つ
            wait_day = WebDriverWait(driver, 10)
            wait_day.until(EC.presence_of_element_located((By.CLASS_NAME, 'modal-body')))

            # 予約時間の表示
            element = driver.find_element(By.CLASS_NAME, 'modal-body')
            timeList = element.find_elements(By.TAG_NAME, 'a')
            time_options = []
            time_candidates = []
            index = 0
            message = "**予約可能時間一覧**\n"
            for elem in timeList:
                if '▲' in elem.text or '●' in elem.text:
                    text_lines = elem.text.strip().split(' ')
                    for part in text_lines:
                        if '～' in part:
                            time_part = part
                        elif '残り' in part:
                            seats_part = part
                    message += f"{time_part} {seats_part}枠\n"
                    time_options.append(
                        discord.SelectOption(label=f"{time_part}", value=str(index)))
                    time_candidates.append(elem)
                    index += 1

            # 予約可能日がなかったら終了
            if not time_options:
                await interaction.followup.send('予約可能時刻がありませんでした')
                driver.quit()
                return

            message += "----------\n何時に予約しますか？"
            select_menu_time = DiscordSelect(placeholder="予約する時刻を選んでください", options=time_options)

            async def select_callback_time(interaction: discord.Interaction):
                # セレクトボタンの無効化
                select_menu_time.disabled = True
                await interaction.message.edit(view=time_view)

                await interaction.response.defer(thinking=True)
                index = int(select_menu_time.values[0])
                time_candidates[index].click()
                text_lines = time_candidates[index].text.strip().split(' ')
                for part in text_lines:
                    if '～' in part:
                        time = part
                await interaction.user.send(f"あなたが選択したオプションは: {time} です")

                # 時刻選択からHTMlが動的に変わるから，日時kakunin画面が表示されるまで最大10秒待つ
                wait_time = WebDriverWait(driver, 10)
                wait_time.until(EC.presence_of_element_located((By.ID, 'rsvsltform_id')))

                #予約日時のkakunin（”次へ”ボタンはJavaScriptだからこれを実行する）
                driver.execute_script('javascript:rsv.setSelectedRsvSlot(1);')

                # kakunin選択からHTMlが動的に変わるから，予約フォームが表示されるまで最大10秒待つ
                wait_form = WebDriverWait(driver, 10)
                wait_form.until(EC.presence_of_element_located((By.XPATH, '/html/body/form/div/div/div/div/div[4]/div/div[1]')))

                #利用者情報の入力
                elements = driver.find_elements(By.CLASS_NAME, 'control-group')
                name = users.cell(line_num, 1).value
                email = users.cell(line_num, 2).value
                permit_id = users.cell(line_num, 3).value
                faculty = users.cell(line_num, 4).value
                user_infos = (name, email, email, permit_id, faculty)
                page_infos = ['name', 'email', 'email_conf', 'other', 'other2']
                index = 0
                for elem in elements:
                    form = elem.find_element(By.NAME, page_infos[index])
                    form.send_keys(user_infos[index])
                    if index == 1:
                        index += 1
                        form = elem.find_element(By.NAME, page_infos[index])
                        form.send_keys(user_infos[index])
                    index += 1
                driver.find_element(By.NAME, 'do_rsv').click()

                # フォーム入力からHTMlが動的に変わるから，kakunin画面が表示されるまで最大10秒待つ
                wait_confirm = WebDriverWait(driver, 10)
                wait_confirm.until(EC.element_to_be_clickable((By.XPATH, '//button[@id="ebtn_id"]')))

                # kakuninボタンを自動的に押す
                driver.find_element(By.XPATH, '/html/body/form/div/div/div/div/div[3]/button').click()

                try:
                    # 予約送信からHTMlが動的に変わるから，予約完了画面が表示されるまで最大20秒待つ
                    wait_final = WebDriverWait(driver, 20)
                    wait_final.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[1]')))

                    # 予約完了出力
                    reservations.append_row([str(user_id), date, time])
                    message = f"{date} {time} の予約を追加しました！"
                except TimeoutException:
                    message = 'エラー：予約完了画面が表示されませんでした．再度試してください'

                driver.quit()
                await interaction.followup.send(message)

            # セレクトメニューをビューに追加
            time_view = View()
            time_view.add_item(select_menu_time)

            # 予約一覧とセレクトメニューを送信
            await interaction.followup.send(message, view=time_view)
            select_menu_time.callback = select_callback_time

        # セレクトメニューをビューに追加
        day_view = View()
        day_view.add_item(select_menu_day)

        # 予約一覧とセレクトメニューを送信
        await interaction.followup.send(message, view=day_view)
        select_menu_day.callback = select_callback_day

    # 今日から7日後が来月かどうかをチェック
    if seven_days_later.month != current_month:
        message = f"今日は{today.strftime('%Y/%m/%d')}です。\n予約したいのは今月ですか，来月ですか？"
        month_options = [
            discord.SelectOption(label="今月", value="current"),
            discord.SelectOption(label="来月", value="next")
        ]
        # ユーザーに予約を選ばせるためのセレクトメニュー
        select_menu_month = DiscordSelect(placeholder="今月か来月か選んでください", options=month_options)

        # セレクトメニューの選択を受けて処理を行う
        async def select_callback_month(interaction: discord.Interaction):
            # セレクトボタンの無効化
            select_menu_month.disabled = True
            await interaction.message.edit(view=month_view)

            await interaction.response.defer(thinking=True)
            month_choice = str(select_menu_month.values[0])  # 選ばれた予約
            await interaction.user.send(f"あなたが選択したオプションは: {month_choice} です")
            await process_reservation(interaction, month_choice, driver)

        # セレクトメニューをビューに追加
        month_view = View()
        month_view.add_item(select_menu_month)

        # メッセージを送信
        await interaction.followup.send(message, view=month_view)
        select_menu_month.callback = select_callback_month

    else:
        await process_reservation(interaction, "current", driver)

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

# Webサーバの起動
keep_alive()

# ボットを起動
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
bot.run(DISCORD_BOT_TOKEN)