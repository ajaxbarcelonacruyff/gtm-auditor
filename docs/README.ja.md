# gtm-auditor

Google Tag Manager（GTM）のコンテナ情報を Google Sheets に自動書き出しする Python CLI ツールです。バージョン差分の自動検出と、Claude API による解説生成（任意）をサポートします。

> **English documentation:** [../README.md](../README.md)

---

## 機能

- **最新スナップショット** — タグ・トリガー・変数・フォルダを個別タブに書き出し
- **バージョン差分** — 追加 / 削除 / 変更された要素を自動検出して記録
- **AI解説生成** — Claude API で各要素の役割と具体例を自動生成（APIキーなしでも動作）
- **GTM notes 優先** — GTMの `notes` フィールドがあればそのまま使用。空の場合のみ AI が補完
- **複数コンテナ対応** — クライアントサイドとサーバーサイドの両GTMコンテナを同時処理
- **ブラウザOAuth認証** — 初回のみブラウザでログイン。以降は `token.json` でトークン自動更新
- **言語切替** — `LANGUAGE=en|ja` でタブ名・列ヘッダー・AI出力言語を切替可能

---

## 生成されるシートタブ

タブ名は `LANGUAGE` 設定に従います（以下は `LANGUAGE=ja` の場合）。

### `--mode latest`（デフォルト）

| タブ名 | 内容 | 更新タイミング |
|--------|------|--------------|
| `タグ（最新）` | 全タグ＋AI解説 | 新バージョン検出時 |
| `トリガー（最新）` | 全トリガー＋AI解説 | 同上 |
| `変数（最新）` | 全変数＋AI解説 | 同上 |
| `フォルダ（最新）` | フォルダ一覧 | 同上 |
| `v251_client_差分` | v250→v251 の追加/削除/変更一覧 | 同上 |
| `バージョン一覧_client` | 全バージョン履歴 | 常時 |

### `--mode all`

上記に加え、過去バージョンごとに `v{N}_client_差分` タブを生成（前バージョンが存在する場合のみ）。

### `--version 251`

| タブ名 | 内容 |
|--------|------|
| `タグ（v251）` | v251 時点のタグ＋AI解説 |
| `トリガー（v251）` | v251 時点のトリガー |
| `変数（v251）` | v251 時点の変数 |
| `フォルダ（v251）` | v251 時点のフォルダ |
| `v251_client_差分` | v250→v251 の変更点 |
| `バージョン一覧_client` | 全バージョン履歴 |

> `LANGUAGE=en` の場合は `Tags (Latest)`、`v251_client_Diff`、`Version List_client` などになります。

---

## クイックスタート

```bash
# 1. 依存ライブラリをインストール
pip install -r requirements.txt

# 2. credentials.json を配置（手順は docs/SETUP.ja.md を参照）

# 3. .env ファイルを設定
#    （プロジェクトルートの .env をテキストエディタで編集）

# 4. 実行（最新バージョンのみ）
python main.py
```

詳細なセットアップ手順は [docs/SETUP.ja.md](SETUP.ja.md) を参照してください。

---

## 実行オプション

```bash
# 現在の Live バージョンを出力（デフォルト）
python main.py

# 全バージョン分のタブを生成
python main.py --mode all

# バージョン指定（v251 と前バージョンの差分を生成）
python main.py --version 251
```

---

## 設定（`.env`）

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `GTM_ACCOUNT_ID` | 必須 | GTM アカウント ID（GTM URL 内の数字） |
| `GTM_CLIENT_CONTAINER_ID` | 必須 | クライアントサイドコンテナ ID（数字） |
| `GTM_SERVER_CONTAINER_ID` | 任意 | サーバーサイドコンテナ ID（不要なら空欄） |
| `GOOGLE_SHEET_URL` | 必須 | 書き出し先 Google スプレッドシートの URL |
| `ANTHROPIC_API_KEY` | 任意 | Claude API キー（空欄なら解説生成スキップ） |
| `MODE` | 任意 | `latest`（デフォルト）/ `all` |
| `LANGUAGE` | 任意 | `en`（デフォルト）/ `ja` — タブ名・列ヘッダー・AI出力言語を制御 |

---

## プロジェクト構成

```
gtm-auditor/
├── gtm_auditor/                  # メインパッケージ
│   ├── __init__.py
│   ├── config.py                 # .env 読み込み・バリデーション
│   ├── gtm_client.py             # GTM API クライアント + OAuth2
│   ├── diff_engine.py            # バージョン差分計算
│   ├── claude_explainer.py       # AI 解説生成
│   ├── sheets_writer.py          # Google Sheets 書き込み
│   ├── i18n.py                   # 表示ラベル定義（en / ja）
│   └── formatters/               # 要素別の行データ整形
│       ├── tag_formatter.py
│       ├── trigger_formatter.py
│       ├── variable_formatter.py
│       ├── folder_formatter.py
│       └── version_formatter.py
├── docs/                         # ドキュメント
│   ├── README.ja.md              # 本ファイル
│   ├── SETUP.md                  # セットアップガイド（英語）
│   └── SETUP.ja.md               # セットアップガイド（日本語）
├── main.py                       # CLI エントリーポイント
├── requirements.txt
├── .env                          # 設定ファイル（コミット禁止）
├── .env.example                  # 設定テンプレート
└── .gitignore
```

---

## 動作要件

- Python 3.10 以上
- Tag Manager API と Sheets API を有効にした Google Cloud プロジェクト
- OAuth 2.0 デスクトップクライアント認証情報（`credentials.json`）

---

## ライセンス

MIT
