from flask import Blueprint, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from io import BytesIO

from routes.qr import build_qr_image
from database.models import get_contact

print_bp = Blueprint('print', __name__)


# Card sizes in millimeters: (width, height)
CARD_SIZES = {
    'phone':    {'w': 55, 'h': 65, 'label': 'Back of phone (5.5 × 6.5 cm)'},
    'keychain': {'w': 38, 'h': 48, 'label': 'Keychain (3.8 × 4.8 cm)'},
}


@print_bp.route('/print/<contact_id>.pdf')
def print_pdf(contact_id):
    contact = get_contact(contact_id)
    if not contact:
        return "Contact not found", 404

    size_key = request.args.get('size', 'phone')
    if size_key not in CARD_SIZES:
        size_key = 'phone'

    try:
        copies = int(request.args.get('copies', 1))
    except ValueError:
        copies = 1
    copies = max(1, min(copies, 100))

    card_w = CARD_SIZES[size_key]['w'] * mm
    card_h = CARD_SIZES[size_key]['h'] * mm

    # A4 page with 10 mm margins
    page_w, page_h = A4
    margin = 10 * mm
    usable_w = page_w - margin * 2
    usable_h = page_h - margin * 2

    cols = int(usable_w // card_w)
    rows = int(usable_h // card_h)
    if cols < 1 or rows < 1:
        return "Card too big for A4 page", 400

    # Build QR image once (with label if present) and wrap it for reportlab
    label = contact['label'] if contact['label'] else None
    qr_pil = build_qr_image(contact_id, label=label)
    qr_reader = ImageReader(qr_pil)

    # Start PDF
    pdf_buf = BytesIO()
    c = canvas.Canvas(pdf_buf, pagesize=A4)

    placed = 0
    while placed < copies:
        for row in range(rows):
            for col in range(cols):
                if placed >= copies:
                    break

                x = margin + col * card_w
                y = page_h - margin - (row + 1) * card_h

                # Cut lines (very light gray)
                c.setStrokeColorRGB(0.82, 0.82, 0.82)
                c.setLineWidth(0.3)
                c.rect(x, y, card_w, card_h, stroke=1, fill=0)

                # QR image centered inside the card with 3mm padding
                padding = 3 * mm
                img_w = card_w - padding * 2
                img_h = card_h - padding * 2

                c.drawImage(
                    qr_reader,
                    x + padding, y + padding,
                    width=img_w, height=img_h,
                    preserveAspectRatio=True,
                    anchor='c',
                    mask='auto'
                )
                placed += 1

            if placed >= copies:
                break

        if placed < copies:
            c.showPage()

    c.save()
    pdf_buf.seek(0)

    return send_file(
        pdf_buf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'emergency_qr_{size_key}.pdf'
    )