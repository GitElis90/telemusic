# Telegram-channel music player (free)

Streams audio directly from a Telegram channel — no storage, no storage fees.
Telegram stays the only place the files live; the backend fetches bytes on
demand each time someone hits play.

## 1. Get Telegram API credentials
1. Go to https://my.telegram.org -> log in -> "API development tools".
2. Create an app (any name/description). Copy the **api_id** and **api_hash**.

## 2. Log in once, locally, to get a session string
This step needs your phone + login code, so it must run on your own
computer, not the server.

```
pip install telethon
python generate_session.py
```

Enter the api_id / api_hash from step 1, your phone number, and the code
Telegram texts/sends you. It prints a `SESSION_STRING` — copy it somewhere
safe. Treat it like a password: whoever has it is logged into your account.

## 3. Prepare the channel
- Make sure the Telegram account you logged in with (step 2) is a member of
  (or admin of) the channel where you upload songs.
- Upload songs as **audio files** (not as generic documents) so Telegram
  tags them with title/performer/duration — the app reads those tags.

## 4. Deploy on Render (free)
1. Push this folder to a GitHub repo.
2. On https://render.com -> New -> Web Service -> connect the repo.
3. Runtime: Python 3. Build command: `pip install -r requirements.txt`.
   Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
4. Under Environment, add these variables:
   - `API_ID` — from step 1
   - `API_HASH` — from step 1
   - `SESSION_STRING` — from step 2
   - `CHANNEL` — the channel's username without @ (e.g. `mysongs`), or its
     numeric ID if it's private
5. Deploy. Render gives you a public URL — that's your music site.

**Free-tier note:** Render's free web services sleep after ~15 minutes of no
traffic and take a few seconds to wake on the next visit. That's normal and
costs nothing — just a short delay on the first play after inactivity.

## 5. Adding songs
Just upload new audio files to the channel as usual. The app rescans the
channel every 60 seconds, so new songs appear automatically — no redeploy,
no manual step.

## Limits to know about
- Works with songs of any size Telegram itself allows (up to 2 GB per file),
  since this uses your account's connection, not the more limited bot API.
- Seeking/scrubbing works but snaps to the nearest ~4KB chunk — fine for
  audio, not frame-exact.
- One person's play = one live fetch from Telegram; this is fine for
  personal/small-audience use. If it ever gets heavy traffic, an in-memory
  or CDN cache layer could be added later.
