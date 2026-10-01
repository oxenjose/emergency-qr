from flask import Blueprint, request, send_file
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

qr_bp = Blueprint('qr', __name__)


# ------------------------------------------------------------------
# Font helper
# ------------------------------------------------------------------

def _load_font(size):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


# ------------------------------------------------------------------
# Icon drawing helpers
# ------------------------------------------------------------------

def draw_phone_icon(draw, x, y, size):
    color = "#0d3b32"
    body_left = x + size // 5
    body_right = x + size - size // 5
    radius = size // 6
    draw.rounded_rectangle(
        [body_left, y, body_right, y + size],
        radius=radius, fill=color
    )
    pad = size // 8
    draw.rounded_rectangle(
        [body_left + pad, y + pad,
         body_right - pad, y + size - pad * 3],
        radius=radius // 2, fill="white"
    )
    r = max(2, size // 22)
    cx = x + size // 2
    cy = y + size - size // 7
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="white")


def draw_cross_icon(draw, x, y, size):
    red = "#e63946"
    thickness = int(size * 0.35)
    offset = (size - thickness) // 2
    draw.rectangle(
        [x + offset, y, x + offset + thickness, y + size], fill=red
    )
    draw.rectangle(
        [x, y + offset, x + size, y + offset + thickness], fill=red
    )


def draw_contacts_icon(draw, x, y, size):
    color = "#0d3b32"
    head_r = size // 4
    head_cx = x + size // 2
    head_cy = y + size // 4
    draw.ellipse(
        [head_cx - head_r, head_cy - head_r,
         head_cx + head_r, head_cy + head_r], fill=color
    )
    body_left = x + size // 6
    body_right = x + size - size // 6
    body_top = y + size // 2 + size // 10
    body_bottom = y + size
    draw.rounded_rectangle(
        [body_left, body_top, body_right, body_bottom],
        radius=size // 6, fill=color
    )


# ------------------------------------------------------------------
# Image builder (label + QR + icons)
# ------------------------------------------------------------------

def build_qr_image(contact_id, label=None):
    """Return a PIL Image with optional label at the top, QR in the middle,
    and the three icons at the bottom."""
    base_url = os.environ.get('BASE_URL') or request.url_root.rstrip('/')
    view_url = f'{base_url}/view/{contact_id}'

    qr = qrcode.QRCode(version=1, box_size=10, border=3)
    qr.add_data(view_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    qr_w, qr_h = qr_img.size

    icon_size = 60
    icon_gap = 28
    padding_top = 24
    padding_bottom = 24
    side_padding = 20

    label_font_size = 34
    label_padding_top = 28
    label_padding_bottom = 18

    total_icons_w = icon_size * 3 + icon_gap * 2

    # Measure label if present
    label_font = _load_font(label_font_size)
    label_w = 0
    label_h = 0
    if label:
        temp = Image.new("RGB", (10, 10), "white")
        bbox = ImageDraw.Draw(temp).textbbox((0, 0), label, font=label_font)
        label_w = bbox[2] - bbox[0]
        label_h = bbox[3] - bbox[1]

    label_block_h = (label_padding_top + label_h + label_padding_bottom) if label else 0

    final_w = max(qr_w, total_icons_w + side_padding * 2)
    if label:
        final_w = max(final_w, label_w + side_padding * 4)

    final_h = label_block_h + padding_top + qr_h + padding_top + icon_size + padding_bottom

    final_img = Image.new("RGB", (final_w, final_h), "white")
    draw = ImageDraw.Draw(final_img)

    # Draw label centered at the top
    if label:
        text_x = (final_w - label_w) // 2
        draw.text((text_x, label_padding_top), label, font=label_font, fill="#0d3b32")

    # QR
    qr_x = (final_w - qr_w) // 2
    qr_y = label_block_h + padding_top
    final_img.paste(qr_img, (qr_x, qr_y))

    # Icons below the QR
    icons_start_x = (final_w - total_icons_w) // 2
    icons_y = qr_y + qr_h + padding_top

    draw_phone_icon(draw, icons_start_x, icons_y, icon_size)
    draw_cross_icon(draw, icons_start_x + icon_size + icon_gap, icons_y, icon_size)
    draw_contacts_icon(draw, icons_start_x + (icon_size + icon_gap) * 2, icons_y, icon_size)

    return final_img


@qr_bp.route('/qr/<contact_id>.png')
def generate_qr(contact_id):
    from database.models import get_contact
    contact = get_contact(contact_id)
    label = contact['label'] if contact and contact['label'] else None

    img = build_qr_image(contact_id, label=label)
    buf = BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


# ------------------------------------------------------------------
# QR decoding (image or PDF)
# ------------------------------------------------------------------

def decode_qr_from_image(image_bytes, filename=''):
    """Decode a QR code from PNG/JPG/PDF bytes. Returns the decoded string or None."""
    import cv2
    import numpy as np

    is_pdf = filename.lower().endswith('.pdf') or image_bytes[:4] == b'%PDF'

    if is_pdf:
        try:
            import fitz  # PyMuPDF
        except ImportError:
            return None
        try:
            doc = fitz.open(stream=image_bytes, filetype="pdf")
        except Exception:
            return None
        if doc.page_count == 0:
            return None
        page = doc.load_page(0)
        mat = fitz.Matrix(2, 2)  # 2x zoom for better detection
        pix = page.get_pixmap(matrix=mat)
        png_bytes = pix.tobytes("png")
        arr = np.frombuffer(png_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    else:
        arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if img is None:
        return None

    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img)
    return data if data else None