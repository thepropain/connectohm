#!/usr/bin/env python3
import sys
import os
from PIL import Image

DEFAULT_FB_FILE = "/tmp/ctohm-fb.bin"
DEFAULT_OUT_FILE = "screen_dump.txt"

def fb_to_ascii(fb_path=DEFAULT_FB_FILE, out_path=DEFAULT_OUT_FILE):
    if not os.path.exists(fb_path):
        print(f"Error: Framebuffer file '{fb_path}' not found.")
        sys.exit(1)

    with open(fb_path, "rb") as f:
        data = f.read()

    if len(data) != 1024:
        print(f"Warning: Expected 1024 bytes, got {len(data)} bytes.")

    # Reconstruct the 128x64 1-bit image from raw bytes
    img = Image.frombytes("1", (128, 64), data)
    pixels = img.load()

    lines = []
    for y in range(64):
        row_chars = []
        for x in range(128):
            # 1-bit mode: 0 is black/off, 255 (or 1) is white/on
            row_chars.append('.' if pixels[x, y] else ' ')
        lines.append("".join(row_chars))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Successfully converted {fb_path} -> {out_path} (64 lines x 128 chars)")

if __name__ == "__main__":
    # Allows passing custom file paths: python3 fb2txt.py [input_bin] [output_txt]
    fb_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FB_FILE
    out_file = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_FILE

    fb_to_ascii(fb_file, out_file)