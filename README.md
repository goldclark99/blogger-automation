# Two-blog Blogger automation

Automates research, duplicate checking, English/Thai article generation, 16:9 thumbnails and scheduled Blogger publishing for:

- `goldclark.blogspot.com`
- `goldclark99.blogspot.com`

## Safety state

The repository starts with publishing disabled. Create the GitHub repository as **public** so Blogger can load thumbnails from `raw.githubusercontent.com`. Keep every credential in GitHub Secrets; never commit OAuth files or tokens.

Publishing requires both:

1. Repository variable `AUTOMATION_ENABLED=true`
2. `DRY_RUN=false`

## GitHub Secrets

- `OPENAI_API_KEY`
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `BLOGGER_EN_REFRESH_TOKEN`
- `BLOGGER_TH_REFRESH_TOKEN`

## Initial setup

1. Create a public GitHub repository named `blogger-automation`.
2. Push this project to its `main` branch.
3. In Google Cloud, enable **Blogger API v3**.
4. Configure an OAuth consent screen and create an OAuth client of type **Desktop app**.
5. Download the client JSON outside the repository.
6. Install dependencies locally and run the OAuth helper once for each Google account:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python scripts\oauth_bootstrap.py C:\path\client_secret.json --label english --output oauth-output-english.json
.venv\Scripts\python scripts\oauth_bootstrap.py C:\path\client_secret.json --label thai --output oauth-output-thai.json
```

7. Each run writes OAuth values only to a git-ignored local JSON file. Never paste that file into chat or commit it. Copy only the required values directly into GitHub Secrets, then delete the local files.
8. Add `AUTOMATION_ENABLED=false` in **Settings → Secrets and variables → Actions → Variables**.
9. Run the workflow manually in `morning` mode.
10. Run `evening` with `dry_run=true`, inspect the report, then set the repository variable to `true`.

## Schedule

GitHub Actions uses UTC:

- `21:00 UTC` → `06:00 Asia/Seoul`: research and current-post inspection
- `09:00 UTC` → `18:00 Asia/Seoul`: prepare the next `20:00` Blogger slot
- Sunday `04:00 UTC` → `13:00 Asia/Seoul`: weekly baseline report

Scheduled GitHub Actions can start late during platform congestion. The evening job therefore runs two hours before the Blogger publication time and schedules the post through the Blogger API.

## Current limitations

- Blogger API post resources do not expose Blogger's editor-only search-description field. The generated description is retained in the run report until a verified API-compatible method is available.
- The weekly report currently covers Blogger post status. Search Console and AdSense performance require additional Google API scopes and a separate reporting authorization.
- Google Trends RSS is a demand signal, not an evidence source. Article claims must use primary sources found during the OpenAI web-search step.
