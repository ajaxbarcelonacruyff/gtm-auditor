# gtm-auditor 実装引き継ぎ

## プロジェクト概要

Google Tag Manager（GTM）のコンテナ情報をGTM APIで取得し、Google Sheetsに自動書き込みするPythonツール。

- GTMのタグ・トリガー・変数・フォルダを取得してシートに整理
- バージョン差分（追加/削除/変更）を自動検出して記録
- Claude APIがあれば各要素の解説を自動生成（なければスキップ）
- Googleアカウントでブラウザログインして認証（OAuth2）

---

## 実装計画（承認済み）

### ディレクトリ構成

```
gtm-auditor/
├── .env                  # 設定ファイル（git管理外）
├── .env.example          # テンプレート（git管理対象）
├── main.py               # エントリーポイント・CLI
├── config.py             # .env読み込み・バリデーション
├── gtm_client.py         # GTM API クライアント
├── diff_engine.py        # バージョン差分計算
├── claude_explainer.py   # Claude API 解説生成（任意）
├── sheets_writer.py      # Sheets API 書き込み
├── formatters/
│   ├── __init__.py
│   ├── tag_formatter.py
│   ├── trigger_formatter.py
│   ├── variable_formatter.py
│   └── folder_formatter.py
├── state.json            # 最終処理バージョン記録（自動生成）
└── token.json            # OAuth2トークンキャッシュ（自動生成）
```

### .env 設定

```env
# GTM（クライアントサイド）
GTM_ACCOUNT_ID=123456789
GTM_CLIENT_CONTAINER_ID=987654321

# GTM（サーバーサイド、不要なら空欄）
GTM_SERVER_CONTAINER_ID=111222333

# Google Sheets（URLそのままでOK）
GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/xxxxx/edit

# Claude API（なければ空欄 → 解説生成スキップ）
ANTHROPIC_API_KEY=

# 実行モード: latest / all / version=251
MODE=latest
```

### CLI実行オプション

```bash
# 最新Liveバージョンのみ（state.jsonと比較して新バージョンなら更新）
python main.py

# 全バージョン分のタブを生成
python main.py --mode all

# バージョン指定（v251とv250の差分を生成）
python main.py --version 251
```

---

## 生成されるシートタブ

| タブ名 | 内容 | 更新タイミング |
|--------|------|--------------|
| `タグ（最新）` | 全タグ＋解説 | 新バージョン検出時・常に上書き |
| `トリガー（最新）` | 全トリガー＋解説 | 同上 |
| `変数（最新）` | 全変数＋解説 | 同上 |
| `フォルダ（最新）` | フォルダ一覧 | 同上 |
| `v251_client_差分` | v250→v251 追加/削除/変更一覧 | `--version 251` 実行時 |
| `v251_client_全体` | v251時点のスナップショット | 同上 |
| `v7_server_差分` | v6→v7 差分 | 同上 |

---

## 列構成

### タグ（最新）

| タグ名 | コンテナ | テンプレート種別 | フォルダ | 役割・解説 | 具体例 | 発火トリガー | ブロックトリガー | パラメータ詳細 |

- 役割・解説: GTMのnotesフィールドがあればそのまま使用。空ならClaude API生成（APIなければ空欄）
- 具体例: Claude API生成のみ（「〜のページを開いたとき発火」などの発火シナリオ）

### 差分タブ（v251_client_差分）

| 変更種別 | 要素種別 | 要素名 | 変更前 | 変更後 | 解説（AI） |

- 変更種別: 追加 / 削除 / 変更

---

## 認証フロー

```
初回実行:
  ブラウザが自動で開く → Googleアカウントでログイン → token.json に保存

2回目以降:
  token.json からトークンを自動リフレッシュ（ログイン不要）

必要スコープ:
  - https://www.googleapis.com/auth/tagmanager.readonly
  - https://www.googleapis.com/auth/spreadsheets
```

---

## 依存ライブラリ

```
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
anthropic
python-dotenv
```

---

## Claude APIなし時の動作

- `ANTHROPIC_API_KEY` が空でも正常動作
- 解説列・具体例列は空欄のまま（エラーにならない）
- GTMの `notes` フィールドに記載があればそれは常に使用
- 後からAPIキーを追加して再実行すれば解説が補完される

---

## 開発上の注意

- `.env` および `token.json` は `.gitignore` に必ず追加
- GTM APIはRead-only（tagmanager.readonly）スコープのみ使用
- Sheets APIは読み書き両方（spreadsheets スコープ）
- state.json でバージョン管理（最後に処理したバージョンIDを記録）
- クライアントとサーバーコンテナは独立して処理（バージョン番号体系が異なる）

---

## 実装開始の指示

このファイルを読んだら、以下の順で実装してください：

1. `requirements.txt` と `.env.example` を作成
2. `config.py`（.env読み込み・バリデーション）
3. `gtm_client.py`（GTM API接続・バージョン取得）
4. `formatters/`（各要素のデータ整形）
5. `diff_engine.py`（バージョン差分計算）
6. `claude_explainer.py`（解説生成、APIなし時はno-op）
7. `sheets_writer.py`（Sheets書き込み・タブ生成）
8. `main.py`（CLI・全体制御）

実装前に必ずユーザーに「Goと言ってください」と確認を取ること。
