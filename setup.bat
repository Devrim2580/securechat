@echo off
REM 🔐 SecureChat - E2EE ChatBox Setup for Windows

cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║          🔐 SecureChat E2EE ChatBox - Setup Wizard            ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Klasör yapısı
echo [*] Klasör yapısı kontrol ediliyor...
if not exist "static" mkdir static
echo [✓] static\ klasörü oluşturuldu
echo.

REM Dosya kontrolü
if not exist "requirements.txt" (
    echo [!] requirements.txt bulunamadı!
    pause
    exit /b 1
)

if not exist "index_e2ee.html" (
    echo [!] index_e2ee.html bulunamadı!
    pause
    exit /b 1
)

if not exist "server_e2ee.py" (
    echo [!] server_e2ee.py bulunamadı!
    pause
    exit /b 1
)

echo [✓] Tüm dosyalar kontrol edildi
echo.

REM HTML dosyasını taşı
echo [*] HTML dosyası static klasörüne taşınıyor...
copy index_e2ee.html static\ >nul 2>&1
echo [✓] HTML taşındı: static\index_e2ee.html
echo.

REM Virtual environment
if not exist "venv" (
    echo [*] Python virtual environment oluşturuluyor...
    python -m venv venv
    echo [✓] venv\ oluşturuldu
) else (
    echo [✓] venv\ zaten mevcut
)

echo.
echo [*] Virtual environment aktivasyonu...
call venv\Scripts\activate.bat
echo [✓] venv aktif
echo.

REM Dependencies
echo [*] Python dependencies kuruluyor...
pip install -q -r requirements.txt
echo [✓] Dependencies kuruldu
echo.

REM Yapılandırma
echo ════════════════════════════════════════════════════════════════
echo.
echo ⚙️  YAPIKLANDIRMA
echo.
echo Varsayılan: Port=8000, Host=0.0.0.0
echo.
set /p PORT="Port numarası [8000]: "
if "%PORT%"=="" set PORT=8000

set /p HOST="Host adresi [0.0.0.0]: "
if "%HOST%"=="" set HOST=0.0.0.0

echo.
echo ════════════════════════════════════════════════════════════════
echo.
echo ✅ KURULUM BAŞARILI!
echo.
echo 📋 Kurulum Özeti:
echo   • Python dependencies: ✓
echo   • Klasör yapısı: ✓
echo   • Static dosyalar: ✓
echo.
echo 🚀 Sunucuyu Başlatmak İçin:
echo.
echo   Seçenek 1 (Otomatik):
echo     python server_e2ee.py
echo.
echo   Seçenek 2 (Uvicorn):
echo     uvicorn server_e2ee:app --reload --host %HOST% --port %PORT%
echo.
echo   Seçenek 3 (Production):
echo     uvicorn server_e2ee:app --workers 4 --host %HOST% --port %PORT%
echo.
echo 🌐 Erişim:
echo   http://%HOST%:%PORT%
echo.
echo ════════════════════════════════════════════════════════════════
echo.
echo 📖 Daha fazla bilgi için README.md'yi oku
echo.

echo Sunucuyu şimdi başlatmak istiyor musunuz? (E/H)
set /p RUN="Yanıt: "
if /i "%RUN%"=="E" (
    cls
    echo Sunucu başlatılıyor...
    echo http://%HOST%:%PORT% adresine git
    echo.
    python server_e2ee.py
) else (
    echo Daha sonra başlatabilirsiniz.
    pause
)
