from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any
from urllib.parse import urlparse

import customtkinter as ctk
import requests
import yt_dlp
from PIL import Image

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None

try:
    from yt_dlp.networking.impersonate import ImpersonateTarget
except ImportError:
    ImpersonateTarget = None


# Görünüm ayarları
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


class DownloadCancelledError(Exception):
    """Kullanıcı indirmeyi iptal ettiğinde fırlatılır."""


def get_ffmpeg_path() -> str | None:
    """Sistemdeki veya imageio-ffmpeg içindeki ffmpeg yürütülebilir dosyasını bulur."""
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    if imageio_ffmpeg is not None:
        try:
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            return None
    return None


def strip_ansi(text: str) -> str:
    """yt-dlp çıktılarındaki ANSI renk kodlarını temizler."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def format_duration(seconds: int | float | None) -> str:
    if not seconds:
        return "Bilinmiyor"
    seconds = int(seconds)
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def extract_origin_referer(url: str) -> str:
    """URL'den Referer başlığı için kök alan adını (scheme://host/) çıkarır."""
    try:
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}/"
    except Exception:
        pass
    return url


def get_resource_path(relative_path: str) -> Path:
    """PyInstaller (.exe) veya normal Python çalışmasında dosya yolunu bulur."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_path / relative_path


class VideoDownloaderApp(ctk.CTk):
    """CustomTkinter ve yt-dlp tabanlı masaüstü video ve ses indirme uygulaması."""

    QUALITY_MAP: dict[str, int | None] = {
        "En İyi Kalite (Otomatik)": None,
        "2160p (4K)": 2160,
        "1440p (2K)": 1440,
        "1080p (Full HD)": 1080,
        "720p (HD)": 720,
        "480p (SD)": 480,
        "360p (Düşük)": 360,
    }

    def __init__(self) -> None:
        super().__init__()

        self.title("Videomatik — Evrensel Video & Ses İndirici")
        self.geometry("800x730")
        self.minsize(720, 660)

        icon_path = get_resource_path("assets/icon.ico")
        if icon_path.is_file():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        self.download_dir = str(Path.home() / "Downloads")
        self.cookie_file_path: str = ""
        default_cookie = Path(__file__).resolve().parent / "cookies.txt"
        if default_cookie.is_file():
            self.cookie_file_path = str(default_cookie)

        self.is_downloading = False
        self.cancel_requested = False
        self.current_thumbnail_image: ctk.CTkImage | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Başlık Alanı
        header_frame = ctk.CTkFrame(self, corner_radius=12)
        header_frame.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header_frame,
            text="Videomatik — Video & Ses İndirici",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title_label.grid(row=0, column=0, padx=16, pady=(12, 2), sticky="w")

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="DRM koruması olmayan 1000+ genel video platformundan MP4 veya MP3 olarak indirin",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray70"),
        )
        subtitle_label.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="w")

        shortcut_btn = ctk.CTkButton(
            header_frame,
            text="Masaüstüne Kısayol Ekle",
            width=165,
            height=34,
            fg_color=("gray75", "gray25"),
            hover_color=("gray65", "gray35"),
            command=self.create_desktop_shortcut,
        )
        shortcut_btn.grid(row=0, column=1, rowspan=2, padx=16, pady=12, sticky="e")

        # 2. URL Giriş Alanı
        url_frame = ctk.CTkFrame(self, corner_radius=12)
        url_frame.grid(row=1, column=0, padx=20, pady=8, sticky="ew")
        url_frame.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="Video bağlantısını buraya yapıştırın (https://...)",
            height=40,
            font=ctk.CTkFont(size=14),
        )
        self.url_entry.grid(row=0, column=0, padx=(16, 8), pady=14, sticky="ew")

        paste_btn = ctk.CTkButton(
            url_frame,
            text="Yapıştır",
            width=85,
            height=40,
            fg_color=("gray75", "gray25"),
            hover_color=("gray65", "gray35"),
            command=self.paste_from_clipboard,
        )
        paste_btn.grid(row=0, column=1, padx=4, pady=14)

        self.analyze_btn = ctk.CTkButton(
            url_frame,
            text="Analiz Et",
            width=110,
            height=40,
            font=ctk.CTkFont(weight="bold"),
            command=self.start_analyze,
        )
        self.analyze_btn.grid(row=0, column=2, padx=(4, 16), pady=14)

        # 3. Video Önizleme Kartı
        self.preview_frame = ctk.CTkFrame(self, corner_radius=12)
        self.preview_frame.grid(row=2, column=0, padx=20, pady=8, sticky="nsew")
        self.preview_frame.grid_columnconfigure(1, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)

        self.thumb_label = ctk.CTkLabel(
            self.preview_frame,
            text="Önizleme Yok",
            width=240,
            height=135,
            fg_color=("gray85", "gray17"),
            corner_radius=8,
        )
        self.thumb_label.grid(row=0, column=0, rowspan=3, padx=16, pady=16, sticky="ns")

        info_container = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        info_container.grid(row=0, column=1, padx=(0, 16), pady=16, sticky="nsew")
        info_container.grid_columnconfigure(0, weight=1)

        self.video_title_label = ctk.CTkLabel(
            info_container,
            text="Henüz bir video analiz edilmedi.\nDoğrudan indirebilir veya bilgi görmek için 'Analiz Et'e tıklayabilirsiniz.",
            font=ctk.CTkFont(size=15, weight="bold"),
            justify="left",
            anchor="w",
            wraplength=440,
        )
        self.video_title_label.grid(row=0, column=0, pady=(4, 8), sticky="ew")

        self.video_meta_label = ctk.CTkLabel(
            info_container,
            text="Kanal / Site: -   |   Süre: -",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray70"),
            justify="left",
            anchor="w",
        )
        self.video_meta_label.grid(row=1, column=0, pady=2, sticky="ew")

        self.available_res_label = ctk.CTkLabel(
            info_container,
            text="Mevcut Çözünürlükler: -",
            font=ctk.CTkFont(size=12),
            text_color=("gray45", "gray65"),
            justify="left",
            anchor="w",
        )
        self.available_res_label.grid(row=2, column=0, pady=(6, 0), sticky="ew")

        # 4. Format, Çözünürlük, Proxy ve Kayıt Klasörü Seçimi
        options_frame = ctk.CTkFrame(self, corner_radius=12)
        options_frame.grid(row=3, column=0, padx=20, pady=8, sticky="ew")
        options_frame.grid_columnconfigure((0, 1), weight=1)

        # Format Seçimi
        format_label = ctk.CTkLabel(
            options_frame,
            text="Format Türü:",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        format_label.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        self.format_var = ctk.StringVar(value="MP4 (Video + Ses)")
        self.format_menu = ctk.CTkOptionMenu(
            options_frame,
            values=["MP4 (Video + Ses)", "MP3 (Sadece Ses)", "M4A (Sadece Ses - Orijinal)"],
            variable=self.format_var,
            height=34,
            command=self._on_format_change,
        )
        self.format_menu.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")

        # Çözünürlük Seçimi
        quality_label = ctk.CTkLabel(
            options_frame,
            text="Çözünürlük / Kalite:",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        quality_label.grid(row=0, column=1, padx=16, pady=(12, 4), sticky="w")

        self.quality_var = ctk.StringVar(value="1080p (Full HD)")
        self.quality_menu = ctk.CTkOptionMenu(
            options_frame,
            values=list(self.QUALITY_MAP.keys()),
            variable=self.quality_var,
            height=34,
        )
        self.quality_menu.grid(row=1, column=1, padx=16, pady=(0, 10), sticky="ew")

        # Proxy Ayarı (İsteğe Bağlı)
        proxy_row = ctk.CTkFrame(options_frame, fg_color="transparent")
        proxy_row.grid(row=2, column=0, columnspan=2, padx=16, pady=(0, 8), sticky="ew")
        proxy_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            proxy_row,
            text="Proxy (İsteğe Bağlı):",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        self.proxy_entry = ctk.CTkEntry(
            proxy_row,
            placeholder_text="Boş bırakılabilir veya örn: http://127.0.0.1:8080 ya da socks5://127.0.0.1:1080",
            height=30,
            font=ctk.CTkFont(size=12),
        )
        self.proxy_entry.grid(row=0, column=1, sticky="ew")

        # Çerez / Oturum Ayarı (YouTube Bot Koruması ve Yaş Kısıtlamalı Videolar İçin)
        cookie_row = ctk.CTkFrame(options_frame, fg_color="transparent")
        cookie_row.grid(row=3, column=0, columnspan=2, padx=16, pady=(0, 8), sticky="ew")
        cookie_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            cookie_row,
            text="Çerez / Oturum:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        initial_cookie_mode = (
            "cookies.txt Dosyası Kullan" if self.cookie_file_path else "Kullanma (Varsayılan)"
        )
        self.cookie_var = ctk.StringVar(value=initial_cookie_mode)
        self.cookie_menu = ctk.CTkOptionMenu(
            cookie_row,
            values=[
                "Kullanma (Varsayılan)",
                "cookies.txt Dosyası Kullan",
                "Firefox Oturumunu Kullan",
                "Brave Oturumunu Kullan (Tarayıcı Kapalıyken)",
                "Edge Oturumunu Kullan (Tarayıcı Kapalıyken)",
                "Chrome Oturumunu Kullan (Tarayıcı Kapalıyken)",
                "Opera Oturumunu Kullan (Tarayıcı Kapalıyken)",
            ],
            variable=self.cookie_var,
            height=30,
        )
        self.cookie_menu.grid(row=0, column=1, padx=(0, 6), sticky="ew")

        choose_cookie_btn = ctk.CTkButton(
            cookie_row,
            text="cookies.txt Seç...",
            width=125,
            height=30,
            fg_color=("gray75", "gray25"),
            hover_color=("gray65", "gray35"),
            command=self.choose_cookie_file,
        )
        choose_cookie_btn.grid(row=0, column=2)

        # Kayıt Klasörü Satırı
        folder_row = ctk.CTkFrame(options_frame, fg_color="transparent")
        folder_row.grid(row=4, column=0, columnspan=2, padx=16, pady=(0, 12), sticky="ew")
        folder_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            folder_row,
            text="Kayıt Klasörü:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        self.folder_label = ctk.CTkLabel(
            folder_row,
            text=self.download_dir,
            font=ctk.CTkFont(size=12),
            text_color=("gray35", "gray75"),
            anchor="w",
        )
        self.folder_label.grid(row=0, column=1, padx=4, sticky="ew")

        choose_folder_btn = ctk.CTkButton(
            folder_row,
            text="Değiştir...",
            width=90,
            height=30,
            fg_color=("gray75", "gray25"),
            hover_color=("gray65", "gray35"),
            command=self.choose_directory,
        )
        choose_folder_btn.grid(row=0, column=2, padx=(6, 4))

        open_folder_btn = ctk.CTkButton(
            folder_row,
            text="Klasörü Aç",
            width=90,
            height=30,
            fg_color=("gray75", "gray25"),
            hover_color=("gray65", "gray35"),
            command=self.open_download_directory,
        )
        open_folder_btn.grid(row=0, column=3, padx=(4, 0))

        # 5. İlerleme Çubuğu ve İndir Butonu
        bottom_frame = ctk.CTkFrame(self, corner_radius=12)
        bottom_frame.grid(row=4, column=0, padx=20, pady=(8, 16), sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            bottom_frame,
            text="Hazır",
            font=ctk.CTkFont(size=13),
            anchor="w",
        )
        self.status_label.grid(row=0, column=0, columnspan=2, padx=16, pady=(12, 4), sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(bottom_frame, height=14)
        self.progress_bar.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 12), sticky="ew")
        self.progress_bar.set(0)

        self.download_btn = ctk.CTkButton(
            bottom_frame,
            text="İndirmeyi Başlat",
            height=42,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#1f6aa5",
            hover_color="#144870",
            command=self.start_download,
        )
        self.download_btn.grid(row=2, column=0, padx=(16, 8), pady=(0, 14), sticky="ew")

        self.cancel_btn = ctk.CTkButton(
            bottom_frame,
            text="İptal Et",
            width=110,
            height=42,
            fg_color="#b91c1c",
            hover_color="#7f1d1d",
            state="disabled",
            command=self.cancel_download,
        )
        self.cancel_btn.grid(row=2, column=1, padx=(0, 16), pady=(0, 14))

    def _on_format_change(self, selected_format: str) -> None:
        if "Sadece Ses" in selected_format:
            self.quality_menu.configure(state="disabled")
        else:
            self.quality_menu.configure(state="normal")

    def paste_from_clipboard(self) -> None:
        try:
            clipboard_text = self.clipboard_get().strip()
            if clipboard_text:
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, clipboard_text)
        except Exception:
            pass

    def choose_directory(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.download_dir)
        if selected:
            self.download_dir = selected
            self.folder_label.configure(text=self.download_dir)

    def choose_cookie_file(self) -> None:
        selected = filedialog.askopenfilename(
            title="Netscape formatında cookies.txt dosyası seçin",
            filetypes=[("Metin Dosyaları", "*.txt"), ("Tüm Dosyalar", "*.*")],
        )
        if selected:
            self.cookie_file_path = selected
            self.cookie_var.set("cookies.txt Dosyası Kullan")
            self.status_label.configure(text=f"Çerez dosyası seçildi: {Path(selected).name}")

    def open_download_directory(self) -> None:
        if os.path.isdir(self.download_dir):
            os.startfile(self.download_dir)

    def create_desktop_shortcut(self) -> None:
        """Kullanıcının Masaüstüne ikonlu Videomatik kısayolu (.lnk) oluşturur."""
        if sys.platform != "win32":
            messagebox.showinfo("Bilgi", "Masaüstü kısayolu oluşturma yalnızca Windows'ta desteklenir.")
            return

        try:
            if getattr(sys, "frozen", False):
                target_path = str(Path(sys.executable).resolve())
                arguments = ""
                working_dir = str(Path(sys.executable).resolve().parent)
                icon_loc = target_path
            else:
                python_exe = Path(sys.executable).resolve()
                pythonw_exe = python_exe.with_name("pythonw.exe")
                target_path = str(pythonw_exe if pythonw_exe.is_file() else python_exe)
                script_path = Path(__file__).resolve()
                arguments = f'"{script_path}"'
                working_dir = str(script_path.parent)
                icon_file = get_resource_path("assets/icon.ico")
                icon_loc = str(icon_file) if icon_file.is_file() else target_path

            ps_script = (
                "$desktop = [Environment]::GetFolderPath('Desktop'); "
                "$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desktop 'Videomatik.lnk')); "
                f"$s.TargetPath = '{target_path}'; "
                f"$s.Arguments = '{arguments}'; "
                f"$s.WorkingDirectory = '{working_dir}'; "
                f"$s.IconLocation = '{icon_loc}'; "
                "$s.Description = 'Videomatik - Evrensel Video ve Ses Indirici'; "
                "$s.Save()"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
                check=True,
                creationflags= getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            messagebox.showinfo(
                "Kısayol Oluşturuldu",
                "Masaüstünüze 'Videomatik' uygulama kısayolu başarıyla eklendi!",
            )
        except Exception as exc:
            messagebox.showerror("Hata", f"Kısayol oluşturulurken hata oluştu:\n{exc}")

    def _get_common_ydl_opts(self, url: str, proxy_str: str = "") -> dict[str, Any]:
        """Standart tarayıcı başlıkları, çerez (cookie), yeniden deneme ve bağlantı ayarlarını döndürür."""
        referer = extract_origin_referer(url)
        is_youtube = any(d in url.lower() for d in ("youtube.com", "youtu.be"))

        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "retries": 5,
            "fragment_retries": 5,
            "extractor_retries": 3,
            "socket_timeout": 30,
            "js_runtimes": {"node": {}, "deno": {}},
        }

        if not is_youtube:
            opts["http_headers"] = {
                "User-Agent": DEFAULT_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": referer,
            }
            if ImpersonateTarget is not None:
                try:
                    opts["impersonate"] = ImpersonateTarget("chrome")
                except Exception:
                    pass

        cookie_choice = self.cookie_var.get()
        if cookie_choice == "cookies.txt Dosyası Kullan":
            if self.cookie_file_path and os.path.isfile(self.cookie_file_path):
                opts["cookiefile"] = self.cookie_file_path
        elif "Firefox" in cookie_choice:
            opts["cookiesfrombrowser"] = ("firefox",)
        elif "Brave" in cookie_choice:
            opts["cookiesfrombrowser"] = ("brave",)
        elif "Edge" in cookie_choice:
            opts["cookiesfrombrowser"] = ("edge",)
        elif "Chrome" in cookie_choice:
            opts["cookiesfrombrowser"] = ("chrome",)
        elif "Opera" in cookie_choice:
            opts["cookiesfrombrowser"] = ("opera",)

        if proxy_str:
            opts["proxy"] = proxy_str
        return opts

    def start_analyze(self) -> None:
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Uyarı", "Lütfen önce bir video bağlantısı (URL) girin.")
            return

        proxy_str = self.proxy_entry.get().strip()
        self.analyze_btn.configure(state="disabled", text="Analiz...")
        self.status_label.configure(text="Video bilgileri alınıyor, lütfen bekleyin...")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()

        threading.Thread(
            target=self._analyze_worker,
            args=(url, proxy_str),
            daemon=True,
        ).start()

    def _analyze_worker(self, url: str, proxy_str: str) -> None:
        ydl_opts = self._get_common_ydl_opts(url, proxy_str)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            title = info.get("title") or "Başlıksız Video"
            uploader = info.get("uploader") or info.get("webpage_url_domain") or "Bilinmiyor"
            duration_str = format_duration(info.get("duration"))
            thumb_url = info.get("thumbnail")

            formats = info.get("formats") or []
            heights = sorted(
                {
                    f.get("height")
                    for f in formats
                    if f.get("height") and f.get("vcodec") != "none"
                },
                reverse=True,
            )
            res_text = (
                ", ".join(f"{h}p" for h in heights[:8])
                if heights
                else "Standart Akış (Tek Parça)"
            )

            pil_img = None
            if thumb_url:
                try:
                    headers = {"User-Agent": DEFAULT_USER_AGENT, "Referer": extract_origin_referer(url)}
                    proxies = {"http": proxy_str, "https": proxy_str} if proxy_str else None
                    resp = requests.get(thumb_url, headers=headers, proxies=proxies, timeout=10)
                    resp.raise_for_status()
                    pil_img = Image.open(io.BytesIO(resp.content))
                except Exception:
                    pil_img = None

            self.after(
                0,
                lambda: self._update_preview_ui(
                    title=title,
                    uploader=uploader,
                    duration_str=duration_str,
                    res_text=res_text,
                    pil_img=pil_img,
                ),
            )
        except Exception as exc:
            err_msg = strip_ansi(str(exc))
            self.after(0, lambda: self._on_analyze_error(err_msg))

    def _update_preview_ui(
        self,
        title: str,
        uploader: str,
        duration_str: str,
        res_text: str,
        pil_img: Image.Image | None,
    ) -> None:
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)
        self.analyze_btn.configure(state="normal", text="Analiz Et")

        self.video_title_label.configure(text=title)
        self.video_meta_label.configure(text=f"Kaynak: {uploader}   |   Süre: {duration_str}")
        self.available_res_label.configure(text=f"Mevcut Çözünürlükler: {res_text}")
        self.status_label.configure(text="Video analiz edildi. İndirmeye hazır.")

        if pil_img is not None:
            self.current_thumbnail_image = ctk.CTkImage(
                light_image=pil_img,
                dark_image=pil_img,
                size=(240, 135),
            )
            self.thumb_label.configure(image=self.current_thumbnail_image, text="")
        else:
            self.thumb_label.configure(image=None, text="Önizleme Yok")

    def _on_analyze_error(self, err_msg: str) -> None:
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)
        self.analyze_btn.configure(state="normal", text="Analiz Et")
        self.status_label.configure(text="Analiz başarısız oldu.")

        extra_hint = (
            "Not: DRM korumalı (şifreli) videolar veya oturum açma gerektiren özel içerikler desteklenmez."
        )
        if "10054" in err_msg or "ConnectionResetError" in err_msg:
            extra_hint = (
                "İpucu (Hata 10054 - Bağlantı Sıfırlandı):\n"
                "Hedef site bağlantıyı kapattı veya bu siteye erişim internet servis sağlayıcınız (İSS) "
                "tarafından kısıtlanmış olabilir. Tarayıcıda VPN/Proxy ile giriyorsanız 'Proxy' alanını doldurmayı "
                "veya sistem genelinde VPN açmayı deneyin."
            )
        elif "not a bot" in err_msg or "cookies" in err_msg.lower():
            extra_hint = (
                "İpucu (YouTube Bot Doğrulaması Hatası):\n"
                "1) Bilgisayarınızda VPN açıksa kapatıp tekrar deneyin (YouTube, VPN sunucusu IP'lerinden gelen "
                "oturumsuz istekleri bot olarak engeller).\n"
                "2) VPN kapatmak istemiyorsanız veya video yaş kısıtlamalıysa, tarayıcınıza 'Get cookies.txt LOCALLY' "
                "eklentisini kurup dışa aktardığınız dosyayı arayüzdeki 'cookies.txt Seç...' butonuyla tanıtın "
                "veya 'Çerez / Oturum' menüsünden tarayıcınızı seçin."
            )

        messagebox.showerror(
            "Analiz Hatası",
            f"Video bilgileri alınamadı:\n\n{err_msg}\n\n{extra_hint}",
        )

    def start_download(self) -> None:
        if self.is_downloading:
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Uyarı", "Lütfen indirilecek video bağlantısını girin.")
            return

        proxy_str = self.proxy_entry.get().strip()
        self.is_downloading = True
        self.cancel_requested = False
        self.download_btn.configure(state="disabled")
        self.analyze_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)
        self.status_label.configure(text="İndirme hazırlanıyor...")

        format_choice = self.format_var.get()
        quality_choice = self.quality_var.get()

        threading.Thread(
            target=self._download_worker,
            args=(url, format_choice, quality_choice, proxy_str),
            daemon=True,
        ).start()

    def cancel_download(self) -> None:
        if self.is_downloading:
            self.cancel_requested = True
            self.status_label.configure(text="İndirme iptal ediliyor...")

    def _build_ydl_opts(
        self,
        url: str,
        format_choice: str,
        quality_choice: str,
        proxy_str: str,
    ) -> dict[str, Any]:
        ffmpeg_path = get_ffmpeg_path()
        outtmpl = os.path.join(self.download_dir, "%(title).180B [%(id)s].%(ext)s")

        ydl_opts = self._get_common_ydl_opts(url, proxy_str)
        ydl_opts["outtmpl"] = outtmpl
        ydl_opts["progress_hooks"] = [self._progress_hook]

        if ffmpeg_path:
            ydl_opts["ffmpeg_location"] = ffmpeg_path

        if format_choice == "MP3 (Sadece Ses)":
            ydl_opts["format"] = "bestaudio/best"
            if ffmpeg_path:
                ydl_opts["postprocessors"] = [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ]
        elif format_choice == "M4A (Sadece Ses - Orijinal)":
            ydl_opts["format"] = "bestaudio[ext=m4a]/bestaudio/best"
        else:
            # MP4 (Video + Ses)
            max_height = self.QUALITY_MAP.get(quality_choice)
            if max_height:
                if ffmpeg_path:
                    ydl_opts["format"] = (
                        f"bestvideo[height<={max_height}][ext=mp4]+bestaudio[ext=m4a]/"
                        f"bestvideo[height<={max_height}]+bestaudio/"
                        f"best[height<={max_height}]/best"
                    )
                    ydl_opts["merge_output_format"] = "mp4"
                else:
                    ydl_opts["format"] = f"best[height<={max_height}][ext=mp4]/best[height<={max_height}]/best"
            else:
                if ffmpeg_path:
                    ydl_opts["format"] = (
                        "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
                    )
                    ydl_opts["merge_output_format"] = "mp4"
                else:
                    ydl_opts["format"] = "best[ext=mp4]/best"

        return ydl_opts

    def _progress_hook(self, d: dict[str, Any]) -> None:
        if self.cancel_requested:
            raise DownloadCancelledError("İndirme kullanıcı tarafından iptal edildi.")

        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            ratio = (downloaded / total) if total > 0 else 0.0

            speed_str = strip_ansi(d.get("_speed_str") or "-").strip()
            eta_str = strip_ansi(d.get("_eta_str") or "-").strip()
            percent_display = f"%{ratio * 100:.1f}"

            status_text = f"İndiriliyor: {percent_display}  |  Hız: {speed_str}  |  Kalan Süre: {eta_str}"
            self.after(0, lambda r=ratio, s=status_text: self._update_progress_ui(r, s))

        elif status == "finished":
            self.after(
                0,
                lambda: self._update_progress_ui(
                    1.0, "İndirme tamamlandı, ses ve görüntü birleştiriliyor (FFmpeg)..."
                ),
            )

    def _update_progress_ui(self, ratio: float, status_text: str) -> None:
        self.progress_bar.set(max(0.0, min(1.0, ratio)))
        self.status_label.configure(text=status_text)

    def _download_worker(
        self,
        url: str,
        format_choice: str,
        quality_choice: str,
        proxy_str: str,
    ) -> None:
        ydl_opts = self._build_ydl_opts(url, format_choice, quality_choice, proxy_str)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.after(0, self._on_download_success)
        except DownloadCancelledError:
            self.after(0, self._on_download_cancelled)
        except Exception as exc:
            err_msg = strip_ansi(str(exc))
            self.after(0, lambda: self._on_download_error(err_msg))

    def _reset_buttons(self) -> None:
        self.is_downloading = False
        self.cancel_requested = False
        self.download_btn.configure(state="normal")
        self.analyze_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")

    def _on_download_success(self) -> None:
        self._reset_buttons()
        self.progress_bar.set(1.0)
        self.status_label.configure(text=f"Tamamlandı! Dosya '{self.download_dir}' klasörüne kaydedildi.")
        messagebox.showinfo(
            "İndirme Tamamlandı",
            f"Video başarıyla indirildi!\n\nKayıt Yeri:\n{self.download_dir}",
        )

    def _on_download_cancelled(self) -> None:
        self._reset_buttons()
        self.progress_bar.set(0)
        self.status_label.configure(text="İndirme iptal edildi.")

    def _on_download_error(self, err_msg: str) -> None:
        self._reset_buttons()
        self.progress_bar.set(0)
        self.status_label.configure(text="Hata oluştu.")
        messagebox.showerror(
            "İndirme Hatası",
            f"Video indirilirken bir hata oluştu:\n\n{err_msg}",
        )


if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.mainloop()
