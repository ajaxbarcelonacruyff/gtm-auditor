# Setup Guide

> **日本語版:** [SETUP.ja.md](SETUP.ja.md)

This guide walks you through everything needed to run gtm-auditor for the first time.

---

## Prerequisites

| Item | Version / Notes |
|------|----------------|
| Python | 3.10 or later |
| Google account | Must have access to the target GTM container and Google Sheet |
| Google Cloud project | Free tier is sufficient |

---

## Step 1 — Enable Google APIs

1. Open [Google Cloud Console](https://console.cloud.google.com/) and select (or create) a project.
2. Go to **APIs & Services → Library**.
3. Search for and enable **Tag Manager API**.
4. Search for and enable **Google Sheets API**.

---

## Step 2 — Create OAuth 2.0 Credentials

1. Go to **APIs & Services → Credentials**.
2. Click **Create Credentials → OAuth client ID**.
3. If prompted, configure the **OAuth consent screen** first:
   - User type: **External** (or Internal if using Google Workspace)
   - Fill in App name, support email, and developer contact email
   - Add the following scopes:
     - `https://www.googleapis.com/auth/tagmanager.readonly`
     - `https://www.googleapis.com/auth/spreadsheets`
   - Add your own Google account as a **test user**
4. Back in Create Credentials, choose **Application type: Desktop app**.
5. Click **Create**, then **Download JSON**.
6. Rename the downloaded file to `credentials.json` and place it in the project root:

```
gtm-auditor/
└── credentials.json   ← here
```

> `credentials.json` is listed in `.gitignore` and will never be committed.

> **You do NOT need to click "Publish app".**  
> Leaving the Publishing status as **Testing** is fine for personal use — no Google verification required. Just make sure your Google account is added as a test user.  
> Note: in Testing mode, `token.json` **expires after 7 days**. When it does, delete `token.json` and run again to re-authenticate.

---

## Step 3 — Install Dependencies

We recommend using a virtual environment.

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
.venv\Scripts\activate             # Windows

# Install packages
pip install -r requirements.txt
```

---

## Step 4 — Configure `.env`

Open the `.env` file in the project root and fill in your values:

```env
# GTM Account ID  (found in GTM URL: accounts/XXXXXXXXX)
GTM_ACCOUNT_ID=123456789

# Client-side GTM Container ID  (GTM URL: containers/XXXXXXXXX)
GTM_CLIENT_CONTAINER_ID=987654321

# Server-side GTM Container ID  (leave blank if not used)
GTM_SERVER_CONTAINER_ID=

# Google Sheets URL  (paste the full URL from your browser)
GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/xxxxx/edit

# Claude API key  (leave blank to skip AI explanations)
ANTHROPIC_API_KEY=

# Run mode: latest (default) / all
MODE=latest
```

### Finding your GTM IDs

Open GTM in your browser. Use the **numeric IDs from the URL** — not the `GTM-XXXXXX` tag ID.

```
https://tagmanager.google.com/#/container/accounts/123456789/containers/987654321/...
                                                   ^^^^^^^^^              ^^^^^^^^^
                                               GTM_ACCOUNT_ID        GTM_CLIENT_CONTAINER_ID
```

> **Note:** The `GTM-XXXXXX` format (e.g. `GTM-P7NMS64`) shown on tags is the public container ID and cannot be used with the API. Use only the numeric IDs from the URL.

### Sharing the Google Sheet

Make sure the Google account you'll log in with has **Editor** access to the target spreadsheet.

---

## Step 5 — First Run

```bash
python main.py
```

1. A browser window opens automatically.
2. Log in with your Google account and grant the requested permissions.
3. A `token.json` file is created in the project root — subsequent runs skip the browser step.
4. GTM data is written to your Google Sheet.

---

## Usage Reference

```bash
# Export the current live version (default)
python main.py

# Export all historical versions
python main.py --mode all

# Export a specific version + diff from the previous version
python main.py --version 251
```

---

## Troubleshooting

### `credentials.json が見つかりません`
Place the file downloaded from Google Cloud Console as `credentials.json` in the project root.

### `redirect_uri_mismatch` browser error
In Google Cloud Console, verify the OAuth client type is **Desktop app** (not Web application).

### `Access blocked: This app's request is invalid`
Add your Google account as a **test user** on the OAuth consent screen.

### Sheet not updated / permission error
Confirm that the logged-in Google account has **Editor** access to the target spreadsheet.

### Re-authenticating
Delete `token.json` and run again to go through the browser login flow.

---

## File Reference

| File | Description |
|------|-------------|
| `credentials.json` | OAuth client credentials (download from Cloud Console, **never commit**) |
| `token.json` | Cached access/refresh token (auto-generated, **never commit**) |
| `state.json` | Tracks the last processed version ID per container (auto-generated) |
| `.env` | Your configuration (GTM IDs, Sheet URL, API keys — **never commit**) |
