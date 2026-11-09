"""Videomatik Web & Mobil Sunucusu (yt-dlp + Yerleşik HTTP Sunucusu).

Hem GitHub Pages ön yüzünü (docs/index.html) sunar hem de /api/analyze ve /api/download
uç noktalarıyla 1000+ siteden mobil ve masaüstü tarayıcıya doğrudan MP4/MP3 indirme sağlar.
"""

from __future__ import annotations

import json
import mimetypes
import os
import shutil
import socket
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, urlparse

import yt_dlp

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def get_ffmpeg_path() -> str | None:
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    if imageio_ffmpeg is not None:
        try:
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            return None
    return None


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
    try:
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}/"
    except Exception:
        pass
    return url


def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


class VideomatikWebHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Access-Control-Allow-Private-Network")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path
        query = parse_qs(parsed.query)

        if route == "/api/health":
            self._send_json(200, {"status": "ok", "engine": "yt-dlp"})
            return

        if route == "/api/analyze":
            url = (query.get("url") or [""])[0].strip()
            if not url:
                self._send_json(400, {"detail": "URL parametresi eksik."})
                return
            self._handle_analyze(url)
            return

        if route == "/api/download":
            url = (query.get("url") or [""])[0].strip()
            fmt = (query.get("format") or ["mp4"])[0].strip().lower()
            quality = (query.get("quality") or ["1080"])[0].strip().lower()
            if not url:
                self._send_json(400, {"detail": "URL parametresi eksik."})
                return
            self._handle_download(url, fmt, quality)
            return

        # Statik dosyaları (docs/) sun
        rel_path = "index.html" if route in ("/", "") else route.lstrip("/")
        file_path = (DOCS_DIR / rel_path).resolve()
        if not str(file_path).startswith(str(DOCS_DIR.resolve())) or not file_path.is_file():
            self._send_json(404, {"detail": "Dosya bulunamadı."})
            return

        mime_type, _ = mimetypes.guess_type(str(file_path))
        data = file_path.read_bytes()
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", mime_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _build_common_opts(self, url: str) -> dict[str, Any]:
        is_youtube = any(d in url.lower() for d in ("youtube.com", "youtu.be"))
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "retries": 5,
            "js_runtimes": {"node": {}, "deno": {}},
        }
        cookie_file = BASE_DIR / "cookies.txt"
        if cookie_file.is_file():
            opts["cookiefile"] = str(cookie_file)
        if not is_youtube:
            opts["http_headers"] = {
                "User-Agent": DEFAULT_USER_AGENT,
                "Referer": extract_origin_referer(url),
            }
        return opts

    def _handle_analyze(self, url: str) -> None:
        opts = self._build_common_opts(url)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            self._send_json(
                200,
                {
                    "title": info.get("title") or "Video",
                    "uploader": info.get("uploader") or info.get("webpage_url_domain") or "Web",
                    "duration_str": format_duration(info.get("duration")),
                    "thumbnail": info.get("thumbnail"),
                },
            )
        except Exception as exc:
            self._send_json(400, {"detail": str(exc)})

    def _handle_download(self, url: str, fmt: str, quality: str) -> None:
        tmp_dir = Path(tempfile.mkdtemp(prefix="videomatik_"))
        try:
            ffmpeg_path = get_ffmpeg_path()
            opts = self._build_common_opts(url)
            opts["outtmpl"] = str(tmp_dir / "%(title).120B.%(ext)s")
            if ffmpeg_path:
                opts["ffmpeg_location"] = ffmpeg_path

            if fmt == "mp3":
                opts["format"] = "bestaudio/best"
                if ffmpeg_path:
                    opts["postprocessors"] = [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ]
            else:
                if quality.isdigit():
                    h = int(quality)
                    if ffmpeg_path:
                        opts["format"] = (
                            f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/"
                            f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
                        )
                        opts["merge_output_format"] = "mp4"
                    else:
                        opts["format"] = f"best[height<={h}][ext=mp4]/best[height<={h}]/best"
                else:
                    if ffmpeg_path:
                        opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
                        opts["merge_output_format"] = "mp4"
                    else:
                        opts["format"] = "best[ext=mp4]/best"

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

            files = list(tmp_dir.iterdir())
            if not files:
                self._send_json(500, {"detail": "İndirilen dosya oluşturulamadı."})
                return

            target_file = files[0]
            file_size = target_file.stat().st_size
            safe_name = quote(target_file.name)
            mime_type, _ = mimetypes.guess_type(str(target_file))

            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", mime_type or "application/octet-stream")
            self.send_header("Content-Length", str(file_size))
            self.send_header(
                "Content-Disposition",
                f"attachment; filename*=UTF-8''{safe_name}",
            )
            self.end_headers()

            with target_file.open("rb") as f:
                shutil.copyfileobj(f, self.wfile)
        except Exception as exc:
            self._send_json(400, {"detail": str(exc)})
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


def run_server() -> None:
    port = int(os.environ.get("PORT", "8000"))
    local_ip = get_local_ip()
    server = ThreadingHTTPServer(("0.0.0.0", port), VideomatikWebHandler)
    print("=" * 60)
    print("  Videomatik Web & Mobil Sunucusu Aktif!")
    print(f"  Bilgisayardan giris : http://localhost:{port}")
    print(f"  Telefondan (Wi-Fi)  : http://{local_ip}:{port}")
    print("=" * 60)
    server.serve_forever()


if __name__ == "__main__":
    run_server()
