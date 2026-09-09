# Gold Signal Bot (XAUUSD M5, RSI+MACD -> Telegram)

Bot ini **tidak melakukan auto-entry**. Dia cuma memantau candle XAUUSD M5,
menghitung RSI+MACD, dan kirim sinyal (entry, SL, TP) ke Telegram. Kamu yang
entry manual di MT5.

Jalan otomatis di server GitHub (gratis) — bukan di HP/PC kamu, jadi tidak
perlu nyala 24 jam.

## Cara Setup (sekali saja)

### 1. Buat akun GitHub (kalau belum punya)
https://github.com/join — gratis.

### 2. Buat repository baru
- Klik "New repository"
- Pilih **Public** (biar dapat jatah menit Actions gratis tanpa batas —
  kalau Private, jatah gratisnya cuma 2000 menit/bulan dan bisa habis)
- Upload semua file dalam folder ini ke repo tersebut (drag & drop lewat
  browser juga bisa, tidak perlu command line)

### 3. Daftar API key data harga (gratis)
- Buka https://twelvedata.com/, daftar akun gratis
- Ambil API Key dari dashboard

### 4. Siapkan Bot Telegram (kalau belum ada dari sebelumnya)
- Chat `@BotFather` di Telegram > buat bot baru > catat **Bot Token**
- Start chat ke bot kamu, buka
  `https://api.telegram.org/bot<TOKEN>/getUpdates` untuk ambil **Chat ID**

### 5. Masukkan 3 Secret ke GitHub
Di repo: **Settings > Secrets and variables > Actions > New repository secret**
Tambahkan tiga secret ini:
- `TWELVEDATA_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### 6. Selesai
Workflow otomatis jalan tiap 5 menit. Untuk tes langsung tanpa nunggu:
buka tab **Actions** di repo > pilih "Gold Signal Bot" > **Run workflow**.

## Catatan Penting

- Harga di sinyal ini berdasarkan candle close TwelveData, bukan harga
  langsung dari broker MT5 kamu — bisa selisih sedikit. Selalu cek harga
  aktual sebelum entry manual.
- Jadwal `*/5 * * * *` di GitHub Actions itu jadwal terjadwal, bukan
  real-time presisi — kadang bisa delay beberapa menit saat traffic
  GitHub sedang padat.
- SL/TP default: 3 USD / 6 USD dari harga entry. Ubah nilai `SL_USD` dan
  `TP_USD` di `gold_signal_bot.py` sesuai gaya trading kamu.
- Strategi ini sama persis dengan EA MT5 yang sudah dibuat sebelumnya
  (MACD cross + filter RSI di atas/bawah 50), cuma versi sinyal-saja.
