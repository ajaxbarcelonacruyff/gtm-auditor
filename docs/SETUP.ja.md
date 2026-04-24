# セットアップガイド（作業手順書）

> **English version:** [SETUP.md](SETUP.md)

gtm-auditor を初めて実行するまでの手順を説明します。

---

## 前提条件

| 項目 | バージョン / 備考 |
|------|-----------------|
| Python | 3.10 以上 |
| Google アカウント | 対象の GTM コンテナとスプレッドシートへのアクセス権が必要 |
| Google Cloud プロジェクト | 無料枠で十分 |

---

## Step 1 — Google API を有効化する

1. [Google Cloud Console](https://console.cloud.google.com/) を開き、プロジェクトを選択（または新規作成）する。
2. **「APIとサービス」→「ライブラリ」** を開く。
3. **「Tag Manager API」** を検索して有効化する。
4. **「Google Sheets API」** を検索して有効化する。

---

## Step 2 — OAuth 2.0 認証情報を作成する

1. **「APIとサービス」→「認証情報」** を開く。
2. **「認証情報を作成」→「OAuthクライアントID」** をクリックする。
3. 同意画面（OAuth consent screen）の設定を求められた場合:
   - ユーザーの種類: **外部**（Google Workspace 組織内のみなら「内部」でも可）
   - アプリ名・サポートメール・開発者の連絡先メールを入力する
   - スコープに以下を追加する:
     - `https://www.googleapis.com/auth/tagmanager.readonly`
     - `https://www.googleapis.com/auth/spreadsheets`
   - **テストユーザー**に自分の Google アカウントを追加する
4. アプリケーションの種類で **「デスクトップアプリ」** を選択する。
5. **「作成」** → **「JSONをダウンロード」** をクリックする。
6. ダウンロードしたファイルを `credentials.json` にリネームし、プロジェクトルートに置く:

```
gtm-auditor/
└── credentials.json   ← ここに配置
```

> `credentials.json` は `.gitignore` に登録済みで、Git にはコミットされません。

---

## Step 3 — 依存ライブラリをインストールする

仮想環境の使用を推奨します。

```bash
# 仮想環境を作成・有効化
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
.venv\Scripts\activate             # Windows

# パッケージをインストール
pip install -r requirements.txt
```

---

## Step 4 — `.env` ファイルを設定する

プロジェクトルートにある `.env` をテキストエディタで開き、各項目を入力する:

```env
# GTM アカウント ID（GTM の URL に含まれる: accounts/XXXXXXXXX）
GTM_ACCOUNT_ID=123456789

# クライアントサイド GTM コンテナ ID（GTM URL: containers/XXXXXXXXX）
GTM_CLIENT_CONTAINER_ID=987654321

# サーバーサイド GTM コンテナ ID（使わない場合は空欄）
GTM_SERVER_CONTAINER_ID=

# 書き出し先 Google スプレッドシートの URL（ブラウザのアドレスバーからコピー）
GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/xxxxx/edit

# Claude API キー（解説生成が不要なら空欄のままでOK）
ANTHROPIC_API_KEY=

# 実行モード: latest（デフォルト）/ all
MODE=latest
```

### GTM の ID の調べ方

GTM をブラウザで開いたときのURL を確認する:

```
https://tagmanager.google.com/#/container/accounts/123456789/containers/987654321/...
                                                   ^^^^^^^^^              ^^^^^^^^^
                                                   アカウントID           コンテナID
```

### Google スプレッドシートの共有設定

ログインする Google アカウントが、対象スプレッドシートの **編集者** 権限を持っていることを確認する。

---

## Step 5 — 初回実行

```bash
python main.py
```

1. ブラウザが自動で開く。
2. Google アカウントでログインし、アクセス許可を承認する。
3. プロジェクトルートに `token.json` が生成される。次回以降のログインは不要。
4. GTM のデータが Google スプレッドシートに書き込まれる。

---

## 実行コマンド一覧

```bash
# 現在の Live バージョンのみ書き出す（デフォルト）
python main.py

# 全バージョン分のタブを生成する
python main.py --mode all

# バージョンを指定して書き出す（指定バージョンと直前との差分も生成）
python main.py --version 251
```

---

## トラブルシューティング

### `credentials.json が見つかりません`
Google Cloud Console からダウンロードしたファイルを `credentials.json` にリネームして、プロジェクトルート直下に配置してください。

### ブラウザに `redirect_uri_mismatch` エラーが表示される
Google Cloud Console で OAuth クライアントの種類が **「デスクトップアプリ」** になっているか確認してください（「ウェブアプリケーション」になっている場合は再作成が必要です）。

### `アクセスをブロックされました: このアプリのリクエストは無効です`
OAuth 同意画面の設定で、自分の Google アカウントを **テストユーザー** に追加してください。

### スプレッドシートが更新されない / 権限エラー
ログインしている Google アカウントが対象スプレッドシートの **編集者** 権限を持っているか確認してください。

### 再ログインしたい
`token.json` を削除してから再実行してください。ブラウザによるログインフローが再開されます。

---

## ファイル説明

| ファイル | 説明 |
|----------|------|
| `credentials.json` | OAuth クライアント認証情報（Cloud Console からダウンロード、**コミット禁止**） |
| `token.json` | アクセストークンのキャッシュ（自動生成、**コミット禁止**） |
| `state.json` | コンテナごとの最終処理バージョン ID を記録（自動生成） |
| `.env` | GTM ID・シート URL・API キーなどの設定（**コミット禁止**） |
