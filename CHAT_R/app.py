import os
import uuid
import json
import random
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VideoChat Elite", version="3.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class User(BaseModel):
    id: str
    username: str
    age: int
    gender: str
    country: str
    interests: List[str]
    language: str
    is_online: bool = False
    rating: float = 5.0

class MatchRequest(BaseModel):
    user_id: str
    preferences: Dict[str, str]

class Message(BaseModel):
    sender_id: str
    recipient_id: str
    content: str
    timestamp: str
    is_translated: bool = False

# Database
users_db: Dict[str, User] = {}
active_connections: Dict[str, WebSocket] = {}
match_queue: List[str] = []
conversations: Dict[str, List[Message]] = {}

# Connection Manager
class ConnectionManager:
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        active_connections[user_id] = websocket
        users_db[user_id].is_online = True
        logger.info(f"User {user_id} connected")

    def disconnect(self, user_id: str):
        if user_id in active_connections:
            del active_connections[user_id]
            users_db[user_id].is_online = False
            logger.info(f"User {user_id} disconnected")

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in active_connections:
            await active_connections[user_id].send_text(message)
            logger.info(f"Message sent to {user_id}")

manager = ConnectionManager()

# Routes
@app.post("/register", response_model=User)
async def register_user(user: User):
    user.id = str(uuid.uuid4())
    users_db[user.id] = user
    logger.info(f"New user registered: {user.username}")
    return user

@app.post("/match")
async def request_match(match_request: MatchRequest):
    if match_request.user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[match_request.user_id]
    potential_matches = [
        u for u in users_db.values() 
        if u.id != user.id 
        and u.is_online
        and (not match_request.preferences.get("gender") or u.gender == match_request.preferences["gender"])
        and (not match_request.preferences.get("min_age") or u.age >= int(match_request.preferences["min_age"]))
        and (not match_request.preferences.get("max_age") or u.age <= int(match_request.preferences["max_age"]))
        and (not match_request.preferences.get("country") or u.country == match_request.preferences["country"])
        and (not match_request.preferences.get("interests") or any(i in u.interests for i in match_request.preferences["interests"].split(",")))
    ]
    
    if potential_matches:
        match = max(potential_matches, key=lambda u: (
            (len(set(user.interests) & set(u.interests))) * 0.6 + u.rating * 0.4
        ))
        return {"matched_user": match, "room_id": str(uuid.uuid4())}
    
    match_queue.append(match_request.user_id)
    return {"status": "waiting", "position": len(match_queue)}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "chat":
                msg = Message(
                    sender_id=user_id,
                    recipient_id=message["recipient_id"],
                    content=message["content"],
                    timestamp=datetime.now().isoformat()
                )
                
                if msg.recipient_id not in conversations:
                    conversations[msg.recipient_id] = []
                conversations[msg.recipient_id].append(msg)
                
                await manager.send_personal_message(json.dumps({
                    "type": "message",
                    "content": msg.content,
                    "sender": users_db[user_id].username,
                    "timestamp": msg.timestamp
                }), msg.recipient_id)
                
            elif message["type"] == "disconnect":
                manager.disconnect(user_id)
                break
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"User {user_id} disconnected")

@app.get("/users/online", response_model=List[User])
async def get_online_users():
    return [u for u in users_db.values() if u.is_online]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)