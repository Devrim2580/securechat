# 🔐 SecureChat E2EE - Başlangıç Kılavuzu

## 📦 Proje Yapısı

```
SecureChat/
├── server_e2ee.py           # FastAPI Backend - WebSocket & E2EE
├── index_e2ee.html          # Frontend - TweetNaCl.js ile şifreleme
├── requirements.txt         # Python dependencies
├── setup.sh                 # Linux/Mac kurulum
├── setup.bat                # Windows kurulum
├── README.md                # Detaylı dokümantasyon
└── ADVANCED_FEATURES.md     # İleri seviye özellikler & improvements
```

---

## ⚡ Hızlı Başlangıç (5 dakika)

### Linux / macOS

```bash
# 1. Kurulum dosyasını çalıştır
chmod +x setup.sh
./setup.sh

# 2. Sunucuyu başlat (otomatik yapılır, ya da manuel:)
python server_e2ee.py

# 3. Tarayıcı açıp git
open http://localhost:8000
```

### Windows

```cmd
# 1. Setup'ı çalıştır
setup.bat

# 2. Yazılı talimatları takip et
```

### Manual (Herhangi bir platform)

```bash
# 1. Virtual environment oluştur
python -m venv venv

# 2. Aktif et
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate.bat       # Windows

# 3. Dependencies kur
pip install -r requirements.txt

# 4. Static klasörü oluştur
mkdir static
cp index_e2ee.html static/

# 5. Sunucuyu başlat
python server_e2ee.py
# veya
uvicorn server_e2ee:app --reload --host 0.0.0.0 --port 8000
```

---

## 🎯 Özellikler & Açıklama

### ✅ Yapılan Şey: End-to-End Encryption (E2EE)

**Basit Açıklama:**
- Alice mesajını **şifreler** (sadece Bob'un public key'i ile)
- Server **şifreli metni görür ama açamaz**
- Bob'a gönderilen mesaj **hala şifreli**
- Bob mesajı **açar (sadece o açabilir)**

```
Alice                    Server                   Bob
  │                        │                       │
  │ Mesaj: "Merhaba"       │                       │
  │                        │                       │
  │ [Encrypt with Bob's    │                       │
  │  public key]           │                       │
  │                        │                       │
  │ Şifrelenmiş: ###...    │                       │
  ├────────────────────────►                       │
  │                        │                       │
  │                    Sunucu sadece              │
  │                    şifreli veriyi              │
  │                    görür/iletir              │
  │                        │                       │
  │                        ├──────────────────────►│
  │                        │                       │
  │                        │      [Decrypt with    │
  │                        │       own private    │
  │                        │       key]           │
  │                        │                       │
  │                        │   "Merhaba" ✓       │
```

### 🔐 Şifreleme Detayları

**Algoritma Stack:**
- **Key Exchange**: X25519 (Elliptic Curve DH)
- **Encryption**: XSalsa20 (stream cipher)
- **Authentication**: Poly1305 (MAC)
- **Implementation**: TweetNaCl.js (browser), NaCl (Python)

**Güvenlik Seviyesi:** 256-bit (quantumcomputing tarafından henüz kırılamaz)

---

## 🎮 Kullanım

### 1. Yeni Oda Oluştur

```
┌─────────────────────┐
│ SecureChat          │
├─────────────────────┤
│ [➕ Yeni Oda]       │
│                     │
│ Oda Kodu: ABC123    │
│ [📋 Kopyala]        │
└─────────────────────┘
```

**Ne oluşur:**
- Unique 6-digit oda kodu
- Her oda kendine özel şifreleme context'i
- URL'de paylaş: `localhost:8000?room=ABC123`

### 2. Mevcut Odaya Katıl

```
┌─────────────────────┐
│ Oda kodunu girin:   │
│ [ABC123          ]  │
│ [Katıl]             │
└─────────────────────┘
```

### 3. Mesaj Gönder

```
┌─────────────────────────────┐
│ Çevrimiçi: 2 ✓              │
├─────────────────────────────┤
│ ┌─────────────────────────┐ │
│ │ Merhaba!              │ │  ← Alıcıdan
│ │ abc12... | 2:45 PM   │ │
│ ├─────────────────────────┤ │
│ │         Sen: Merhabalar! │ │  ← Senin mesajın
│ │         2:46 PM ✓       │ │
│ └─────────────────────────┘ │
├─────────────────────────────┤
│ [Mesaj yazın...          ] ► │
└─────────────────────────────┘
```

**Arkaplanda Neler Oluyor:**
```javascript
// 1. Mesaj türünü yaz
"Merhaba"

// 2. TweetNaCl.js şifreler
Encrypted: "SoJe8N/x4K2+..."
Nonce: "aB3cD4eF5gH6..."

// 3. Server'a gönder (şifreli)
{
  type: "message",
  encrypted: "SoJe8N/x4K2+...",
  nonce: "aB3cD4eF5gH6..."
}

// 4. Alıcı açar (sadece o yapabilir)
Decrypted: "Merhaba"
```

---

## 🔍 Technical Detaylar

### Frontend (JavaScript)
```javascript
// Public key pair oluştur
const keyPair = nacl.box.keyPair();

// Mesajı şifrele
const encrypted = nacl.box(
  message,
  nonce,
  recipientPublicKey,
  senderSecretKey
);

// WebSocket ile gönder
ws.send(JSON.stringify({
  type: "message",
  encrypted: btoa(encrypted),
  nonce: btoa(nonce)
}));
```

### Backend (Python)
```python
# WebSocket'den şifreli mesajı al
data = await websocket.receive_text()
message_data = json.loads(data)

# Diğer kullanıcılara olduğu gibi yolla
# (Sunucu açamaz, fork eder)
for user in rooms[room_code]["users"]:
    await user["websocket"].send_text(json.dumps({
        "type": "message",
        "encrypted": message_data.get("encrypted"),
        "nonce": message_data.get("nonce"),
        "sender_public_key": sender_public_key
    }))

# Alıcı açar:
decrypted = nacl.box.open(
    encrypted,
    nonce,
    sender_public_key,
    recipient_secret_key
)
```

---

## ⚙️ Yapılandırma

### Port Değiştir

```bash
uvicorn server_e2ee:app --port 3000
```

### Environment Variables (Production)

```bash
export DATABASE_URL="postgresql://user:pass@localhost/securechat"
export ENCRYPTION_KEY="your-encryption-key"
export LOG_LEVEL="INFO"
```

### HTTPS/WSS (Production)

```python
# Nginx reverse proxy örneği
location / {
    proxy_pass http://localhost:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

---

## 🧪 Test Etme

### 1. Lokal Olarak

```bash
# Terminal 1: Sunucu
python server_e2ee.py

# Terminal 2: İstemci test
curl http://localhost:8000/create-room

# Terminal 3: WebSocket test
wscat -c ws://localhost:8000/ws/ABC123
```

### 2. Birden Fazla Browser Tab'ta

```
Tab 1: http://localhost:8000
  └─ Yeni Oda Oluştur
     └─ Room Code: ABC123

Tab 2: http://localhost:8000
  └─ ABC123 kodunu gir
     └─ Katıl
     
Tab 3: http://localhost:8000
  └─ Aynı kodu gir
     └─ 3 kişi aynı odada
```

### 3. Network Inspection

Browser DevTools → Network tab
- WS bağlantısını gözlemle
- Mesajların şifreli olduğunu kontrol et (random data)
- Sunucu plaintext hiç göndermiyor

---

## 🚨 Bilinen Limitasyonlar & TODOs

### Güvenlik (Uyarı ⚠️)
- [ ] Metadata şifrelemesi yok (kim kime mesaj gönderdiği görünür)
- [ ] Perfect Forward Secrecy yok (static keys kullanıyor)
- [ ] Message signing yok (non-repudiation eksik)
- [ ] Key rotation mekanizması yok
- [ ] HTTPS/WSS gerekli (HTTP'de açık!)

### Fonksiyonelite
- [ ] Mesaj history yok (her yeni oturum temiz başlar)
- [ ] Persistence yok (sunucu restart = oda silindi)
- [ ] User accounts yok (anonim)
- [ ] File transfer yok

### Refactor Gerekli
- [ ] Database entegrasyonu (SQLAlchemy)
- [ ] Logging system
- [ ] Error handling iyileştirilmesi
- [ ] Rate limiting
- [ ] Input validation

---

## 📚 Sonraki Adımlar

### Beginner'lar İçin
1. ✅ Kurulumu tamamla
2. ✅ Lokal olarak test et
3. ✅ README.md'yi oku
4. ➜ ADVANCED_FEATURES.md'ye bak
5. ➜ Database entegrasyonu ekle

### Intermediate'lar İçin
1. PostgreSQL entegrasyonu
2. JWT authentication
3. Message persistence
4. Rate limiting
5. Deployment (Docker)

### Advanced'ler İçin
1. Perfect Forward Secrecy (PFS)
2. Double Ratchet Algorithm
3. E2EE file transfer
4. WebRTC voice/video
5. Kubernetes scaling

---

## 🆘 Troubleshooting

### "Module not found" hatası
```bash
pip install -r requirements.txt
```

### "Port already in use"
```bash
# Port numarasını değiştir
uvicorn server_e2ee:app --port 8001
```

### WebSocket bağlantısı başarısız
```
1. Server çalışıyor mu? (python server_e2ee.py)
2. Port doğru mu? (8000)
3. URL doğru mu? (ws://localhost:8000/ws/ROOMCODE)
```

### Mesajlar şifreli görünüyor ama açılamıyor
```
1. Public keys paylaşıldı mı?
2. Nonce doğru mu?
3. Recipient public key doğru mu?
```

---

## 📞 İletişim & Katkı

- **Issue**: Hata bildirerek yardım et
- **Pull Request**: Kod öner
- **Discussion**: Soru sor

---

## 📜 Lisans

MIT - Özgürce kullan, modifiye et, dağıt

---

## 🙏 Teşekkürler

- **TweetNaCl.js** - Harika crypto library
- **FastAPI** - Modern web framework
- **NaCl** - Crypto reference implementation

---

**Enjoy secure chatting! 🔐**

Made with ❤️ for privacy enthusiasts and developers
