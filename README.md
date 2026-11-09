# Videomatik — Evrensel Video & Ses İndirici (Web, Mobil & Masaüstü)

Python, **CustomTkinter**, **yt-dlp** ve **Modern Web (PWA)** teknolojileriyle geliştirilmiş karanlık tema (Dark Mode) video ve ses indirme aracı.

---

## 🌐 1. Web & Mobil Sürüm (Tarayıcıdan Kullanım)

Telefonunuzdan (Android / iPhone) veya herhangi bir bilgisayardan kurulum yapmadan web sitesi olarak kullanabilirsiniz:

- **GitHub Pages Web Adresi:** **[https://demir468.github.io/Videomatik/](https://demir468.github.io/Videomatik/)**
  *(Mobil tarayıcınızda açıp **"Ana Ekrana Ekle"** seçeneğiyle telefonunuza uygulama kısayolu olarak ekleyebilirsiniz!)*
- **Aynı Wi-Fi Ağında Tam `yt-dlp` Sunucusu:** Bilgisayarınızda `Web_Sitesi_Baslat.bat` dosyasına çift tıkladığınızda ekranda beliren `http://192.168.1.x:8000` adresini telefonunuzun tarayıcısına yazarak 1000+ siteden doğrudan telefonunuza MP4/MP3 indirebilirsiniz.
- **Bulutta 7/24 Ücretsiz Python Sunucusu (Render):** [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Demir468/Videomatik)

---

## 💻 2. Windows Masaüstü Uygulaması (.exe)

Bilgisayarınızda Python kurulu olmasına gerek kalmadan doğrudan uygulama (`.exe`) olarak indirmek için:

1. **[Son Sürümü İndir (Videomatik.exe)](https://github.com/Demir468/Videomatik/releases/latest)** sayfasına gidin ve **`Videomatik.exe`** dosyasını indirin.
2. İndirdiğiniz **`Videomatik.exe`** dosyasına çift tıklayarak programı açın.
3. Uygulamanın sağ üst köşesindeki **"Masaüstüne Kısayol Ekle"** butonuna tıklayarak Masaüstünüze ikonlu uygulama kısayolunu ekleyin!

---

## Özellikler

- **Mobil & Masaüstü Uyumlu:** Hem telefon tarayıcısında çalışan PWA web arayüzü (`docs/index.html` & `web_app.py`) hem de yerel Windows masaüstü uygulaması (`app.py`).
- **1000+ Platform Desteği:** `yt-dlp` altyapısı ile herkese açık ve DRM koruması olmayan video sitelerinden (YouTube, TikTok, Vimeo, Dailymotion, X/Twitter, Reddit, Twitch klipleri vb.) indirme.
- **Format Seçimi:**
  - `MP4 (Video + Ses)`
  - `MP3 (Sadece Ses - 192 kbps)`
  - `M4A (Sadece Ses - Orijinal Akış)`
- **Çözünürlük Seçimi:** `4K (2160p)`, `2K (1440p)`, `1080p (Full HD)`, `720p (HD)`, `480p (SD)`, `360p` ve `En İyi Kalite (Otomatik)`.
- **Gömülü FFmpeg Desteği:** Sistemde harici FFmpeg kurulu olmasa bile `imageio-ffmpeg` paketiyle yüksek çözünürlüklü ayrı video ve ses akışlarını otomatik birleştirir ve MP3 dönüşümü yapar.
- **Çerez / Oturum Desteği:** YouTube bot doğrulaması veya yaş kısıtlamalı videolar için `cookies.txt` ve tarayıcı oturumu desteği.

## Yasal Uyarı
Bu araç yalnızca herkese açık, telif hakkı ihlali oluşturmayan ve DRM (Dijital Haklar Yönetimi / Widevine, FairPlay vb.) şifrelemesi bulunmayan medya içerikleri için eğitim ve kişisel kullanım amacıyla geliştirilmiştir.
