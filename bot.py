import os
import asyncio
import sys
from hydrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, Update, StreamEnded, AudioQuality, VideoQuality
from dotenv import load_dotenv
from yt_handler import yt_handler

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# Channel username or ID
RAW_CHANNEL_ID = os.getenv("CHANNEL_ID", "Sl_Echo_ofwords")
if RAW_CHANNEL_ID.startswith("-100"):
    CHANNEL_ID = int(RAW_CHANNEL_ID)
else:
    CHANNEL_ID = RAW_CHANNEL_ID if RAW_CHANNEL_ID.startswith("@") else f"@{RAW_CHANNEL_ID}"

# Global Clients
app = None
call_py = None

# Global queue and state
queue = []
is_playing = False
current_video_id = None

async def play_next():
    global is_playing, current_video_id
    if len(queue) > 0:
        video = queue.pop(0)
        current_video_id = video['id']
        is_playing = True
        
        try:
            # Play with 240p Video Support
            await call_py.play(
                CHANNEL_ID, 
                MediaStream(
                    video['url'],
                    audio_parameters=AudioQuality.LOW,
                    video_parameters=VideoQuality.SD_360p, # Lowest standard SD quality
                )
            )
            
            await asyncio.sleep(1)
            try:
                await call_py.mute(CHANNEL_ID, False)
            except Exception as e:
                print(f"Unmute failed: {e}")
                
            try:
                print(f"Playing Video: {video['title']}")
            except:
                print(f"Playing Video ID: {video['id']}")
        except Exception as e:
            print(f"Error playing next: {e}")
            is_playing = False
            await play_next()
    else:
        if current_video_id:
            next_id = await yt_handler.get_related_video(current_video_id)
            if next_id:
                info = await yt_handler.extract_info(next_id)
                if info:
                    queue.append(info)
                    await play_next()
                    return
        
        is_playing = False
        print("Queue finished.")

async def start_bot():
    global app, call_py
    
    app = Client("musicbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
    call_py = PyTgCalls(app)

    @call_py.on_update()
    async def on_stream_end(client: PyTgCalls, update: Update):
        if isinstance(update, StreamEnded):
            await play_next()

    @app.on_message(filters.command("play") & filters.chat(CHANNEL_ID))
    async def cmd_play(client, message):
        query = " ".join(message.command[1:])
        if not query: return
        info = await add_to_queue(query)
        if info: await message.reply(f"Added: **{info['title']}**")

    @app.on_message(filters.command("skip") & filters.chat(CHANNEL_ID))
    async def cmd_skip(client, message):
        await play_next()
        await message.reply("Skipped!")

    await app.start()
    await call_py.start()
    
    try:
        await app.join_chat(CHANNEL_ID)
    except:
        pass
    
    if not is_playing:
        await add_to_queue("Lofi hip hop mix")

async def add_to_queue(query, play_now=False):
    global is_playing
    if not (query.startswith('http') or len(query) == 11):
        results = await yt_handler.search(query, limit=1)
        if not results: return None
        query = results[0]['id']

    info = await yt_handler.extract_info(query)
    if info:
        if play_now:
            queue.insert(0, info)
            await play_next()
        else:
            queue.append(info)
            if not is_playing:
                await play_next()
        return info
    return None

def get_state():
    return {
        "is_playing": is_playing,
        "current_video_id": current_video_id,
        "queue_length": len(queue),
        "queue": [v['title'] for v in queue[:10]]
    }

if __name__ == "__main__":
    asyncio.run(start_bot())
