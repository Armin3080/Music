import os
import asyncio
import websockets
import json
import uuid
from collections import defaultdict
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Global variables
rooms = defaultdict(dict)  # room_id: {socket1: websocket, socket2: websocket}
clients = {}  # websocket: room_id

async def handle_connection(websocket, path):
    print(f"New WebSocket connection: {websocket.remote_address}")
    
    try:
        async for message in websocket:
            data = json.loads(message)
            
            if data['type'] == 'create_or_join':
                await handle_create_or_join(websocket, data)
                
            elif data['type'] == 'offer':
                await handle_offer(websocket, data)
                
            elif data['type'] == 'answer':
                await handle_answer(websocket, data)
                
            elif data['type'] == 'candidate':
                await handle_candidate(websocket, data)
                
            elif data['type'] == 'leave':
                await handle_leave(websocket, data)
                
    except websockets.exceptions.ConnectionClosed:
        print(f"WebSocket connection closed: {websocket.remote_address}")
        await handle_disconnect(websocket)

async def handle_create_or_join(websocket, data):
    # Find an available room or create a new one
    room_id = None
    
    for existing_room, clients_in_room in rooms.items():
        if len(clients_in_room) < 2:
            room_id = existing_room
            break
    
    if room_id is None:
        room_id = str(uuid.uuid4())
        rooms[room_id][websocket] = None
        clients[websocket] = room_id
        await websocket.send(json.dumps({
            'type': 'room_created',
            'room': room_id
        }))
        print(f"Created new room: {room_id}")
    else:
        rooms[room_id][websocket] = None
        clients[websocket] = room_id
        
        # Notify both clients that room is ready
        for client in rooms[room_id]:
            await client.send(json.dumps({
                'type': 'room_joined',
                'room': room_id
            }))
        print(f"Joined room: {room_id}")

async def handle_offer(websocket, data):
    room_id = data['room']
    if room_id in rooms and websocket in rooms[room_id]:
        for client in rooms[room_id]:
            if client != websocket:
                await client.send(json.dumps({
                    'type': 'offer',
                    'offer': data['offer'],
                    'room': room_id
                }))

async def handle_answer(websocket, data):
    room_id = data['room']
    if room_id in rooms and websocket in rooms[room_id]:
        for client in rooms[room_id]:
            if client != websocket:
                await client.send(json.dumps({
                    'type': 'answer',
                    'answer': data['answer'],
                    'room': room_id
                }))

async def handle_candidate(websocket, data):
    room_id = data['room']
    if room_id in rooms and websocket in rooms[room_id]:
        for client in rooms[room_id]:
            if client != websocket:
                await client.send(json.dumps({
                    'type': 'candidate',
                    'candidate': data['candidate'],
                    'room': room_id
                }))

async def handle_leave(websocket, data):
    room_id = data['room']
    if room_id in rooms and websocket in rooms[room_id]:
        for client in rooms[room_id]:
            if client != websocket:
                await client.send(json.dumps({
                    'type': 'user_disconnected',
                    'room': room_id
                }))
        
        await cleanup_room(room_id, websocket)

async def handle_disconnect(websocket):
    if websocket in clients:
        room_id = clients[websocket]
        
        if room_id in rooms:
            for client in rooms[room_id]:
                if client != websocket and client.open:
                    await client.send(json.dumps({
                        'type': 'user_disconnected',
                        'room': room_id
                    }))
            
            await cleanup_room(room_id, websocket)

async def cleanup_room(room_id, websocket):
    if room_id in rooms:
        rooms[room_id].pop(websocket, None)
        if len(rooms[room_id]) == 0:
            rooms.pop(room_id)
    
    clients.pop(websocket, None)
    print(f"Cleaned up room: {room_id}")

async def start_websocket_server():
    async with websockets.serve(handle_connection, "0.0.0.0", 8080):
        await asyncio.Future()  # run forever

class HTTPHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.getcwd(), **kwargs)

def start_http_server():
    server_address = ('0.0.0.0', 8000)
    httpd = HTTPServer(server_address, HTTPHandler)
    print(f"Starting HTTP server on http://localhost:8000")
    httpd.serve_forever()

async def main():
    # Create static directory if it doesn't exist
    os.makedirs("static", exist_ok=True)
    
    # Start HTTP server in a separate thread
    http_thread = asyncio.to_thread(start_http_server)
    http_task = asyncio.create_task(http_thread)
    
    # Start WebSocket server
    await start_websocket_server()

if __name__ == "__main__":
    asyncio.run(main())