import uuid
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, List
from pydantic import BaseModel

app = FastAPI()

# Static UI
app.mount("/ui", StaticFiles(directory="static", html=True), name="static")

# Oda verisi
rooms: Dict[str, Dict] = {}
user_sessions: Dict[str, Dict] = {}

class EncryptedMessage(BaseModel):
    encrypted: str
    nonce: str
    sender_public_key: str
    recipient_id: str = None  # EKLEME: Alıcı ID'si

def generate_room_code():
    return f"{uuid.uuid4().hex[:6]}".upper()

@app.get("/", response_class=HTMLResponse)
def home():
    with open("static/index_e2ee_FIXED.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/create-room")
def create_room():
    room_code = generate_room_code()
    rooms[room_code] = {
        "users": [],        # [{id, websocket, public_key}]
        "messages": [],
        "public_keys": {}
    }
    return {
        "room_code": room_code,
        "status": "success",
        "message": f"Oda '{room_code}' başarıyla oluşturuldu"
    }

@app.websocket("/ws/{room_code}")
async def websocket_endpoint(websocket: WebSocket, room_code: str):
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
        "public_key": None
    }

    rooms[room_code]["users"].append(user_data)
    user_sessions[user_id] = {"room": room_code}

    try:
        # INIT: Public key al
        init_message = await websocket.receive_text()
        init_data = json.loads(init_message)

        if init_data.get("type") == "init":
            user_data["public_key"] = init_data.get("public_key")
            rooms[room_code]["public_keys"][user_id] = init_data.get("public_key")

            # Yeni kullanıcıya mevcut public key'leri gönder
            await websocket.send_text(json.dumps({
                "type": "init_response",
                "user_id": user_id,
                "public_keys": rooms[room_code]["public_keys"],
                "message": f"✅ Odaya bağlandınız ({user_id})"
            }))

            # Diğerlerine yeni kullanıcıyı bildir
            for user in rooms[room_code]["users"]:
                if user["id"] != user_id:
                    try:
                        await user["websocket"].send_text(json.dumps({
                            "type": "user_joined",
                            "user_id": user_id,
                            "public_key": user_data["public_key"]
                        }))
                    except:
                        pass

        # MESAJ DÖNGÜSÜ
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data.get("type") == "message":
                # DÜZELTME: Mesajı sadece belirli alıcıya gönder
                recipient_id = message_data.get("recipient_id")
                
                payload = {
                    "type": "message",
                    "sender_id": user_id,
                    "encrypted": message_data.get("encrypted"),
                    "nonce": message_data.get("nonce"),
                    "sender_public_key": user_data["public_key"]
                }

                rooms[room_code]["messages"].append(payload)

                # Mesajı sadece alıcıya gönder (gönderene değil!)
                if recipient_id:
                    for user in rooms[room_code]["users"]:
                        if user["id"] == recipient_id:
                            try:
                                await user["websocket"].send_text(json.dumps(payload))
                                print(f"📤 Mesaj gönderildi: {user_id} → {recipient_id}")
                            except Exception as e:
                                print(f"❌ Mesaj gönderilemedi: {e}")
                            break
                else:
                    # recipient_id yoksa herkese gönder (eski davranış)
                    for user in list(rooms[room_code]["users"]):
                        if user["id"] != user_id:  # Gönderen hariç
                            try:
                                await user["websocket"].send_text(json.dumps(payload))
                            except:
                                pass

    except WebSocketDisconnect:
        pass
    finally:
        # Kullanıcıyı çıkar
        rooms[room_code]["users"] = [u for u in rooms[room_code]["users"] if u["id"] != user_id]
        rooms[room_code]["public_keys"].pop(user_id, None)
        user_sessions.pop(user_id, None)

        # Diğerlerine bildir
        for user in rooms[room_code]["users"]:
            try:
                await user["websocket"].send_text(json.dumps({
                    "type": "user_left",
                    "user_id": user_id
                }))
            except:
                pass

        print(f"👋 Kullanıcı ayrıldı: {user_id} (oda {room_code})")

@app.get("/room/{room_code}/info")
def get_room_info(room_code: str):
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