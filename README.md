# gtm-auditor

A Python CLI tool that exports Google Tag Manager (GTM) container data to Google Sheets — with automatic version diffing and optional AI-powered explanations via Claude API.

> **日本語ドキュメント:** [docs/README.ja.md](docs/README.ja.md)

---

## Features

- **Latest snapshot** — Tags, Triggers, Variables, and Folders exported as individual tabs
- **Version diff** — Automatically detects Added / Deleted / Modified elements between versions
- **AI explanations** — Generates role descriptions and usage examples via Claude API (optional; skipped if no API key)
- **GTM notes passthrough** — Uses existing GTM `notes` fields as-is; AI fills in only what's missing
- **Multi-container** — Supports both Client-side and Server-side GTM containers simultaneously
- **Browser OAuth** — First-run browser login; subsequent runs use cached token automatically
- **Language switching** — Output language (tab names, headers, AI text) configurable via `LANGUAGE=en|ja`

---

## Generated Sheet Tabs

Tab names vary based on the `LANGUAGE` setting (example below uses `LANGUAGE=en`).

### `--mode latest` (default)

| Tab | Content | When |
|-----|---------|------|
| `Tags (Latest)` | All tags + AI explanations | On new version detection |
| `Triggers (Latest)` | All triggers + AI explanations | Same |
| `Variables (Latest)` | All variables + AI explanations | Same |
| `Folders (Latest)` | Folder list | Same |
| `v251_client_Diff` | Added / Deleted / Modified since v250 | Same |
| `Version List_client` | All version history | Always |

### `--mode all`

Same as above, plus one `v{N}_client_Diff` tab per historical version (if a previous version exists).

### `--version 251`

| Tab | Content |
|-----|---------|
| `Tags (v251)` | Tags at v251 + AI explanations |
| `Triggers (v251)` | Triggers at v251 |
| `Variables (v251)` | Variables at v251 |
| `Folders (v251)` | Folders at v251 |
| `v251_client_Diff` | Changes from v250 → v251 |
| `Version List_client` | All version history |

> With `LANGUAGE=ja`, tab names become `タグ（最新）`, `v251_client_差分`, `バージョン一覧_client`, etc.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Place credentials.json (see docs/SETUP.md for details)

# 3. Fill in .env
#    (edit the existing .env file in the project root)

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
| `GTM_ACCOUNT_ID` | Yes | GTM Account ID (numeric, from GTM URL) |
| `GTM_CLIENT_CONTAINER_ID` | Yes | Client-side container ID (numeric) |
| `GTM_SERVER_CONTAINER_ID` | No | Server-side container ID (leave blank if unused) |
| `GOOGLE_SHEET_URL` | Yes | Target Google Sheet URL |
| `ANTHROPIC_API_KEY` | No | Claude API key (explanations skipped if empty) |
| `MODE` | No | `latest` (default) / `all` |
| `LANGUAGE` | No | `en` (default) / `ja` — controls tab names, headers, and AI output language |

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
│   ├── i18n.py                   # All user-visible labels (en / ja)
│   └── formatters/               # Per-element row formatters
│       ├── tag_formatter.py
│       ├── trigger_formatter.py
│       ├── variable_formatter.py
│       ├── folder_formatter.py
│       └── version_formatter.py
├── docs/                         # Documentation
│   ├── README.ja.md              # Japanese README
│   ├── SETUP.md                  # Setup guide (English)
│   └── SETUP.ja.md               # Setup guide (Japanese)
├── main.py                       # CLI entry point
├── requirements.txt
├── .env                          # Your configuration (never commit)
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
