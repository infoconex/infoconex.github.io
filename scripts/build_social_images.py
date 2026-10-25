#!/usr/bin/env python3
"""Build 1200x630 social share PNG images for the homepage and projects."""
import json
import io
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "social"
OUT.mkdir(parents=True, exist_ok=True)
projects = json.loads((ROOT / "projects.json").read_text(encoding="utf-8"))
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
REGULAR = FONT_DIR / "DejaVuSans.ttf"
BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
assert REGULAR.exists() and BOLD.exists(), "DejaVu fonts required by share image generator"

def font(size, bold=False):
    return ImageFont.truetype(str(BOLD if bold else REGULAR), size)

def wrap(draw, text, f, width):
    lines = []
    for word in text.split():
        candidate = (lines[-1] + " " + word) if lines else word
        if lines and draw.textbbox((0, 0), candidate, font=f)[2] > width:
            lines.append(word)
        elif lines:
            lines[-1] = candidate
        else:
            lines.append(candidate)
    return lines

def make_image(title, category, subtitle, filename):
    image = Image.new("RGB", (1200, 630), "#252F3A")
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((62, 55, 1138, 575), radius=25, fill="#344151", outline="#4A5969", width=2)
    d.rounded_rectangle((106, 96, 160, 150), radius=12, fill="#91B5CC")
    d.text((120, 105), "i.", fill="#252F3A", font=font(27, True))
    d.text((182, 108), "infoconex", font=font(26, True), fill="#F1F5F9")
    d.text((108, 194), category.upper(), font=font(19, True), fill="#91B5CC")
    headline = font(54 if len(title) < 31 else 43, True)
    title_lines = wrap(d, title, headline, 970)[:3]
    y = 242
    for line in title_lines:
        d.text((106, y), line, font=headline, fill="#F1F5F9")
        y += (72 if len(title) < 31 else 61)
    subtitle_font = font(23)
    sub_y = max(y + 19, 398)
    for line in wrap(d, subtitle, subtitle_font, 975)[:3]:
        if sub_y > 519:
            break
        d.text((107, sub_y), line, font=subtitle_font, fill="#BECAD7")
        sub_y += 34
    image.save(OUT / filename, format="PNG", optimize=True)

def use_repo_banner(url, filename):
    """Use an explicit repo banner, with a generated card as a safe fallback."""
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "infoconex-social-image-builder"})
        with urllib.request.urlopen(request, timeout=12) as response:
            data = response.read(10 * 1024 * 1024 + 1)
        if len(data) > 10 * 1024 * 1024:
            raise ValueError("Image exceeds 10 MB")
        with Image.open(io.BytesIO(data)) as source:
            source.load()
            if source.width < 600 or source.height < 315:
                raise ValueError("Image resolution too small for a social preview")
            rgb = source.convert("RGB")
            background = Image.new("RGB", (1200, 630), "#252F3A")
            fitted = ImageOps.contain(rgb, (1200, 630), method=Image.Resampling.LANCZOS)
            background.paste(fitted, ((1200 - fitted.width) // 2, (630 - fitted.height) // 2))
            background.save(OUT / filename, format="PNG", optimize=True)
        print(f"Using repository banner: {filename}")
        return True
    except (OSError, ValueError, UnidentifiedImageError) as exc:
        print(f"Repository banner unavailable for {filename}; using generated fallback: {exc}")
        return False

make_image("AI, .NET & Developer Projects", "Open-source engineering", "Software projects, experiments, and technical writing.", "home.png")
for p in projects:
    slug = p["url"].rstrip("/").split("/")[-1]
    filename = slug + ".png"
    if not p.get("socialSource") or not use_repo_banner(p["socialSource"], filename):
        make_image(p["name"], p["category"], p["seoDescription"], filename)
print(f"Generated {len(projects) + 1} social share images.")
