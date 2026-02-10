# 🔐 SecureChat - Ultra Güvenlikli E2EE ChatBox

**End-to-End Encryption (E2EE) ile korunan, açık kaynaklı gerçek zamanlı sohbet uygulaması**

---

## 📋 Özellikler

✅ **End-to-End Encryption (E2EE)**
- TweetNaCl.js kütüphanesi ile NaCl cryptography
- Her mesaj client-side'da şifrelenir
- Sunucu şifrelenmiş veriler dışında hiçbir şey görmez
- Quantum-resistant değil (X25519 eliptik eğri)

✅ **Gerçek Zamanlı İletişim**
- WebSocket bağlantısı
- Düşük latency
- Otomatik reconnection

✅ **Modern UI**
- Dark mode optimized
- Responsive tasarım
- Smooth animations
- Minimalist aesthetic

✅ **Kullanıcı Yönetimi**
- Anonimlik (ID-based)
- Otomatik public key paylaşımı
- Kullanıcı join/leave bildirimleri

---

## 🛠️ Kurulum

### 1. **Gereksinimleri Kur**

```bash
pip install -r requirements.txt
```

### 2. **Klasör Yapısını Oluştur**

```
project/
├── server_e2ee.py
├── requirements.txt
├── static/
│   └── index_e2ee.html
└── README.md
```

### 3. **Sunucuyu Çalıştır**

```bash
python server_e2ee.py
```

Veya Uvicorn ile doğrudan:

```bash
uvicorn server_e2ee:app --reload --host 0.0.0.0 --port 8000
```

### 4. **Erişim**

Tarayıcıda açın:
```
http://localhost:8000
```

---

## 🔒 Şifreleme Detayları

### Public Key Cryptography (NaCl Box)
- **Algoritma**: X25519 Elliptic Curve Diffie-Hellman (ECDH)
- **Encryption**: XSalsa20 stream cipher
- **Authentication**: Poly1305 MAC
- **Key Size**: 256-bit

### Akış
1. İstemci keypair oluşturur
2. Public key sunucuya gönderilir
3. Mesaj, alıcının public key'i ile şifrelenir
4. Sunucu şifrelenmiş mesajı diğer istemcilere yönlendirir
5. İstemci, private key ile mesajı şifre çözer

```
Alice                          Server                        Bob
  |                              |                           |
  |------ pubKeyA --------->      |                           |
  |                              |<----- pubKeyB -----        |
  |                              |<----- pubKeyB -----        |
  |                              |                           |
  |------ EncryptedMsg(B) -->     |------ EncryptedMsg(B) --> |
  |                              |                           |
  |                              Şifreli veri sadece         |
  |                              B tarafından açılabilir     |
```

---

## 📝 API Endpoints

### REST

**POST /create-room**
```json
{
  "room_code": "ABC123",
  "status": "success"
}
```

**GET /room/{room_code}/info**
```json
{
  "room_code": "ABC123",
  "user_count": 2,
  "message_count": 15,
  "status": "active"
}
```

### WebSocket

**Connection**: `ws://localhost:8000/ws/{room_code}`

#### Mesaj Formatları

**Init (Bağlantı Başlatma)**
```json
{
  "type": "init",
  "public_key": "base64_encoded_public_key"
}
```

**Init Response**
```json
{
  "type": "init_response",
  "user_id": "abc12345",
  "public_keys": {
    "user1": "pubkey1_base64",
    "user2": "pubkey2_base64"
  }
}
```

**Message (Şifreli Mesaj)**
```json
{
  "type": "message",
  "encrypted": "base64_encrypted_data",
  "nonce": "base64_nonce"
}
```

**User Joined**
```json
{
  "type": "user_joined",
  "user_id": "newuser",
  "public_key": "pubkey_base64"
}
```

**User Left**
```json
{
  "type": "user_left",
  "user_id": "user123",
  "message": "👤 Kullanıcı ayrıldı"
}
```

---

## 🔐 Güvenlik Notları

### ✅ Yapılan Doğru Şeyler
- Client-side encryption (sunucu hiç plaintext görmez)
- Modern cryptography (TweetNaCl.js)
- Random nonce kullanımı
- Authenticated encryption (AEAD)

### ⚠️ Gelecek İyileştirmeler
- Perfect Forward Secrecy (PFS) - ephemeral keys
- Message signing (non-repudiation)
- Key rotation mekanizması
- Double Ratchet Algorithm (Signal Protocol)
- Metadata şifreleme (header şifrelemesi)
- Rate limiting
- Input validation & sanitization
- HTTPS/WSS zorunlu hale getirme

### 🚨 Üretim Öncesi Checklist
```
[ ] HTTPS/WSS kullan (HTTP tarafından erişilebilir olmasın)
[ ] CORS konfigürasyonu
[ ] Rate limiting
[ ] Input validation
[ ] SQL injection koruması (NoSQL injections)
[ ] XSS koruması
[ ] CSRF token'ları
[ ] Authentication (OAuth2, JWT)
[ ] Encryption at rest (database)
[ ] Key management system
[ ] Audit logging
[ ] DDoS protection
```

---

## 🎨 Özelleştirme

### Tema Değiştir

`index_e2ee.html` içinde CSS variables'ı değiştir:

```css
:root {
    --primary: #0f172a;      /* Ana renk */
    --accent: #06b6d4;        /* Accent renk */
    --success: #10b981;       /* Success */
    --error: #ef4444;         /* Error */
}
```

### Sunucu Portunu Değiştir

```bash
uvicorn server_e2ee:app --port 3000
```

---

## 🚀 Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY server_e2ee.py .
COPY static/ ./static/

CMD ["uvicorn", "server_e2ee:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Railway / Heroku / Render

1. `requirements.txt` ekle
2. `Procfile` oluştur:
   ```
   web: uvicorn server_e2ee:app --host 0.0.0.0 --port $PORT
   ```

### Production Best Practices

```python
# HTTPS kullan
# CORS ayarla
# Uvicorn workers artır
# Reverse proxy (Nginx) kullan
# Database şifrele
# Environment variables ile secrets tut
```

---

## 📊 Mimarisi

```
┌─────────────────────────────────────────────┐
│              Web Tarayıcı                    │
│  (TweetNaCl.js, WebSocket Client)           │
└─────────────────────────────────────────────┘
                    │ WSS
                    │ (şifrelenmiş)
                    │
┌─────────────────────────────────────────────┐
│         FastAPI WebSocket Server            │
│  ┌─────────────────────────────────────┐   │
│  │    Rooms (session yönetimi)        │   │
│  ├─────────────────────────────────────┤   │
│  │    Public Key Store                 │   │
│  ├─────────────────────────────────────┤   │
│  │    Message Relay (şifrelenmiş)      │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

---

## 🧪 Test Etme

### Birden Fazla Tab'ta Test Et
1. İlk tab: Yeni oda oluştur
2. İkinci tab: Oda kodunu gir, katıl
3. Her iki tab'da mesaj gönder

### Console'da Debug
```javascript
secureChat.keyPair       // KeyPair check
secureChat.userId        // User ID
secureChat.otherPublicKeys  // Connected users
```

---

## 📚 Referanslar

- **TweetNaCl.js**: https://tweetnacl.js.org/
- **NaCl Box**: https://nacl.cr.yp.to/box.html
- **FastAPI WebSockets**: https://fastapi.tiangolo.com/advanced/websockets/
- **Signal Protocol**: https://signal.org/docs/

---

## 📄 Lisans

MIT License - Özgürce kullan ve özelleştir

---

## 🤝 Katkılar

Hata bildirimi veya feature suggestions hoştur!

---

## ⚡ Quick Commands

```bash
# Sunucuyu başlat
python server_e2ee.py

# Oto-reload ile başlat
uvicorn server_e2ee:app --reload

# Production ortamında başlat (4 workers)
uvicorn server_e2ee:app --workers 4 --host 0.0.0.0

# Belirli port'ta başlat
uvicorn server_e2ee:app --port 3000
```

---

**Açık kaynaklı, modern ve güvenlikli.** 🔐

Made with ❤️ for privacy enthusiasts
