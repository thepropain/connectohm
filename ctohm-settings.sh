#!/bin/bash

node="/dev/ctohm0"

cfgfile="/etc/connectohm.conf"

# load config values, is formatted so we can just include it directly
if [ -f $cfgfile ]; then
    source $cfgfile
else
        mode=1
	bitrate=8
	databits=3
	parity=0
	stopbits=0
fi


bitrate_vals=("300" "1200" "2400" "4800" "9600" "19200" "38400" "57600" "115200" "230400")
databits_vals=("5" "6" "7" "8")
# We're not using these arrays, leaving them here for reference
# mode_vals=("PPP" "HAYES" "SLIP" "CSLIP" "SHELL" "NULL MODEM" "LOOPBACK")
# parity_vals=("NONE" "EVEN" "ODD")
# stopbits_vals=("1" "2")

# Translate parity to parameters for stty
case "$parity" in
    "0")
	    pparm="-parenb"
		;;
	"1")
	    pparm="parenb -parodd"
		;;
	"2")
	    pparm="parenb parodd"
		;;
esac

# Translate stopbits to a parameter for stty
if [[ $stopbits == 0 ]]; then
    sbparm="-cstopb"
else
    sbparm="cstopb"
fi

# Trap SIGTERM/SIGINT so when systemd stops the service, the script exits cleanly
trap "exit 0" SIGTERM SIGINT

case "$mode" in
    "0") # PPP
        echo "Launching PPP mode..."
        pppd "$node" "${bitrate_vals[bitrate]}" call ctohm-ppp &
        ;;

    "1") # HAYES
        echo "Launching Hayes modem bridge..."
        # e.g., tcpser or socat bridge background job
        tcpser -s "${bitrate_vals[bitrate]}" -d "$node" &
        ;;

    "2") # SLIP
        echo "Launching SLIP daemon..."
        slattach -p slip -s "${bitrate_vals[bitrate]}" "$node" &
        ;;

    "3") # SHELL
        echo "Launching Serial Shell..."
        agetty -L "${bitrate_vals[bitrate]}" ctohm0 vt100 &
        ;;
esac

# -------------------------------------------------------------
# UNIVERSAL BLOCK: Wait for ANY background process spawned above
# -------------------------------------------------------------
wait