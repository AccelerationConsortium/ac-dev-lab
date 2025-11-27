"""
Minimal working example for Brother QL-810W label printer.

Prints a simple test label using the brother_ql library.
"""

from io import BytesIO

from brother_ql import BrotherQLRaster
from brother_ql.backends.helpers import send
from brother_ql.conversion import convert
from PIL import Image, ImageDraw, ImageFont

PRINTER_MODEL = "QL-810W"
LABEL_TYPE = "62"  # 62mm endless tape
PRINTER_IDENTIFIER = "tcp://192.168.1.100:9100"  # Replace with your printer's IP

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

buffer = BytesIO()
for instruction in instructions:
    buffer.write(instruction)

send(instructions=buffer.getvalue(), printer_identifier=PRINTER_IDENTIFIER)
print("Print job sent successfully")
