##### HOW TO INSTALL

First, let's get the hardware set up. For basic operation, you're going to need a Rasperry Pi 3 or 4. [NOTE: I do not know which, if any, other models will work. I don't see why they wouldn't, just make sure you change things if your GPIO pin layout differs from the Pi 3/4. I originally wanted to do this on a Zero W, but both of mine bit the dust, I can't find new ones in stock anywhere due to hoarders and scalpers, and my 3 just didn't have the horsepower I needed while developing, so I'm using a 4.] You will also need:

- An SSD1306 128x64 OLED display. (USD 6 for a 2pk on Amazon at time of writing). These typically comes with pins already soldered and DuPont female-to-female wires, but of course if yours doesn't, you'll need those as well.

- A momentary ON switch. A button, a toggle switch, whatever. Heck, if you wanna risk your Pi's life, I bet you could get away with a knife switch or bare wire ends if you can make and break the connection fast enough and tweak the debounce delay to count as a double-tap.

- If your device doesn't connect via USB already, you'll need a USB to serial adapter. Depending on your adapter, you may also need a serial cable.  (NOTE: this just for now. I'm going to design a multi-function serial connector that'll plug directly to Pi in the future.)

Of course you also need an appropriate beefy power supply. I also recommend a box/case to put all this in. (NOTE: the prototype is literally in a cardboard box that my vape came in, and I cut holes and covered stuff with electrical tape where appropriate.)

###### SSD1306 to Pi wiring:

- VCC to PIN 1 or 17 (3V3 power)

- GND to PIN 9, 16, 14, or 20 (ground)

- SDA to PIN 3 (GPIO 2)

- SCL to PIN 5 (GPIO 3)

**Button wiring:** PINS 37 (GPIO 26) and 39 (ground)

---

As for the software, I've still got to work on an installer and/or an SD card image. I've got everything set up to run as root. Start with a fresh install of Raspberry Pi OS (Bookworm, 32-bit). In your /root directory, clone ConnectOhm and OpenXiino. Make the symlinks listed in SYMLINKS.md. Try to run stuff, apt install whatever packages are needed.


