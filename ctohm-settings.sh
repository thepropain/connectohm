#!/bin/bash

cfgfile="/etc/connectohm"
pidfile="/var/run/ctohm-mode.pid"

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

# Set tty params
stty -F $1 ${bitrate_vals[bitrate]} cs${databits_vals[databits]} $pparm $sbparm raw -echo

# Kill the previous program mode (if there is one and it is still running)
# NOTE: at least with pppd, it has been my experience that it dies when the tty it is on disappears
# NOTE 2: We could just "killall -9 {each mode program}" if gettings PIDs proves to be a problem
if [ -f $pidfile ]; then
    killpid=$(<$pidfile)
    kill -9 $killpid
    rm $pidfile
fi

# Run the new mode
case "$mode" in
    # PPP
    "0")
        # HERE WE GO, HOMIE!
        ;;
esac
