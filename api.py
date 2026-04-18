from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Pass references to bot functions from main.py
# (We will import these in main.py)

app = FastAPI(title="Music Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("JWT_SECRET", "supersecret")
ALGORITHM = "HS256"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class SongResult(BaseModel):
    title: str
    id: str
    thumbnail: Optional[str]
    duration: Optional[int] = None

class BotState(BaseModel):
    is_playing: bool
    current_video_id: Optional[str]
    queue_length: int
    queue: List[str]

# Reference to bot functions (will be set in main.py)
bot_add_to_queue = None
bot_get_state = None
bot_skip = None
bot_search = None

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": "admin"})
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401)
        return username
    except:
        raise HTTPException(status_code=401)

@app.get("/state", response_model=BotState)
async def get_state(user: str = Depends(get_current_user)):
    if bot_get_state:
        return bot_get_state()
    return {"is_playing": False, "current_video_id": None, "queue_length": 0, "queue": []}

@app.post("/play")
async def play_song(query: str, play_now: bool = False, user: str = Depends(get_current_user)):
    if bot_add_to_queue:
        info = await bot_add_to_queue(query, play_now=play_now)
        if info:
            return {"status": "success", "song": info['title']}
    return {"status": "error", "message": "Failed to add song"}

@app.post("/skip")
async def skip_song(user: str = Depends(get_current_user)):
    if bot_skip:
        await bot_skip()
        return {"status": "success"}
    return {"status": "error"}

@app.get("/search", response_model=List[SongResult])
async def search_songs(q: str, user: str = Depends(get_current_user)):
    if bot_search:
        return await bot_search(q)
    return []

# Catch-all to serve index.html for SPA (must be at the end)
@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    # Check if the file exists in the build directory
    dist_path = os.path.join("web", "dist", full_path)
    if os.path.isfile(dist_path):
        return FileResponse(dist_path)
    
    # Otherwise return index.html for SPA routing
    index_path = os.path.join("web", "dist", "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    
    # If build doesn't exist yet, return a simple message
    return HTMLResponse("<h1>Bot is running!</h1><p>Frontend not yet built.</p>")
