"""
One-time script: generates the Open Graph social preview image.
Run once with: python generate_og_image.py
Output: static/images/og-image.png  (1200 x 630)
"""

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1200
HEIGHT = 630
BG_COLOR = "#0d3b32"     # dark green (brand)
MINT = "#c8f7dc"          # mint accent
WHITE = "#ffffff"


def load_font(size, bold=True):
    """Try common system font paths. Falls back to default."""
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def centered_text(draw, text, font, y, fill):
    """Draw text horizontally centered at the given y position."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    x = (WIDTH - text_w) // 2
    draw.text((x, y), text, font=font, fill=fill)


# --- Canvas ---
img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
draw = ImageDraw.Draw(img)

# --- Title "Emergency QR" (big, mint) ---
font_title = load_font(130, bold=True)
centered_text(draw, "Emergency QR", font_title, 120, MINT)

# --- Tagline (medium, white) ---
font_tagline = load_font(44, bold=False)
centered_text(draw, "Never forget an important number again", font_tagline, 300, WHITE)

# --- Divider line ---
line_y = 400
draw.line([(WIDTH // 2 - 200, line_y), (WIDTH // 2 + 200, line_y)], fill=MINT, width=2)

# --- Bottom caption (small, mint) ---
font_caption = load_font(30, bold=False)
centered_text(draw, "Free  ·  No app  ·  No account", font_caption, 450, MINT)

# --- Save ---
img.save("static/images/og-image.png", "PNG", optimize=True)
print("✓ og-image.png saved to static/images/")