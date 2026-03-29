"""
Minimal working example for Brother QL-810W label printer.

Prints a simple test label using the brother_ql library.
"""

import os

from brother_ql import BrotherQLRaster
from brother_ql.backends.helpers import send
from brother_ql.conversion import convert
from PIL import Image, ImageDraw, ImageFont

PRINTER_MODEL = os.environ.get("BROTHER_QL_MODEL", "QL-810W")
LABEL_TYPE = os.environ.get("BROTHER_QL_LABEL", "62")  # 62mm endless tape
PRINTER_IDENTIFIER = os.environ.get("BROTHER_QL_PRINTER", "tcp://192.168.1.167:9100")

img = Image.new("RGB", (696, 300), color="white")
draw = ImageDraw.Draw(img)

try:
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48
    )
except OSError:
    font = ImageFont.load_default()

draw.text((50, 50), "Hello from", fill="black", font=font)
draw.text((50, 150), "Brother QL-810W!", fill="black", font=font)

qlr = BrotherQLRaster(PRINTER_MODEL)
instructions = convert(qlr=qlr, images=[img], label=LABEL_TYPE)

send(instructions=instructions, printer_identifier=PRINTER_IDENTIFIER)
print("Print job sent successfully")
