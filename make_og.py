"""Generate og-cover.png (1200x630) for Facebook/OG link preview."""
from PIL import Image, ImageDraw, ImageFont
import textwrap, os

W, H = 1200, 630
DARK = (15, 39, 68)      # --primary-dark #0f2744
BLUE = (27, 58, 107)     # --primary #1b3a6b
GOLD = (201, 162, 39)    # --gold #c9a227

img = Image.new("RGB", (W, H), DARK)
draw = ImageDraw.Draw(img)

# Gradient-ish background bands
for y in range(H):
    t = y / H
    r = int(DARK[0] + (BLUE[0] - DARK[0]) * t)
    g = int(DARK[1] + (BLUE[1] - DARK[1]) * t)
    b = int(DARK[2] + (BLUE[2] - DARK[2]) * t)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# Gold accent bar at bottom
draw.rectangle([(0, H - 8), (W, H)], fill=GOLD)

# Gold horizontal rule
draw.rectangle([(60, 260), (W - 60, 264)], fill=GOLD)

# Try to load logo
logo_path = os.path.join(os.path.dirname(__file__),
                         "lms", "static", "lms", "logo.png")
if os.path.exists(logo_path):
    logo = Image.open(logo_path).convert("RGBA")
    logo.thumbnail((130, 130))
    lx = (W - logo.width) // 2
    ly = 60
    img.paste(logo, (lx, ly), logo)
    text_y = ly + logo.height + 24
else:
    text_y = 80

# Load fonts — fall back to default if not found
def load_font(size, bold=False):
    for name in (["arialbd.ttf", "Arial_Bold.ttf"] if bold else ["arial.ttf", "Arial.ttf"]):
        for root in [r"C:\Windows\Fonts", "/usr/share/fonts/truetype/msttcorefonts"]:
            p = os.path.join(root, name)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()

font_title = load_font(36, bold=True)
font_sub   = load_font(22)
font_url   = load_font(18)

title = "ТӨРИЙН ТУСГАЙ ХАМГААЛАЛТЫН АЛБА ХААГЧИЙН\nАНГЛИ ХЭЛНИЙ ЦАХИМ СУРГАЛТЫН СИСТЕМ"
sub   = "ТТХГ — Онлайн сургалтын платформ"
url   = "sspa400v3.onrender.com"

def centered_text(text, y, font, color=(255, 255, 255), spacing=8):
    lines = text.split("\n")
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, y), line, font=font, fill=color)
        y += bbox[3] - bbox[1] + spacing
    return y

y = text_y
y = centered_text(title, y, font_title, spacing=10)
y += 20
y = centered_text(sub, y, font_sub, color=(200, 210, 230))
y += 16
centered_text(url, y, font_url, color=GOLD)

out = os.path.join(os.path.dirname(__file__),
                   "lms", "static", "lms", "og-cover.png")
img.save(out, "PNG")
print(f"Saved: {out}")
