# ConnectOhm

---

## Turn a Raspberry Pi into a Swiss army knife for retrotech <-> WiFi/Internet connectivity

If it's got a serial port, then it's got Wifi. Easy peasy!

---

###### UP FRONT WARNINGS

- While I CAN code from scratch, I'm old and lazy, and have been relying heavily on Google Gemini for a lot of the scut work and most of the "I don't feel like writing data pipes and twiddles and regular expressions" parts. Additionally, until the first release, expect that there are untested/broken/insecure things.

- This project is currently NOT in a "clone and go" state. Ideally, I'll have both an installable package and a preinstalled SD card image available.

---

###### Current features

- Provides SLIP, CSLIP, PPP, Hayes-compatible modem emulation, and direct shell access via USB-> serial

- Serial parameters and connection mode selectable via a single button and external display

- WiFi configurable via HTTP, telnet, or shell command line.

###### Planned Features (in no particular order)

- Tiny software footprint.

- An adjustable voltage/logic invertable DB-9 on the Pi's pins, with the idea being "bodge/splice together a DB-9 and whatever weird connector you need, and ConnectOhm can handle the conversion" (Looking at you, pre-Perifractic Commodore; though there's plenty of others)

- PLIP via external MCU, assuming I can get the nybbles/bytes

- SSH connections from Hayes mode

- Bi-directional charset translations for SHELL mode and Hayes connections.

###### Possible future inclusions

Assuming I can find and afford the relevant hardware, or at least get access to it.

- Multi-Link PPP (MLPPP - RFC 1990)

- X.25 / LAPB (RFC 1356)

- AppleTalk / LocalTalk (IP over DDP / MacIP)

- DDCMP (Digital Data Communications Message Protocol)

- AX.25 (Packet Radio / KISS TNC IP)

###### Current Project Status

**08 Aug 2026: core functionality achieved!** Feels like a milestone to me. I've got some meatspace issues coming up soon that may slow/stall development.

###### The TO DO List

- Documentation: parts needed, assembly, usage, installation (that last may be a while...)
- Firewall the WiFi configurators and any other servers ConnectOhm ends up with.
- Give everything a good shakedown.
- Maybe move away from Python in favor of C
- Reduce software footprint
- Need to scrounge up some dinero for some parts. (I will happily accept donations of required parts, money, and retrotech to test!)
