import os
from io import BytesIO

import qrcode
from qrcode.constants import ERROR_CORRECT_H

from app.config import settings


def generate_qr(inventory_number: str) -> str:
    qr_url = f"{settings.BASE_URL}/scan/{inventory_number}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    os.makedirs(settings.QRCODE_DIR, exist_ok=True)
    filename = f"{inventory_number}.png"
    filepath = os.path.join(settings.QRCODE_DIR, filename)
    img.save(filepath)

    return filename


def get_qr_bytes(inventory_number: str) -> bytes:
    qr_url = f"{settings.BASE_URL}/scan/{inventory_number}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()
