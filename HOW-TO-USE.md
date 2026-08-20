#### So how do I use this thing now that I've got it running?

###### Make sure your device is plugged into the Pi.

For example, the two devices I have available to work with at the moment are an MS-DOS machine with a serial port and Palm OS device. For the DOS machine, I run a serial cable from it to a USB-to-serial adapter, and plug the USB end of the latter into the Pi. For the Palm OS device, I can just plug the cradle's USB into the Pi directly.

Once systemd sees the USB tty device(s), it sets the comm parameters the display shows and runs the select mode on that device.

###### So how do I change modes and parameters?

Let's get familiar with the display so we know what we're looking at.

![](Z:\connectohm\docimg\main.gif)

On the top row, we see: current mode, bitrate, data bits, parity, and stop bits.

The three lines in the middle are menu options. The caret at the left shows us what row we're on. To the right of the menu options, triangles will show us if there's more of the menu above or below the 3 options we can see. A single press of the button will move to the next option, and a double press will select it. When you select an option in the submenus, the changes will be immedately applied and you'll be returned to the main menu.

The bottom row shows what WiFi you're connected to, if any.

###### How do I change what WiFi I'm connected to?

You to this from you retro device. There's a few ways. I tried to cover as many connection-case bases as I could.

If you have access to a web browser, you can go to http://192.168.2.1 and use the web configurator.

If you have access to a telnet client, you can telnet to 192.168.2.1 on port 2323.

If you're on a serial terminal, you can go into HAYES mode and ATDT192.168.2.1:2323; or you can go into SHELL mode and run ctohm-wifi.sh; or if you need/prefer, from HAYES modem you can ATDT192.168.2.1:23 (or skip the :23) to get to a shell and run ctohm-wifi.sh from there. Whatever method you use, once you finish with that method, the system should connect automatically (assuming everything was entered correctly and there's no problems) and update the display.

###### So what's this OpenXiino thing you haven't mentioned yet?

On Palm OS, there's a browser called Xiino. It uses (well, usED; the developer took it down) a proprietary proxy-thingy to dumb down images and stuff for Palm OS. OpenXiino is a reverse engineered reimplementation of that proxy-thingy. In Xiino, dig around in the settings and set your data server to 192.168.2.1:4040.

###### Ok, so how do I get my retro device to use this connection?

Right now, all I can say is that it depends on your device. If/when I ever get to a 1st release, I'll start a series of articles of how to do so for each and every method for each and every device I can think of.

What I can do is give you examples of what I've been doing to test/play with the project, though they may be less than helpful if you're not already an old retrotech nerd. On my DOS machine, I've been using a PPP packet driver; haven't tested SLIP/CSLIP, but I was using SLiRP over a modem connection back in the day, and we're using SLiRP here, so I can't imagine it not working. I have also tested SHELL and HAYES mode with Qmodem Pro, and I expect I won't have problmens when I get around to playing with Windows 3x at some point. On my Palm device, I've tested PPP and SLIP/CSLIP and they work just fine.


