import os
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeAudio, DocumentAttributeFilename

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]
CHANNEL = os.environ["CHANNEL"]  # channel username (no @) or numeric id, as string

CACHE_TTL = 60  # seconds between re-scanning the channel for new songs
MAX_MESSAGES = 1000  # how far back to look in the channel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

_cache = {"songs": [], "messages": {}, "ts": 0.0}


async def refresh_songs():
    entity = await client.get_entity(CHANNEL)
    songs = []
    messages = {}
    async for msg in client.iter_messages(entity, limit=MAX_MESSAGES):
        if not msg.media or not getattr(msg.media, "document", None):
            continue
        doc = msg.media.document
        if not (doc.mime_type or "").startswith("audio"):
            continue

        title, performer, duration = None, "", 0
        for attr in doc.attributes:
            if isinstance(attr, DocumentAttributeAudio):
                title = attr.title or title
                performer = attr.performer or performer
                duration = attr.duration or duration
            elif isinstance(attr, DocumentAttributeFilename) and not title:
                title = attr.file_name

        songs.append({
            "id": msg.id,
            "title": title or f"Track {msg.id}",
            "performer": performer,
            "duration": duration,
            "size": doc.size,
            "mime": doc.mime_type,
        })
        messages[msg.id] = msg

    songs.sort(key=lambda s: s["id"])
    _cache["songs"] = songs
    _cache["messages"] = messages
    _cache["ts"] = time.time()


async def ensure_fresh():
    if time.time() - _cache["ts"] > CACHE_TTL:
        await refresh_songs()


@app.on_event("startup")
async def startup():
    await client.start()
    await refresh_songs()


@app.get("/api/songs")
async def list_songs():
    await ensure_fresh()
    return _cache["songs"]


@app.get("/api/stream/{message_id}")
async def stream(message_id: int, request: Request):
    await ensure_fresh()
    msg = _cache["messages"].get(message_id)
    if not msg:
        raise HTTPException(404, "Song not found")

    doc = msg.media.document
    size = doc.size
    mime = doc.mime_type or "audio/mpeg"

    start, end, status_code = 0, size - 1, 200
    range_header = request.headers.get("range")
    if range_header:
        try:
            _, rng = range_header.split("=")
            start_s, end_s = (rng.split("-") + [""])[:2]
            start = int(start_s) if start_s else 0
            end = int(end_s) if end_s else size - 1
            status_code = 206
        except Exception:
            start, end = 0, size - 1
    length = end - start + 1

    async def chunk_generator():
        sent = 0
        aligned_start = start - (start % 4096)
        skip = start - aligned_start
        async for chunk in client.iter_download(doc, offset=aligned_start, request_size=1024 * 1024):
            if skip:
                if len(chunk) <= skip:
                    skip -= len(chunk)
                    continue
                chunk = chunk[skip:]
                skip = 0
            remaining = length - sent
            if remaining <= 0:
                break
            if len(chunk) > remaining:
                chunk = chunk[:remaining]
            yield chunk
            sent += len(chunk)
            if sent >= length:
                break

    headers = {
        "Content-Range": f"bytes {start}-{end}/{size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(length),
    }
    return StreamingResponse(chunk_generator(), status_code=status_code, media_type=mime, headers=headers)


app.mount("/", StaticFiles(directory="static", html=True), name="static")
