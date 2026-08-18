#!/usr/bin/env python3
import os
import subprocess
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

FB_CACHE = "/tmp/ctohm-fb.bin"

def get_wifi_ssn():
    """
    Returns 'SSN: <SSID>' if connected to Wi-Fi, or 'SSN: not connected'.
    """
    ssid = None

    # 1. Try iwgetid (Standard Raspberry Pi OS / Debian)
    try:
        res = subprocess.run(["iwgetid", "-r"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0 and res.stdout.strip():
            ssid = res.stdout.strip()
    except Exception:
        pass

    # 2. Fallback for NetworkManager (nmcli)
    if not ssid:
        try:
            res = subprocess.run(
                ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
                capture_output=True, text=True, timeout=2
            )
            for line in res.stdout.splitlines():
                if line.startswith("yes:"):
                    ssid = line.split(":", 1)[1].strip()
                    break
        except Exception:
            pass

    if ssid:
        # Max displayable chars across 128px is ~18 chars with font spacing
        # "SSN: " is 5 chars, so clamp SSID to 13 chars
        max_ssid_len = 13
        truncated_ssid = ssid[:max_ssid_len]
        return f"SSN: {truncated_ssid}"
    else:
        return "SSN: not connected"

def load_framebuffer():
    """
    Reconstructs the 128x64 image from the cache file, or creates a clean blank slate.
    """
    if os.path.exists(FB_CACHE):
        try:
            with open(FB_CACHE, "rb") as f:
                data = f.read()
                if len(data) == 1024:
                    return Image.frombytes("1", (128, 64), data)
        except Exception:
            pass
    return Image.new("1", (128, 64), 0)

def main():
    # 1. Initialize display hardware
    try:
        serial = i2c(port=1, address=0x3c)
        device = ssd1306(serial)
        device.cleanup = lambda: None
    except Exception as e:
        print(f"Hardware init failed: {e}")
        exit(1)

    # 2. Load font
    try:
        oledfont = ImageFont.load("oledfont.pil")
    except Exception:
        oledfont = ImageFont.load_default()

    # 3. Load pre-existing framebuffer and prepare drawing context
    img = load_framebuffer()
    draw = ImageDraw.Draw(img)

    # 4. Clear/blank lines 52 to 63
    draw.rectangle((0, 52, 127, 63), fill="black")

    # 5. Draw divider line and updated SSN string
    status_str = get_wifi_ssn()
    draw.line((0, 52, 127, 52), fill="white")
    draw.text((1, 52), status_str, font=oledfont, fill="white")

    # 6. Push to physical screen
    device.display(img)

    # 7. Write back updated composite buffer to cache
    try:
        with open(FB_CACHE, "wb") as f:
            f.write(img.tobytes())
    except Exception as e:
        print(f"Failed to cache framebuffer: {e}")

if __name__ == "__main__":
    main()