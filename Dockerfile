# 基本となるイメージ
FROM python:3.9-slim

# 作業ディレクトリの設定
WORKDIR /app

# アプリケーションのコピー
COPY . /app/

# 必要なPythonライブラリのインストール
RUN pip install --no-cache-dir -r requirements.txt

# ボットを実行するために必要なコマンドを指定
CMD ["python", "reservation_bot.py"]