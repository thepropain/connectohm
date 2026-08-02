#!/usr/bin/env python3
import sys
from PIL import Image

if len(sys.argv) < 2:
    print("Usage: bmp2c.py input.bmp")
    sys.exit(1)

# Open image and force 1-bit monochrome (128x64)
img = Image.open(sys.argv[1]).convert('1')
if img.size != (128, 64):
    img = img.resize((128, 64))

# Convert pixels to SSD1306 Page-based byte array
buffer = bytearray(1024)

for page in range(8):
    for col in range(128):
        byte_val = 0
        for bit in range(8):
            y = page * 8 + bit
            pixel = img.getpixel((col, y))
            # White pixel (255 or 1) sets the bit to 1
            if pixel:
                byte_val |= (1 << bit)
        buffer[page * 128 + col] = byte_val

# Output as C array
array_name = "boot_splash_data"
print(f"static const unsigned char {array_name}[1024] = {{")
for i, b in enumerate(buffer):
    if i % 16 == 0:
        print("    ", end="")
    print(f"0x{b:02X}, ", end="")
    if (i + 1) % 16 == 0:
        print()
print("};")
