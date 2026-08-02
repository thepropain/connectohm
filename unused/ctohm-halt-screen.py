#!/usr/bin/env python3
import sys
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont

try:
    # Initialize I2C and SSD1306
    serial = i2c(port=1, address=0x3c)
    device = ssd1306(serial)
    
    # CRITICAL: Prevent luma from clearing the display when Python exits!
    device.cleanup = lambda: None

    oledfont = ImageFont.load("/usr/local/lib/connectohm/oledfont.pil")

    with canvas(device) as draw:
        draw.rectangle((0, 0, 127, 16), fill="white")
        draw.text((1, 2), "Connect\u00a9 Halt", font=oledfont, fill="black")
        draw.text((1, 24), "SYSTEM HALTED", font=oledfont, fill="white")
        draw.text((1, 38), "Safe to unplug now", font=oledfont, fill="white")

except Exception as e:
    print(f"Failed to draw halt screen: {e}")