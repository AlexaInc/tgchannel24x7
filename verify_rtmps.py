import asyncio
import os
from hydrogram import Client
from hydrogram.raw import functions, types
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
CHANNEL_ID = os.getenv("CHANNEL_ID", "Sl_Echo_ofwords")

async def test_credentials():
    print(f"--- RTMPS CREDENTIAL VERIFICATION ---")
    app = Client("test_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING, in_memory=True)
    
    try:
        await app.start()
        print("[PASS] Session connected successfully.")
        
        peer = await app.resolve_peer(CHANNEL_ID)
        print(f"[PASS] Resolved peer for {CHANNEL_ID}.")
        
        try:
            res = await app.invoke(functions.phone.GetGroupCallStreamRtmpUrl(
                peer=peer,
                revoke=False
            ))
            print(f"[PASS] Successfully fetched RTMPS credentials!")
            print(f"    URL: {res.url}")
            print(f"    Key: {res.key[:5]}****")
        except Exception as e:
            print(f"[FAIL] Failed to fetch RTMPS credentials: {e}")
            print(f"    Tip: Ensure a Live Stream 'Stream With...' has been started in the channel.")
            
        await app.stop()
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    asyncio.run(test_credentials())
