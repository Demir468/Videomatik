# Videomatik — Evrensel Video & Ses İndirici

Python, **CustomTkinter** ve **yt-dlp** kullanılarak geliştirilmiş modern karanlık tema (Dark Mode) arayüzlü masaüstü video ve ses indirme uygulaması.

## Özellikler

- **1000+ Platform Desteği:** `yt-dlp` altyapısı ile herkese açık ve DRM koruması olmayan video sitelerinden (YouTube, Vimeo, Dailymotion, X/Twitter, Reddit, Twitch klipleri vb.) indirme.
- **Format Seçimi:**
  - `MP4 (Video + Ses)`
  - `MP3 (Sadece Ses - 192 kbps)`
  - `M4A (Sadece Ses - Orijinal Akış)`
- **Çözünürlük Seçimi:** `4K (2160p)`, `2K (1440p)`, `1080p (Full HD)`, `720p (HD)`, `480p (SD)`, `360p` ve `En İyi Kalite (Otomatik)`.
- **Gömülü FFmpeg Desteği:** Sistemde harici FFmpeg kurulu olmasa bile `imageio-ffmpeg` paketiyle yüksek çözünürlüklü ayrı video ve ses akışlarını otomatik birleştirir ve MP3 dönüşümü yapar.
- **Video Önizleme:** İndirme öncesinde video başlığı, kaynak/kanal, süre, mevcut çözünürlükler ve kapak fotoğrafı (thumbnail) görüntüleme.
- **Tarayıcı Uyumluluğu & Proxy Desteği:** `curl-cffi` ile modern tarayıcı TLS el sıkışması ve isteğe bağlı HTTP/SOCKS5 Proxy desteği.
- **Canlı İlerleme Çubuğu:** Anlık yüzde, hız, kalan süre (ETA) ve indirmeyi iptal etme butonu.

## Kurulum ve Çalıştırma

### Hızlı Başlangıç (Windows)
`baslat.bat` dosyasına çift tıklayın. Eğer sanal ortam (`.venv`) henüz kurulmamışsa otomatik olarak oluşturup gerekli kütüphaneleri yükleyecek ve uygulamayı başlatacaktır.

### Manuel Kurulum (Terminal)
```bash
git clone https://github.com/Demir468/Videomatik.git
cd Videomatik
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Yasal Uyarı
Bu araç yalnızca herkese açık, telif hakkı ihlali oluşturmayan ve DRM (Dijital Haklar Yönetimi / Widevine, FairPlay vb.) şifrelemesi bulunmayan medya içerikleri için eğitim ve kişisel kullanım amacıyla geliştirilmiştir.
