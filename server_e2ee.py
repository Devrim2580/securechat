import uuid
import json
import os
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from typing import Dict, List
from pydantic import BaseModel, validator, constr
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('securechat.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== APP SETUP ====================
app = FastAPI(
    title="SecureChat E2EE",
    description="End-to-End Encrypted Chat with Security Hardening",
    version="2.0.0"
)

# ==================== RATE LIMITING ====================
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ==================== SECURITY MIDDLEWARE ====================

# CORS Configuration - STRICT!
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("ALLOWED_ORIGIN", "http://localhost:8000")
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self' ws: wss:;"
    )
    return response

# HTTPS Redirect (production için)
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
    logger.info("✅ HTTPS redirect enabled")

# ==================== DATA MODELS ====================

class SecureMessage(BaseModel):
    """Validated encrypted message model"""
    encrypted: constr(min_length=1, max_length=100000)
    nonce: constr(min_length=32, max_length=64)
    signature: constr(min_length=1, max_length=200) = None
    ephemeral_key: constr(min_length=1, max_length=200) = None
    
    @validator('encrypted', 'nonce')
    def validate_base64(cls, v):
        """Ensure base64 encoding"""
        import base64
        try:
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError("Invalid base64 encoding")

class RoomInfo(BaseModel):
    room_code: str
    user_count: int
    created_at: str
    max_users: int = 10

# ==================== IN-MEMORY STORAGE ====================
rooms: Dict[str, Dict] = {}
user_sessions: Dict[str, Dict] = {}

# Rate limit tracking
connection_attempts: Dict[str, List[datetime]] = {}

# ==================== HELPER FUNCTIONS ====================

def generate_room_code() -> str:
    """Generate secure 6-character room code"""
    return f"{uuid.uuid4().hex[:6]}".upper()

def check_connection_rate_limit(ip: str, max_attempts: int = 10, window_seconds: int = 60) -> bool:
    """Check if IP is making too many connection attempts"""
    now = datetime.utcnow()
    
    if ip not in connection_attempts:
        connection_attempts[ip] = []
    
    # Clean old attempts
    connection_attempts[ip] = [
        attempt for attempt in connection_attempts[ip]
        if (now - attempt).total_seconds() < window_seconds
    ]
    
    # Check limit
    if len(connection_attempts[ip]) >= max_attempts:
        logger.warning(f"🚨 Rate limit exceeded for IP: {ip}")
        return False
    
    connection_attempts[ip].append(now)
    return True

# ==================== REST ENDPOINTS ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main HTML page"""
    try:
        with open("static/index_e2ee.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>404 - index_e2ee.html not found</h1>",
            status_code=404
        )

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "rooms": len(rooms),
        "connections": sum(len(r["users"]) for r in rooms.values())
    }

@app.get("/create-room")
@limiter.limit("5/minute")  # 5 rooms per minute per IP
async def create_room(request: Request):
    """Create a new encrypted chat room"""
    room_code = generate_room_code()
    
    # Ensure uniqueness
    while room_code in rooms:
        room_code = generate_room_code()
    
    rooms[room_code] = {
        "users": [],
        "messages": [],
        "public_keys": {},
        "created_at": datetime.utcnow().isoformat(),
        "max_users": 10
    }
    
    logger.info(f"✅ Room created: {room_code}")
    
    return {
        "room_code": room_code,
        "status": "success",
        "message": f"Oda '{room_code}' başarıyla oluşturuldu",
        "created_at": rooms[room_code]["created_at"]
    }

@app.get("/room/{room_code}/info")
@limiter.limit("20/minute")
async def get_room_info(room_code: str, request: Request):
    """Get room information"""
    if room_code not in rooms:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")
    
    room = rooms[room_code]
    return RoomInfo(
        room_code=room_code,
        user_count=len(room["users"]),
        created_at=room["created_at"],
        max_users=room.get("max_users", 10)
    )

# ==================== WEBSOCKET ENDPOINT ====================

@app.websocket("/ws/{room_code}")
async def websocket_endpoint(websocket: WebSocket, room_code: str):
    """
    WebSocket endpoint for encrypted real-time chat
    
    Security features:
    - Rate limiting per IP
    - Input validation
    - Max users per room
    - Connection tracking
    """
    
    # Get client IP
    client_ip = websocket.client.host
    
    # Rate limit check
    if not check_connection_rate_limit(client_ip):
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "message": "⚠️ Too many connection attempts. Please wait."
        })
        await websocket.close(code=1008)  # Policy violation
        return
    
    # Room existence check
    if room_code not in rooms:
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "message": "❌ Oda bulunamadı!"
        })
        await websocket.close(code=1008)
        return
    
    # Max users check
    if len(rooms[room_code]["users"]) >= rooms[room_code].get("max_users", 10):
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "message": "❌ Oda dolu! (Max 10 kullanıcı)"
        })
        await websocket.close(code=1008)
        return
    
    await websocket.accept()
    
    user_id = str(uuid.uuid4())[:8]
    user_data = {
        "id": user_id,
        "websocket": websocket,
        "public_key": None,
        "joined_at": datetime.utcnow().isoformat(),
        "ip": client_ip
    }
    
    rooms[room_code]["users"].append(user_data)
    user_sessions[user_id] = {
        "room": room_code,
        "ip": client_ip
    }
    
    logger.info(f"👤 User joined: {user_id} in room {room_code} (IP: {client_ip})")
    
    try:
        # ==================== INITIALIZATION ====================
        init_message = await websocket.receive_text()
        init_data = json.loads(init_message)
        
        if init_data.get("type") == "init":
            # Validate public key
            public_key = init_data.get("public_key")
            if not public_key or len(public_key) < 32:
                raise ValueError("Invalid public key")
            
            user_data["public_key"] = public_key
            rooms[room_code]["public_keys"][user_id] = public_key
            
            # Send init response
            await websocket.send_json({
                "type": "init_response",
                "user_id": user_id,
                "public_keys": rooms[room_code]["public_keys"],
                "message": f"✅ Odaya bağlandınız ({user_id})"
            })
            
            logger.info(f"🔑 Public key registered for {user_id}")
            
            # Notify others
            for user in rooms[room_code]["users"]:
                if user["id"] != user_id and user["websocket"]:
                    try:
                        await user["websocket"].send_json({
                            "type": "user_joined",
                            "user_id": user_id,
                            "public_key": user_data["public_key"]
                        })
                    except Exception as e:
                        logger.error(f"Error notifying user: {e}")
        
        # ==================== MESSAGE LOOP ====================
        message_count = 0
        max_messages_per_minute = 100
        
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Rate limit messages
            message_count += 1
            if message_count > max_messages_per_minute:
                await websocket.send_json({
                    "type": "error",
                    "message": "⚠️ Too many messages. Slow down!"
                })
                continue
            
            if message_data.get("type") == "message":
                try:
                    # Validate message using Pydantic
                    secure_msg = SecureMessage(
                        encrypted=message_data.get("encrypted"),
                        nonce=message_data.get("nonce"),
                        signature=message_data.get("signature"),
                        ephemeral_key=message_data.get("ephemeral_key")
                    )
                    
                    recipient_id = message_data.get("recipient_id")
                    
                    payload = {
                        "type": "message",
                        "sender_id": user_id,
                        "encrypted": secure_msg.encrypted,
                        "nonce": secure_msg.nonce,
                        "signature": secure_msg.signature,
                        "ephemeral_key": secure_msg.ephemeral_key,
                        "sender_public_key": user_data["public_key"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # Store in room (for potential persistence)
                    rooms[room_code]["messages"].append(payload)
                    
                    # Broadcast to recipient(s)
                    if recipient_id:
                        # Direct message
                        for user in rooms[room_code]["users"]:
                            if user["id"] == recipient_id:
                                try:
                                    await user["websocket"].send_json(payload)
                                    logger.info(f"📤 Message: {user_id} → {recipient_id}")
                                except Exception as e:
                                    logger.error(f"Failed to send message: {e}")
                                break
                    else:
                        # Broadcast to all
                        for user in rooms[room_code]["users"]:
                            if user["id"] != user_id:
                                try:
                                    await user["websocket"].send_json(payload)
                                except Exception as e:
                                    logger.error(f"Broadcast failed: {e}")
                
                except ValueError as e:
                    logger.warning(f"Invalid message format: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "❌ Invalid message format"
                    })
            
            elif message_data.get("type") == "typing":
                # Typing indicator
                for user in rooms[room_code]["users"]:
                    if user["id"] != user_id:
                        try:
                            await user["websocket"].send_json({
                                "type": "typing",
                                "user_id": user_id,
                                "is_typing": message_data.get("is_typing", False)
                            })
                        except:
                            pass
    
    except WebSocketDisconnect:
        logger.info(f"👋 User disconnected: {user_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    
    finally:
        # ==================== CLEANUP ====================
        rooms[room_code]["users"] = [
            u for u in rooms[room_code]["users"] 
            if u["id"] != user_id
        ]
        rooms[room_code]["public_keys"].pop(user_id, None)
        user_sessions.pop(user_id, None)
        
        # Notify others
        for user in rooms[room_code]["users"]:
            try:
                await user["websocket"].send_json({
                    "type": "user_left",
                    "user_id": user_id
                })
            except:
                pass
        
        # Clean up empty rooms
        if len(rooms[room_code]["users"]) == 0:
            del rooms[room_code]
            logger.info(f"🗑️ Empty room deleted: {room_code}")
        
        logger.info(f"👤 User cleanup completed: {user_id}")

# ==================== STARTUP/SHUTDOWN ====================

@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("🚀 SecureChat E2EE Server Starting...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Version: 2.0.0")
    
    if os.getenv("ENVIRONMENT") == "production":
        if not os.getenv("SSL_CERT"):
            logger.warning("⚠️ Production mode but no SSL certificate configured!")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("🛑 SecureChat E2EE Server Shutting Down...")
    
    # Close all WebSocket connections gracefully
    for room in rooms.values():
        for user in room["users"]:
            try:
                await user["websocket"].close()
            except:
                pass

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting server on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )