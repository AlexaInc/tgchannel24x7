import asyncio
import uvicorn
import os
from dotenv import load_dotenv

import api
import bot
from yt_handler import yt_handler
import dns.resolver

# Force Cloudflare DNS for the entire process
try:
    dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
    dns.resolver.default_resolver.nameservers = ['1.1.1.1', '1.0.0.1']
    print("Cloudflare DNS (1.1.1.1) forced.")
except Exception as e:
    print(f"DNS override failed: {e}")

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
