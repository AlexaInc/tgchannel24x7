import asyncio
import uvicorn
import os
import sys
import socket
from dotenv import load_dotenv

import api
import bot
from yt_handler import yt_handler

# --- DIAGNOSTICS & HARDENING ---
VERSION = "1.0.4-DEBUG"
print(f"--- BOT STARTUP (Version: {VERSION}) ---")
print(f"Python: {sys.version}")

# Force Cloudflare DNS for the entire process
try:
    import dns.resolver
    dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
    dns.resolver.default_resolver.nameservers = ['1.1.1.1', '1.0.0.1']
    print("[✓] Cloudflare DNS (1.1.1.1) forced.")
except Exception as e:
    print(f"[!] DNS override failed: {e}")

# Check TGCrypto
try:
    import tgcrypto
    print("[✓] TgCrypto detected and loaded successfully.")
except ImportError:
    print("[✗] TgCrypto still MISSING from python path.")

# Check Proxy
proxy = os.getenv("PROXY_URL")
if proxy:
    if not proxy.startswith(("http://", "https://", "socks")):
        print(f"[!] PRXOY_URL does not start with protocol. Fixing...")
        proxy = f"http://{proxy}"
        os.environ["PROXY_URL"] = proxy
    print(f"[✓] Proxy configured: {proxy[:15]}...")
else:
    print("[!] No PROXY_URL found in environment secrets.")

# --- END DIAGNOSTICS ---

load_dotenv()

# Inject bot functionalities into API
api.bot_add_to_queue = bot.add_to_queue
api.bot_get_state = bot.get_state
api.bot_skip = bot.play_next
api.bot_search = yt_handler.search

async def main():
    # Start bot and calls
    await bot.start_bot()
    
    # Run FastAPI via uvicorn in the same event loop
    # We use uvicorn.Config and Server to run it async
    config = uvicorn.Config(
        app=api.app, 
        host="0.0.0.0", 
        port=int(os.getenv("PORT", 7860)),
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    # Run both bot and api concurrently
    # Note: bot.app.run_forever() is replaced by this concurrent execution
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
