###### Software Flow

Menu saves settings

Do we have /dev/ctohm*? If so, trigger udev.

-----

Udev triggers

create /dev/ctohm*, run ctohm-settings.sh

-----

ctohm-settings is called

kill any old modes running

set tty rate, databits, parity, stopbits

run current mode and any appropriate wifi config server backend



MeatSpace flow

set params and mode

make connections (plug in usb, start connection from Palm OS, etc.)

if not already connected, connect to wifi using web (gopher?, wais? others?), Hayes-like commands, shell script, not needed for null modem or loop

OFF TO THE RACES!

break connections (wifi should remain connected)

wash, rinse, repeat