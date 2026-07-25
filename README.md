# House Search Bot

Daily automated search of Domain.com.au listings (via Parse.bot's wrapper API) with Telegram notifications for new matches.

## Setup

1. **Push these files to your private GitHub repo** (`house-search-bot`), preserving the folder structure — the `.github/workflows/daily-search.yml` file must stay at that exact path.

2. **Add repository secrets** — go to your repo's Settings → Secrets and variables → Actions → New repository secret, and add:
   - `PARSE_API_KEY` — your Parse.bot API key
   - `TELEGRAM_BOT_TOKEN` — your Telegram bot token from BotFather
   - `TELEGRAM_CHAT_ID` — your numeric Telegram chat ID

3. **Edit your search criteria** in `house_search.py` — the `SEARCHES` list near the top of the file. Add one dict per suburb/criteria combination you want tracked. Location must be a `suburb-state-postcode` slug (e.g. `"newtown-nsw-2042"`).

4. **Test manually first**: go to your repo's "Actions" tab → "Daily House Search" workflow → "Run workflow" button → run it manually once to confirm everything works before waiting for the daily schedule.

5. Once confirmed, it will run automatically every day at the time set in the cron schedule (default: 22:00 UTC = 8am Sydney standard time — adjust the cron line in the workflow file if you want a different time, keeping daylight saving in mind).

## Troubleshooting

- **401 Unauthorized error**: Your Parse.bot API key may be a truncated/masked value rather than the full secret. Go to the Parse.bot dashboard → API Keys → "Create API Key" to generate a fresh full-length key, then update the `PARSE_API_KEY` secret in GitHub.
- **No notifications arriving**: Check the Actions tab → click the latest run → expand "Run house search" step to see console output and any errors.
- **Telegram messages not sending**: Confirm you've sent at least one message to your bot first (Telegram bots can't message you until you've messaged them first).

## How it works

- Each run calls Parse.bot's `search_properties_for_sale` endpoint once per entry in `SEARCHES`.
- Listing IDs already notified are stored in `seen_listings.json`, which the workflow commits back to the repo after each run — so you're only notified about genuinely new listings, not the same ones every day.
- Off-the-plan "project" listings are skipped by default (can be changed in `house_search.py`).
