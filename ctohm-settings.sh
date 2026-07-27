#!/bin/bash
# /usr/local/bin/ctohm-usb-attach.sh
TTY_DEV="/dev/$1"
# Read current mode from ConnectOhm state file (e.g. 
# /tmp/ctohm_mode)
CURRENT_MODE=$(cat /tmp/ctohm_mode 2>/dev/null || echo 
"HAYES") if [ "$CURRENT_MODE" = "PPP" ]; then
    # Grab current baud rate from state file or default to 
    # 115200
    BAUD=$(cat /tmp/ctohm_baud 2>/dev/null || echo 
    "115200")
    # Set framing parameters
    stty -F "$TTY_DEV" "$BAUD" cs8 -parenb -cstopb raw 
    -echo
    # Launch pppd attached to the newly created ttyUSB0
    /usr/sbin/pppd "$TTY_DEV" "$BAUD" 
    192.168.2.1:192.168.2.2 local ms-dns 1.1.1.1 noauth 
    passive persist &
fi
