# 🚀 SecureChat - İleri Özellikler ve Geliştirme Kılavuzu

## 🎯 Roadmap

### Phase 1: Foundation ✅
- [x] E2EE with TweetNaCl.js
- [x] WebSocket real-time messaging
- [x] Room-based chat
- [x] Modern UI/UX

### Phase 2: Authentication & Storage
- [ ] User registration & login (JWT)
- [ ] Message history (encrypted database)
- [ ] User profiles
- [ ] Password protection for rooms

### Phase 3: Advanced Security
- [ ] Perfect Forward Secrecy (PFS)
- [ ] Double Ratchet Algorithm (Signal Protocol)
- [ ] Message signing & verification
- [ ] Key rotation
- [ ] Fingerprint verification

### Phase 4: Features
- [ ] File sharing (E2E encrypted)
- [ ] Voice/Video calls
- [ ] Group chats
- [ ] Message reactions
- [ ] Typing indicators

### Phase 5: Infrastructure
- [ ] Database integration (PostgreSQL + encryption)
- [ ] Cache layer (Redis)
- [ ] Load balancing
- [ ] Kubernetes deployment
- [ ] Monitoring & logging

---

## 💾 Veritabanı Entegrasyonu

### PostgreSQL + Encryption Örneği

```python
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet
import json

# Database setup
DATABASE_URL = "postgresql://user:password@localhost/securechat"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Encryption key (environment variable'dan oku)
ENCRYPTION_KEY = b'your-secret-key-base64-encoded'
cipher = Fernet(ENCRYPTION_KEY)

class EncryptedMessage(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    room_code = Column(String, index=True)
    sender_id = Column(String)
    encrypted_data = Column(String)
    nonce = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    @staticmethod
    def encrypt_content(content):
        """Mesajı database'e kaydetmeden önce şifrele"""
        return cipher.encrypt(content.encode()).decode()
    
    @staticmethod
    def decrypt_content(encrypted):
        """Şifreli mesajı şifre çöz"""
        return cipher.decrypt(encrypted.encode()).decode()

# Veritabanında şifreli mesaj sakla
def save_message(room_code, sender_id, encrypted_msg, nonce):
    db = SessionLocal()
    
    msg = EncryptedMessage(
        room_code=room_code,
        sender_id=sender_id,
        encrypted_data=encrypted_msg,
        nonce=nonce
    )
    
    db.add(msg)
    db.commit()
    db.close()

# Geçmiş mesajları al
@app.get("/room/{room_code}/history")
def get_message_history(room_code: str):
    db = SessionLocal()
    messages = db.query(EncryptedMessage).filter(
        EncryptedMessage.room_code == room_code
    ).all()
    
    return [
        {
            "sender_id": msg.sender_id,
            "encrypted": msg.encrypted_data,
            "nonce": msg.nonce,
            "timestamp": msg.created_at
        }
        for msg in messages
    ]
```

---

## 🔐 Perfect Forward Secrecy (PFS) Implementasyonu

```python
# Ephemeral session keys - her mesaj için yeni key
class EphemeralKeyManager:
    def __init__(self):
        self.session_keys = {}  # room_code -> {user_id -> ephemeral_key}
    
    def generate_ephemeral_keys(self, room_code, user_ids):
        """Her bağlantı için unique ephemeral keys oluştur"""
        self.session_keys[room_code] = {}
        
        for user_id in user_ids:
            # Static key + ephemeral key kombinasyonu
            ephemeral_pair = nacl.box.keyPair()
            self.session_keys[room_code][user_id] = {
                "ephemeral_public": ephemeral_pair.pk,
                "ephemeral_secret": ephemeral_pair.sk,
                "created_at": time.time()
            }
    
    def rotate_keys(self, room_code, user_id):
        """Belirli aralıkta keyleri rotate et"""
        ephemeral_pair = nacl.box.keyPair()
        
        self.session_keys[room_code][user_id].update({
            "ephemeral_public": ephemeral_pair.pk,
            "ephemeral_secret": ephemeral_pair.sk,
            "created_at": time.time()
        })
    
    def encrypt_with_ephemeral(self, message, recipient_public_key, user_ephemeral_secret):
        """Ephemeral key ile şifrele"""
        nonce = nacl.randomBytes(24)
        encrypted = nacl.box(
            message,
            nonce,
            recipient_public_key,
            user_ephemeral_secret  # Ephemeral secret kullan
        )
        return encrypted, nonce

# Implementasyon
ephemeral_manager = EphemeralKeyManager()

@app.websocket("/ws/{room_code}")
async def websocket_endpoint(websocket: WebSocket, room_code: str):
    # ... existing code ...
    
    # Ephemeral keys oluştur
    user_ids = [u["id"] for u in rooms[room_code]["users"]]
    ephemeral_manager.generate_ephemeral_keys(room_code, user_ids)
    
    # 5 dakikada bir keyleri rotate et
    @asyncio.task
    async def rotate_task():
        while True:
            await asyncio.sleep(300)  # 5 dakika
            ephemeral_manager.rotate_keys(room_code, user_id)
```

---

## 🔑 Message Signing (Non-Repudiation)

```javascript
// Frontend: Mesajı imzala
async signMessage(message) {
    const messageBytes = nacl.util.decodeUTF8(message);
    
    // Signing key pair'ı oluştur (bir kere)
    const signingKeyPair = nacl.sign.keyPair();
    
    const signature = nacl.sign.detached(messageBytes, signingKeyPair.secretKey);
    
    return {
        message: message,
        signature: this.arrayToString(signature),
        signing_public_key: this.arrayToString(signingKeyPair.publicKey)
    };
}

// Backend: İmzayı doğrula
def verify_signature(message, signature, signing_public_key):
    """Mesajın sender tarafından imzalandığını doğrula"""
    try:
        message_bytes = message.encode()
        sig_bytes = base64.b64decode(signature)
        pub_key_bytes = base64.b64decode(signing_public_key)
        
        # Doğrulama başarılı olursa True döner
        nacl.bindings.crypto_sign_open(
            sig_bytes + message_bytes,  # Signature + message
            pub_key_bytes
        )
        return True
    except nacl.exceptions.BadSignatureError:
        return False
```

---

## 🎙️ Voice/Video Integration

```javascript
// WebRTC ile peer-to-peer ses/video
class SecureChatWithMedia extends SecureChat {
    constructor() {
        super();
        this.peerConnection = null;
        this.localStream = null;
    }
    
    async initializeMedia() {
        try {
            this.localStream = await navigator.mediaDevices.getUserMedia({
                audio: true,
                video: { width: 640, height: 480 }
            });
            
            // Local stream'i video elementi'ne ekle
            document.getElementById('local-video').srcObject = this.localStream;
        } catch (error) {
            console.error('Media erişimi başarısız:', error);
        }
    }
    
    async initiateCall(recipientUserId) {
        const config = {
            iceServers: [
                { urls: ['stun:stun.l.google.com:19302'] }
            ]
        };
        
        this.peerConnection = new RTCPeerConnection(config);
        
        // Local stream track'lerini ekle
        this.localStream.getTracks().forEach(track => {
            this.peerConnection.addTrack(track, this.localStream);
        });
        
        // Remote stream'i dinle
        this.peerConnection.ontrack = (event) => {
            document.getElementById('remote-video').srcObject = event.streams[0];
        };
        
        // ICE candidates'ı server üzerinden gönder (şifreli)
        this.peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                this.sendEncryptedICECandidate(
                    recipientUserId,
                    event.candidate
                );
            }
        };
        
        // Offer oluştur
        const offer = await this.peerConnection.createOffer();
        await this.peerConnection.setLocalDescription(offer);
        
        // Offer'ı şifreli gönder
        this.sendEncryptedOffer(recipientUserId, offer);
    }
}
```

---

## 📊 Analytics & Monitoring

```python
from prometheus_client import Counter, Histogram, start_http_server
import time

# Metrics
message_counter = Counter(
    'securechat_messages_total',
    'Total encrypted messages',
    ['room_code']
)

connection_gauge = Gauge(
    'securechat_connections_active',
    'Active connections'
)

encryption_latency = Histogram(
    'securechat_encryption_duration_seconds',
    'Time to encrypt message'
)

# Kullanım
@encryption_latency.time()
def encrypt_message(message):
    # Encryption logic
    pass

# Prometheus endpoint
@app.get("/metrics")
async def metrics():
    return generate_latest()
```

---

## 🐳 Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App files
COPY server_e2ee.py .
COPY static/ ./static/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["uvicorn", "server_e2ee:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose:**

```yaml
version: '3.8'
services:
  securechat:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/securechat
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    depends_on:
      - db
    
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: securechat
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 🔒 Rate Limiting & DDoS Protection

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/create-room")
@limiter.limit("5/minute")  # 5 requests per minute
async def create_room(request: Request):
    # ... implementation ...
    pass

# WebSocket rate limiting
class RateLimitedWebSocket:
    def __init__(self, max_messages_per_minute=100):
        self.message_count = 0
        self.last_reset = time.time()
        self.max_messages = max_messages_per_minute
    
    async def check_rate_limit(self):
        current_time = time.time()
        
        if current_time - self.last_reset >= 60:
            self.message_count = 0
            self.last_reset = current_time
        
        self.message_count += 1
        
        if self.message_count > self.max_messages:
            raise RateLimitException("Rate limit exceeded")
```

---

## 🧪 Testing

```python
import pytest
from fastapi.testclient import TestClient

client = TestClient(app)

def test_create_room():
    response = client.get("/create-room")
    assert response.status_code == 200
    assert "room_code" in response.json()

def test_room_info():
    # Create room first
    create_response = client.get("/create-room")
    room_code = create_response.json()["room_code"]
    
    # Check info
    info_response = client.get(f"/room/{room_code}/info")
    assert info_response.status_code == 200
    assert info_response.json()["room_code"] == room_code

def test_websocket_connection():
    with client.websocket_connect("/ws/TEST123") as websocket:
        # Send init message
        websocket.send_json({
            "type": "init",
            "public_key": "test_key"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "init_response"
```

---

## 📈 Performance Optimization

### 1. Message Compression
```python
import gzip

def compress_message(message: str) -> bytes:
    return gzip.compress(message.encode())

def decompress_message(data: bytes) -> str:
    return gzip.decompress(data).decode()
```

### 2. Connection Pooling
```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600
)
```

### 3. Async I/O
```python
# Use async database queries
async def save_message_async(session, message_data):
    db_message = EncryptedMessage(**message_data)
    await session.add(db_message)
    await session.commit()
```

---

## 🛡️ Security Hardening Checklist

- [ ] HTTPS/WSS enforced
- [ ] CORS properly configured
- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (use ORM)
- [ ] XSS protection (CSP headers)
- [ ] CSRF tokens for state-changing operations
- [ ] Secure cookie settings (HttpOnly, Secure, SameSite)
- [ ] Security headers configured (X-Frame-Options, X-Content-Type-Options, etc.)
- [ ] Secrets management (environment variables)
- [ ] Key rotation mechanism
- [ ] Audit logging
- [ ] Regular security updates
- [ ] Dependency scanning
- [ ] Static code analysis

---

Made with 🔐 for privacy advocates
