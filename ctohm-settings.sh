#!/bin/bash

# FOR TESTING PURPOSES. This should be deleted or commented out for proper operation
# exit 0

if [ -z "$1" ]; then
    echo "No node specified! Usage: ctohm-settings.sh ctohm0"
    exit 1
fi


node="/dev/$1"

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
# mode_vals=("PPP" "HAYES" "(C)SLIP" "SHELL" "NULL MODEM" "LOOPBACK")
# parity_vals=("NONE" "EVEN" "ODD")
# stopbits_vals=("1" "2")

# Translate parity to parameters for stty
case "$parity" in
    "0") # NONE
	    pparm="-parenb"
		;;
	"1") #EVEN
	    pparm="parenb -parodd"
		;;
	"2") # ODD
	    pparm="parenb parodd"
		;;
esac

# Translate stopbits to a parameter for stty
if [[ $stopbits == 0 ]]; then
    sbparm="-cstopb"
else
    sbparm="cstopb"
fi

# Set comm parameters
stty -F $node ${bitrate_vals[bitrate]} cs${databits_vals[databits]} $pparm $sbparm raw -echo

case "$mode" in
    "0") # PPP
        echo "Launching PPP mode on $node..."
        # 'exec' replaces this shell with pppd so pppd runs directly in the background
        exec pppd "$node" "${bitrate_vals[bitrate]}" call ctohm-ppp
        #cd /root/connectohm
        #touch /root/connectohm/ppp.log
        #export HOME=/root
        #ipaddress=`ip -4 addr show wlan0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'`
        #exec slirp "debug" "debugppp" "host addr ${ipaddress}" "tty ${node}" "baudrate ${bitrate_vals[bitrate]}" "ppp" "auth" "+pap" "debugppp" 2>> /root/connectohm/ppp.log
        ;;

    "1") # HAYES
        echo "Launching Hayes modem bridge on $node..."
        exec tcpser -s "${bitrate_vals[bitrate]}" -d "$node"
        ;;

    "2") # (C)SLIP
        echo "Launching SLIP daemon on $node..."
        export HOME=/root
        exec slirp "tty ${node}" "baudrate ${bitrate_vals[bitrate]}"
        ;;

    "3") # SHELL
        echo "Launching Serial Shell on $node..."
        exec agetty -a root -L "${bitrate_vals[bitrate]}" "${node#/dev/}" vt100
        ;;
esac
