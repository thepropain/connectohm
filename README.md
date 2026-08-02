![connectohm logo.png](misc/connectohm%20logo.png)

# ConnectOhm

A Swiss army knife for retrotech Internet connectivity. I'm an old programmer who's been out of the loop and out of practice for 20+ years, so I'm leaning on AI for a lot of this project. Inspect ALL OF THIS CODE before you use it.

This is NOT ready for primetime yet.

###### List of features to be added down the line

- adjustable voltage/polarity DB-9 on the Pi's pins

- PLIP via external MCU

- Raw multicast hub, for as many adapters as you like (for example, I've got a 5 port USB-to-serial box). Dunno what use that might be, but it does feel like it's just barely within scope.

- Maaaaybe a chat room kinda thing? That feels a little silly, tho. I mean, if we're going to have a shell mode, just log in and use IRC or whatever.

- I was originally going to use tcpser for Hayes mode, but I think I want to use ZiModem instead. For now, I've got an ESP32 board that I'm going to wire in, but I want to port ZiModem and add/remove some stuff.

###### What I'm working on now

- Revamping Hayes mode to use ZiModem instead of tcpser.
