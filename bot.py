import os
import asyncio
import sys
import random
import subprocess
from hydrogram import Client, filters
from hydrogram.raw import functions, types
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
STREAM_MODE = os.getenv("STREAM_MODE", "VOICE_CHAT")
BACKGROUND_IMAGE_PATH = os.path.normpath(os.path.abspath(os.getenv("BACKGROUND_IMAGE_PATH", "background.png")))

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
played_history = []
cached_rtmps_url = None

class FFMPEGStreamer:
    def __init__(self):
        self.process = None

    async def start(self, audio_url, rtmps_url):
        if self.process:
            self.stop()
        
        command = [
            "ffmpeg",
            "-loglevel", "warning",
            "-reconnect", "1",
            "-reconnect_at_eof", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "5",
            "-re",
            "-i", audio_url,
            "-vf", "scale=-2:50",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-profile:v", "baseline",
            "-b:v", "100k",
            "-maxrate", "100k",
            "-bufsize", "200k",
            "-pix_fmt", "yuv420p",
            "-g", "15",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-f", "flv",
            "-flvflags", "no_duration_filesize",
            rtmps_url
        ]
        
        try:
            self.process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            print(f"Started FFmpeg process for RTMPS streaming.")
            # Monitor process in background
            asyncio.create_task(self._monitor())
        except Exception as e:
            print(f"Failed to start FFmpeg: {e}")

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
            except:
                pass
            self.process = None

    async def _monitor(self):
        while self.process and self.process.returncode is None:
            line = await self.process.stderr.readline()
            if not line:
                break
            msg = line.decode(errors='ignore').strip()
            if msg:
                if "Successfully connected" in msg or "Publishing" in msg:
                    print(f"--- [✓] RTMPS CONNECTION ESTABLISHED ---")
                print(f"FFmpeg: {msg}")
            
        returncode = await self.process.wait()
        print(f"FFmpeg process exited with code {returncode}")
        if is_playing:
            await play_next()

streamer = FFMPEGStreamer()

async def get_rtmp_credentials():
    try:
        peer = await app.resolve_peer(CHANNEL_ID)
        
        # 1. Check if a group call already exists
        channel_full = await app.invoke(functions.channels.GetFullChannel(channel=peer))
        call_exists = getattr(channel_full.full_chat, "call", None)
        
        if not call_exists:
            print("No active Live Stream found. Starting a new one...")
            try:
                await app.invoke(functions.phone.CreateGroupCall(
                    peer=peer,
                    random_id=random.randint(0, 2**31 - 1),
                    rtmp_stream=True,
                    title="24/7 Music Stream"
                ))
                # Wait a moment for changes to propagate
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Warning: Could not create group call: {e}")

        # 2. Get the stream credentials
        res = await app.invoke(functions.phone.GetGroupCallStreamRtmpUrl(
            peer=peer,
            revoke=False
        ))
        cached_rtmps_url = f"{res.url}{res.key}"
        print(f"Successfully fetched RTMPS credentials.")
        return cached_rtmps_url
    except Exception as e:
        print(f"Error getting RTMPS credentials: {e}")
        return None

async def play_next():
    global is_playing, current_video_id, played_history
    
    # Add finished song to history
    if current_video_id:
        if current_video_id not in played_history:
            played_history.append(current_video_id)
        if len(played_history) > 100:
            played_history.pop(0)

    if len(queue) > 0:
        video = queue.pop(0)
        current_video_id = video['id']
        is_playing = True
        
        try:
            if STREAM_MODE == "RTMPS":
                rtmps_url = await get_rtmp_credentials()
                if not rtmps_url:
                    print("Failed to get RTMPS credentials. Check admin permissions.")
                    is_playing = False
                    return

                await streamer.start(video['url'], rtmps_url)
            else:
                # Play with 240p Video Support
                await call_py.play(
                    CHANNEL_ID, 
                    MediaStream(
                        video['url'],
                        audio_parameters=AudioQuality.MEDIUM,
                        video_parameters=VideoQuality.SD_360p, 
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
            related_ids = await yt_handler.get_related_videos(current_video_id)
            for next_id in related_ids:
                if next_id not in played_history:
                    info = await yt_handler.extract_info(next_id)
                    if info:
                        queue.append(info)
                        await play_next()
                        return
        
        is_playing = False
        current_video_id = None
        print("Queue finished and no recommendations found.")

async def start_bot():
    global app, call_py
    
    app = Client("musicbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
    
    if STREAM_MODE != "RTMPS":
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
        if STREAM_MODE == "RTMPS":
            streamer.stop()
        await play_next()
        await message.reply("Skipped!")

    await app.start()
    
    if STREAM_MODE != "RTMPS":
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
