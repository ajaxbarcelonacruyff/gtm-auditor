# gtm-auditor

A Python CLI tool that exports Google Tag Manager (GTM) container data to Google Sheets — with automatic version diffing and optional AI-powered explanations via Claude API.

> **日本語ドキュメント:** [docs/README.ja.md](docs/README.ja.md)

---

## Features

- **Full snapshot sheets** — Tags, Triggers, Variables, and Folders exported as individual tabs
- **Version diff** — Automatically detects Added / Deleted / Changed elements between versions
- **AI explanations** — Generates role descriptions and usage examples via Claude API (optional; skipped if no API key)
- **GTM notes passthrough** — Uses existing GTM `notes` fields as-is; AI fills in only what's missing
- **Multi-container** — Supports both Client-side and Server-side GTM containers simultaneously
- **Browser OAuth** — First-run browser login; subsequent runs use cached token automatically

---

## Generated Sheet Tabs

| Tab name | Content | When updated |
|----------|---------|--------------|
| `タグ（最新）` | All tags + explanations | On new version detection (always overwritten) |
| `トリガー（最新）` | All triggers + explanations | Same |
| `変数（最新）` | All variables + explanations | Same |
| `フォルダ（最新）` | Folder list | Same |
| `v251_client_差分` | Added / Deleted / Changed since v250 | `--version 251` |
| `v251_client_全体` | Full snapshot at v251 | `--version 251` |
| `v7_server_差分` | Server-side diff | `--version 7` (server) |

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Place credentials.json (see docs/SETUP.md for details)

# 3. Copy and fill in .env
cp .env.example .env

# 4. Run (latest version only)
python main.py
```

See [docs/SETUP.md](docs/SETUP.md) for the full setup walkthrough.

---

## Usage

```bash
# Export the current live version (default)
python main.py

# Export all versions
python main.py --mode all

# Export a specific version and its diff from the previous version
python main.py --version 251
```

---

## Configuration (`.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `GTM_ACCOUNT_ID` | Yes | GTM Account ID |
| `GTM_CLIENT_CONTAINER_ID` | Yes | Client-side container ID |
| `GTM_SERVER_CONTAINER_ID` | No | Server-side container ID (leave blank if unused) |
| `GOOGLE_SHEET_URL` | Yes | Target Google Sheet URL |
| `ANTHROPIC_API_KEY` | No | Claude API key (explanations skipped if empty) |
| `MODE` | No | `latest` (default) / `all` |

---

## Project Structure

```
gtm-auditor/
├── gtm_auditor/                  # Main package
│   ├── __init__.py
│   ├── config.py                 # .env loading & validation
│   ├── gtm_client.py             # GTM API client + OAuth2
│   ├── diff_engine.py            # Version diff calculation
│   ├── claude_explainer.py       # AI explanation generator
│   ├── sheets_writer.py          # Google Sheets writer
│   └── formatters/               # Per-element row formatters
│       ├── tag_formatter.py
│       ├── trigger_formatter.py
│       ├── variable_formatter.py
│       └── folder_formatter.py
├── docs/                         # Documentation
│   ├── README.ja.md              # Japanese README
│   ├── SETUP.md                  # Setup guide (English)
│   └── SETUP.ja.md               # Setup guide (Japanese)
├── main.py                       # CLI entry point
├── requirements.txt
├── .env.example                  # Configuration template
└── .gitignore
```

---

## Requirements

- Python 3.10+
- Google Cloud project with Tag Manager API and Sheets API enabled
- OAuth 2.0 Desktop client credentials (`credentials.json`)

---

## License

MIT
