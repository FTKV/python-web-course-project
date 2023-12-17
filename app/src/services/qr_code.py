"""
module to work with QR-code
"""

import qrcode


def generate_qr_code(image_url: str) -> None:
    """
    Generates a PNG image with a QR code from the url of the image:

    :param image_url: URL of the image
    :type image_url: str.
    :return BytesIO: File in image/png format with QR-code url.
    :rtype BytesIO:
    """
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5,
    )

    # Add URL to QR-code
    qr.add_data(image_url)
    qr.make(fit=True)

    # Make QR-code object
    qr_code = qr.make_image(fill_color="black", back_color="white")
    qr_code.save("static/qrcode.png")
