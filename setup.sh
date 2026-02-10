#!/bin/bash

# 🔐 SecureChat - E2EE ChatBox Kurulum Script

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          🔐 SecureChat E2EE ChatBox - Setup Wizard            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Klasör yapısı kontrolü
echo "[*] Klasör yapısı kontrol ediliyor..."
mkdir -p static

echo "[✓] static/ klasörü oluşturuldu"

# Dosya kontrolü
if [ ! -f "requirements.txt" ]; then
    echo "[!] requirements.txt bulunamadı!"
    exit 1
fi

if [ ! -f "index_e2ee.html" ]; then
    echo "[!] index_e2ee.html bulunamadı!"
    exit 1
fi

if [ ! -f "server_e2ee.py" ]; then
    echo "[!] server_e2ee.py bulunamadı!"
    exit 1
fi

echo "[✓] Tüm dosyalar kontrol edildi"
echo ""

# HTML dosyasını static klasörüne taşı
echo "[*] HTML dosyası static klasörüne taşınıyor..."
cp index_e2ee.html static/
echo "[✓] HTML taşındı: static/index_e2ee.html"
echo ""

# Virtual environment kontrolü
if [ ! -d "venv" ]; then
    echo "[*] Python virtual environment oluşturuluyor..."
    python3 -m venv venv
    echo "[✓] venv/ oluşturuldu"
else
    echo "[✓] venv/ zaten mevcut"
fi

echo ""
echo "[*] Virtual environment aktivasyonu..."
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate

echo "[✓] venv aktif"
echo ""

# Dependencies kurulumu
echo "[*] Python dependencies kuruluyor..."
pip install -q -r requirements.txt
echo "[✓] Dependencies kuruldu"
echo ""

# Yapılandırma
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "⚙️  YAPIKLANDIRMA"
echo ""

read -p "Sunucunun çalışacağı port [8000]: " PORT
PORT=${PORT:-8000}

read -p "Sunucunun bind edileceği host [0.0.0.0]: " HOST
HOST=${HOST:-0.0.0.0}

echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "✅ KURULUM BAŞARILI!"
echo ""
echo "📋 Kurulum Özeti:"
echo "  • Python dependencies: ✓"
echo "  • Klasör yapısı: ✓"
echo "  • Static dosyalar: ✓"
echo ""
echo "🚀 Sunucuyu Başlatmak İçin:"
echo ""
echo "  Seçenek 1 (Otomatik):"
echo "    python server_e2ee.py --port $PORT --host $HOST"
echo ""
echo "  Seçenek 2 (Uvicorn):"
echo "    uvicorn server_e2ee:app --reload --host $HOST --port $PORT"
echo ""
echo "  Seçenek 3 (Production):"
echo "    uvicorn server_e2ee:app --workers 4 --host $HOST --port $PORT"
echo ""
echo "🌐 Erişim:"
echo "  http://$HOST:$PORT"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📖 Daha fazla bilgi için README.md'yi oku"
echo ""
