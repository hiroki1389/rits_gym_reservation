# 基本となるイメージ
FROM selenium/standalone-chrome-debug:3

# タイムゾーン設定
ENV TZ=Asia/Tokyo

# rootユーザーに切り替える
USER root

# 作業ディレクトリの設定
WORKDIR /app

# 必要なシステムパッケージをインストール
RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# アプリケーションのコピー
COPY . /app/

# 必要なPythonライブラリのインストール
RUN pip install --no-cache-dir -r requirements.txt

# ボットを実行するために必要なコマンドを指定
# CMD ["python3", "reservation_bot.py"]