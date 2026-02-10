import uuid
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, List
from pydantic import BaseModel

app = FastAPI()

# Static dosyaları serve et
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Veritabanı
rooms: Dict[str, Dict] = {}
user_sessions: Dict[str, Dict] = {}

class EncryptedMessage(BaseModel):
    """Şifrelenmiş mesaj modeli"""
    encrypted: str
    nonce: str
    sender_public_key: str

def generate_room_code():
    """Benzersiz oda kodu oluştur"""
    return f"{uuid.uuid4().hex[:6]}".upper()

@app.get("/", response_class=HTMLResponse)
def home():
    """Ana sayfa"""
    with open("static/index_e2ee.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/create-room")
def create_room():
    """Yeni şifreli oda oluştur"""
    room_code = generate_room_code()
    rooms[room_code] = {
        "users": [],
        "messages": [],
        "public_keys": {},
        "created_at": str(uuid.uuid4())
    }
    return {
        "room_code": room_code,
        "status": "success",
        "message": f"Oda '{room_code}' başarıyla oluşturuldu"
    }

@app.websocket("/ws/{room_code}")
async def websocket_endpoint(websocket: WebSocket, room_code: str):
    """WebSocket bağlantısı - E2EE ile mesaj şifreleme"""
    
    if room_code not in rooms:
        await websocket.accept()
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "❌ Oda bulunamadı!"
        }))
        await websocket.close()
        return

    await websocket.accept()
    
    user_id = str(uuid.uuid4())[:8]
    user_data = {
        "id": user_id,
        "websocket": websocket,
        "public_key": None,
        "joined_at": str(uuid.uuid4())
    }
    
    rooms[room_code]["users"].append(user_data)
    user_sessions[user_id] = {"room": room_code, "data": user_data}
    
    try:
        # İlk mesaj: Kullanıcının public key'ini al
        init_message = await websocket.receive_text()
        init_data = json.loads(init_message)
        
        if init_data.get("type") == "init":
            user_data["public_key"] = init_data.get("public_key")
            rooms[room_code]["public_keys"][user_id] = init_data.get("public_key")
            
            # Tüm mevcut public key'leri yeni kullanıcıya gönder
            await websocket.send_text(json.dumps({
                "type": "init_response",
                "user_id": user_id,
                "public_keys": rooms[room_code]["public_keys"],
                "message": f"✅ Odaya bağlandınız ({user_id})"
            }))
            
            # Diğer kullanıcılara yeni kullanıcıyı bildir
            for user in rooms[room_code]["users"]:
                if user["id"] != user_id and user["websocket"].client_state.name == "CONNECTED":
                    await user["websocket"].send_text(json.dumps({
                        "type": "user_joined",
                        "user_id": user_id,
                        "public_key": user_data["public_key"]
                    }))
        
        # Mesajları dinle ve şifrelenmiş olarak diğerlerine yolla
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "message":
                # Mesajı veritabanına kaydet (şifrelenmiş)
                rooms[room_code]["messages"].append({
                    "sender_id": user_id,
                    "encrypted": message_data.get("encrypted"),
                    "nonce": message_data.get("nonce"),
                    "timestamp": str(uuid.uuid4())
                })
                
                # Diğer tüm kullanıcılara gönder
                for user in rooms[room_code]["users"]:
                    if user["id"] != user_id and user["websocket"].client_state.name == "CONNECTED":
                        await user["websocket"].send_text(json.dumps({
                            "type": "message",
                            "sender_id": user_id,
                            "encrypted": message_data.get("encrypted"),
                            "nonce": message_data.get("nonce"),
                            "sender_public_key": user_data["public_key"]
                        }))
    
    except WebSocketDisconnect:
        # Kullanıcıyı çıkar
        rooms[room_code]["users"] = [u for u in rooms[room_code]["users"] if u["id"] != user_id]
        if user_id in user_sessions:
            del user_sessions[user_id]
        
        # Diğerlere bildir
        for user in rooms[room_code]["users"]:
            try:
                await user["websocket"].send_text(json.dumps({
                    "type": "user_left",
                    "user_id": user_id,
                    "message": f"👤 Kullanıcı ayrıldı ({user_id})"
                }))
            except:
                pass
        
        print(f"❌ Kullanıcı ayrıldı: {user_id} from room {room_code}")
    
    except Exception as e:
        print(f"⚠️ Hata: {str(e)}")

@app.get("/room/{room_code}/info")
def get_room_info(room_code: str):
    """Oda bilgisini al"""
    if room_code not in rooms:
        return {"error": "Oda bulunamadı", "status": "error"}
    
    room = rooms[room_code]
    return {
        "room_code": room_code,
        "user_count": len(room["users"]),
        "message_count": len(room["messages"]),
        "status": "active"
    }

if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
