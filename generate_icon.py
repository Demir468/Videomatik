"""Videomatik uygulama ikonunu (assets/icon.ico ve assets/icon.png) oluşturur."""

from pathlib import Path
from PIL import Image, ImageDraw


def generate_icon() -> Path:
    base_dir = Path(__file__).resolve().parent
    assets_dir = base_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Yuvarlatılmış koyu mavi arka plan
    draw.rounded_rectangle(
        [12, 12, size - 12, size - 12],
        radius=56,
        fill=(20, 72, 112, 255),
        outline=(56, 189, 248, 255),
        width=8,
    )

    # İç daire
    draw.ellipse([48, 48, size - 48, size - 48], fill=(31, 106, 165, 255))

    # İndirme oku (beyaz)
    draw.rectangle([112, 68, 144, 134], fill=(255, 255, 255, 255))
    draw.polygon([(80, 126), (176, 126), (128, 178)], fill=(255, 255, 255, 255))

    # Alt tepsi çizgisi (açık mavi)
    draw.rounded_rectangle([76, 188, 180, 204], radius=6, fill=(56, 189, 248, 255))

    png_path = assets_dir / "icon.png"
    ico_path = assets_dir / "icon.ico"

    img.save(png_path)
    img.save(
        ico_path,
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
    )
    print(f"Icon created: {ico_path}")
    return ico_path


if __name__ == "__main__":
    generate_icon()
