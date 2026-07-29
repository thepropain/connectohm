#!/bin/bash

# NOTE: Palm OS gives 2 nodes. I got a feeling that's going to cause problems. Doing what we can to avoid one now.
runfile="/var/run/ctohm-settings-running"
if [ -f $runfile ]; then
    echo "Already running, exiting..."
    exit 0
fi
touch $runfile

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

# Set tty params.
# NOTE: I misunderstood when this was to be done. We'll revisit this later, if not for HAYES mode, then for SHELL mode.
# stty -F $node ${bitrate_vals[bitrate]} cs${databits_vals[databits]} $pparm $sbparm raw -echo

# Kill the previous program modes
# NOTE: Since Palm OS gives 2 nodes and Linux likes to juggle their order, I gave up on PID tracking.
killall pppd

# If we don't have at least ctohm0 to work on, we better stop now
if [ ! -L /dev/ctohm0 ]; then
    rm $runfile
    exit 0
fi

# Run the new mode
case "$mode" in
    # PPP
    "0")
        # Again, Palm OS multi-node juggling. Just run pppd on ALL ctohm nodes
        for node in /dev/ctohm*
        do
            echo "Looping on ${node} with ${bitrate_vals[bitrate]} as `whoami`"
            pppd $node ${bitrate_vals[bitrate]} call ctohm-ppp &
        done
        ;;
esac

rm $runfile
