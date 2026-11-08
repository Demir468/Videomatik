# Videomatik — Evrensel Video & Ses İndirici

Python, **CustomTkinter** ve **yt-dlp** kullanılarak geliştirilmiş modern karanlık tema (Dark Mode) arayüzlü masaüstü video ve ses indirme uygulaması.

---

## İndir ve Hemen Kullan (Windows)

Bilgisayarınızda Python kurulu olmasına gerek kalmadan doğrudan uygulama (`.exe`) olarak indirmek için:

1. **[Son Sürümü İndir (Videomatik.exe)](https://github.com/Demir468/Videomatik/releases/latest)** sayfasına gidin ve **`Videomatik.exe`** dosyasını indirin.
2. İndirdiğiniz **`Videomatik.exe`** dosyasına çift tıklayarak programı açın.
3. Uygulamanın sağ üst köşesindeki **"Masaüstüne Kısayol Ekle"** butonuna tıklayarak Masaüstünüze ikonlu uygulama kısayolunu ekleyin!

---

## Özellikler

- **1000+ Platform Desteği:** `yt-dlp` altyapısı ile herkese açık ve DRM koruması olmayan video sitelerinden (YouTube, Vimeo, Dailymotion, X/Twitter, Reddit, Twitch klipleri vb.) indirme.
- **Format Seçimi:**
  - `MP4 (Video + Ses)`
  - `MP3 (Sadece Ses - 192 kbps)`
  - `M4A (Sadece Ses - Orijinal Akış)`
- **Çözünürlük Seçimi:** `4K (2160p)`, `2K (1440p)`, `1080p (Full HD)`, `720p (HD)`, `480p (SD)`, `360p` ve `En İyi Kalite (Otomatik)`.
- **Gömülü FFmpeg Desteği:** Sistemde harici FFmpeg kurulu olmasa bile `imageio-ffmpeg` paketiyle yüksek çözünürlüklü ayrı video ve ses akışlarını otomatik birleştirir ve MP3 dönüşümü yapar.
- **Tek Tıkla Masaüstü Kısayolu:** Uygulama içindeki **"Masaüstüne Kısayol Ekle"** butonu ile özel ikonlu Masaüstü kısayolu oluşturma.
- **Video Önizleme:** İndirme öncesinde video başlığı, kaynak/kanal, süre, mevcut çözünürlükler ve kapak fotoğrafı (thumbnail) görüntüleme.
- **Tarayıcı Uyumluluğu & Proxy Desteği:** `curl-cffi` ile modern tarayıcı TLS el sıkışması ve isteğe bağlı HTTP/SOCKS5 Proxy desteği.
- **Canlı İlerleme Çubuğu:** Anlık yüzde, hız, kalan süre (ETA) ve indirmeyi iptal etme butonu.

---

## Kaynak Koddan Çalıştırma (Geliştiriciler İçin)

Projeyi kaynak kod olarak indirip çalıştırmak isterseniz:
1. Klasör içindeki **`Kurulum_ve_Kisayol.bat`** dosyasına çift tıklamanız yeterlidir (otomatik olarak `.venv` kurar ve Masaüstünüze **Videomatik** kısayolunu ekler).
2. Veya terminal üzerinden:
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
