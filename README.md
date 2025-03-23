# 立命館のジム予約を簡略化するdiscord botのセットアップ手順

## 実行環境
- replitを使った無料サーバ運用
   - `必要デバイス:` 特になし
   - `デメリット:` 無料プランでは24時間中最大で30分ほどダウンタイムあり
- Dockerを使ったローカルサーバ運用
   - `必要デバイス:` DockerのインストールされたPC
   - `デメリット:` 24時間インターネットに接続した状態で起動しておく必要あり

# 1. discord Botの作成および追加
<!-- あとで追記する -->

# 2. Google関連の設定
## Googleスプレッドシートの準備
1. Googleアカウントを用意
1. `Users_template.xlsx`を`Google Drive`にアップロード
1. エクセルファイルを開いた後，`File` > `Save as Google Sheets`を選択し，Google Sheetに変換
1. 変換されたスプレッドシート名を適当な名前に変更する
1. スプレッドシートの `sheetID` をあとで使うのでメモしておく
   - `sheetID`：URLの `d/` と `/edit` の間の文字列

## Google Cloud Platformの設定
1. [Google Cloud Platform](https://console.cloud.google.com/) にアクセス
2. コンソールを開き，新規プロジェクトを作成（名前は自由）
3. 左のメニューから `有効なAPIとサービス` を選択
4. `Google Sheets API` を有効化
5. `Google Drive API` を有効化

## 認証情報の設定
1. `OAuth同意画面` から `開始`
   - アプリ名：自由
   - ユーザーサポートメール：作成したGoogleアカウントが無難
   - 対象：`外部`
   - 連絡先情報：作成したGoogleアカウントが無難
2. 作成を押す
3. `APIとサービス` → `認証情報` → `認証情報を作成`
   - `サービスアカウント` を選択
   - `サービスアカウント名` は自由
   - `ロール` は `オーナー`
   - 完了
4. `サービスアカウントの編集` → `鍵（キー）` → `新しい鍵を作成`
   - `JSON` を選択し，ダウンロード
5. ダウンロードした `JSON` ファイルをプロジェクトフォルダに保存し， `credentials.json` にリネーム
6. `credentials.json` を開き，`client_email` をコピー
7. スプレッドシートを開き，`共有` → `ユーザーを追加` に `client_email` をペーストし，`編集者` に設定

<!-- envファイル系はローカルのDockerとreplit使うバージョンで少し異なる（replitではenvファイルは非推奨？）ことを書く -->
<!-- # 3. `.env` ファイルの作成
1. `.env`ファイルをプロジェクトのルートディレクトリに作成
1. `.env.example` ファイルを参考に，さきほどメモした情報を `.env` ファイルに記述
```sh
DISCORD_BOT_TOKEN = （作成したBotのトークン）
USERS_SHEET_ID = （スプレッドシートID）
```

<!--
   replit使う場合のやつ
## サーバに定期通信を行うためのGAS (Google Apps Script)の環境構築
   1. GASプロジェクトの作成
   1. GASコードのコピペ
   1. 変数の設定（プロジェクトセッティングのとこから設定する）
   1. トリガーを1分毎に設定
-->

# 4. 実行手順
1. ターミナルを開いてプロジェクトフォルダに移動

例↓
```sh
cd workSpace/rits_gym_reservation
```

2. コンテナをビルド＆起動
```sh
docker-compose up --build
```

3. 終了時は `Ctrl + C` で強制終了 -->

<!-- # 5. bot利用方法 -->
<!-- あとで追記する（コマンドの使い方とか） -->