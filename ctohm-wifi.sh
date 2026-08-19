#!/bin/sh

# Ensure safe path
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Clear terminal screen (using classic ASCII form-feed + VT100 clear fallback)
printf "\033[2J\033[H\014" 2>/dev/null || clear 2>/dev/null

echo "=================================================="
echo "          ConnectOhm Wi-Fi Configurator           "
echo "=================================================="
echo ""
echo "Scanning for wireless networks, please wait..."
echo ""

# Temporary file to store the scanned SSIDs
SCAN_TMP="/tmp/ctohm_scan_$$.tmp"
trap 'rm -f "$SCAN_TMP"' EXIT INT TERM

# Perform Wi-Fi scan and populate indexed list
# Output format: Index: SSID [Security] Stars (Label)
index=1
# Perform fast wireless scan via iwlist and parse with awk
iwlist wlan0 scan 2>/dev/null | awk '
  /Cell [0-9]+/ {
    if (ssid != "") {
      # Default to Open if no encryption was flagged
      if (sec == "") sec = "Open"
      print ssid ":" sec ":" sig
    }
    ssid = ""; sec = ""; sig = 0;
  }
  /Quality=/ {
    # Handles "Quality=58/70  Signal level=-52 dBm"
    if (match($0, /Quality=([0-9]+)\/([0-9]+)/, q)) {
      sig = int((q[1] / q[2]) * 100)
    } else if (match($0, /Signal level=([0-9]+)\/100/, q)) {
      sig = int(q[1])
    }
  }
  /Encryption key:off/ { sec = "Open" }
  /IE: IEEE 802.11i\/WPA2/ { sec = "WPA2" }
  /IE: WPA Version 1/ { if (sec == "") sec = "WPA" }
  /ESSID:/ {
    # Extract SSID between quotes
    if (match($0, /ESSID:"([^"]*)"/, e)) {
      ssid = e[1]
    }
  }
  END {
    if (ssid != "") {
      if (sec == "") sec = "Open"
      print ssid ":" sec ":" sig
    }
  }
' | while IFS=':' read -r ssid sec sig; do
  if [ -n "$ssid" ]; then
    # Sanitize security display
    [ -z "$sec" ] && sec="Open"

    # Convert numeric signal percentage into stars & qualitative label
    sig_num=${sig:-0}
    if [ "$sig_num" -ge 80 ]; then
      qual="**** (Excellent)"
    elif [ "$sig_num" -ge 55 ]; then
      qual="*** (Good)"
    elif [ "$sig_num" -ge 30 ]; then
      qual="** (Fair)"
    else
      qual="* (Weak)"
    fi

    # Print to user and record to temporary lookup table
    printf "%2d: %s [%s] %s\n" "$index" "$ssid" "$sec" "$qual"
    printf "%d\t%s\n" "$index" "$ssid" >> "$SCAN_TMP"
    index=$((index + 1))
  fi
done

total_scanned=$(wc -l < "$SCAN_TMP" 2>/dev/null | tr -d ' ')
[ -z "$total_scanned" ] && total_scanned=0

echo ""
echo " 0: [Enter Hidden / Manual SSID]"
echo " Q: Quit / Disconnect"
echo "--------------------------------------------------"

# 1. Prompt for Network Selection
printf "Select network [0-%s, or Q]: " "$total_scanned"
read -r choice
# Strip carriage return if sent over Telnet (\r\n)
choice=$(echo "$choice" | tr -d '\r\n ')

# Handle Quit
case "$choice" in
  [Qq]*)
    echo ""
    echo "Exiting configuration. Goodbye!"
    exit 0
    ;;
esac

TARGET_SSID=""

# 2. Process Selection or Manual Entry
if [ "$choice" = "0" ]; then
  echo ""
  printf "Enter SSID name: "
  read -r TARGET_SSID
  TARGET_SSID=$(echo "$TARGET_SSID" | tr -d '\r\n')
  
  if [ -z "$TARGET_SSID" ]; then
    echo ""
    echo "ERROR: SSID cannot be blank. Aborting."
    exit 1
  fi
else
  # Verify input is a valid number within range
  case "$choice" in
    ''|*[!0-9]*)
      echo ""
      echo "ERROR: Invalid selection '$choice'. Aborting."
      exit 1
      ;;
  esac

  if [ "$choice" -lt 1 ] || [ "$choice" -gt "$total_scanned" ]; then
    echo ""
    echo "ERROR: Selection out of range. Aborting."
    exit 1
  fi

  # Lookup SSID by index
  TARGET_SSID=$(awk -F'\t' -v sel="$choice" '$1 == sel {print $2}' "$SCAN_TMP")
fi

if [ -z "$TARGET_SSID" ]; then
  echo ""
  echo "ERROR: Could not resolve target SSID. Aborting."
  exit 1
fi

# 3. Prompt for Password / Key
echo ""
echo "Selected Network: $TARGET_SSID"
printf "Enter Password / Key (leave empty for Open): "
read -r PASS
PASS=$(echo "$PASS" | tr -d '\r\n')

# 4. Apply Settings and Connect
echo ""
echo "--------------------------------------------------"
echo "Connecting to '$TARGET_SSID'..."
echo "Please wait..."

# 1. Clear out old connection network profiles in wpa_supplicant
for net_id in $(wpa_cli -i wlan0 list_networks 2>/dev/null | awk 'NR>1 {print $1}'); do
  wpa_cli -i wlan0 remove_network "$net_id" >/dev/null 2>&1
done

# 2. Allocate a new network block
NET_ID=$(wpa_cli -i wlan0 add_network 2>/dev/null | tail -n 1)

if [ -z "$NET_ID" ] || [ "$NET_ID" = "FAIL" ]; then
  NM_STATUS=1
else
  # 3. Configure SSID
  wpa_cli -i wlan0 set_network "$NET_ID" ssid "\"$TARGET_SSID\"" >/dev/null 2>&1

  # 4. Configure Authentication
  if [ -n "$PASS" ]; then
    # WPA/WPA2 Pre-Shared Key
    wpa_cli -i wlan0 set_network "$NET_ID" psk "\"$PASS\"" >/dev/null 2>&1
  else
    # Open / unencrypted network
    wpa_cli -i wlan0 set_network "$NET_ID" key_mgmt NONE >/dev/null 2>&1
  fi

  # 5. Enable network and save configuration
  wpa_cli -i wlan0 enable_network "$NET_ID" >/dev/null 2>&1
  wpa_cli -i wlan0 select_network "$NET_ID" >/dev/null 2>&1
  wpa_cli -i wlan0 save_config >/dev/null 2>&1

  # 6. Fast polling loop: Wait up to 10 seconds for association
  connected=0
  for i in $(seq 1 10); do
    state=$(wpa_cli -i wlan0 status 2>/dev/null | awk -F= '$1=="wpa_state" {print $2}')
    if [ "$state" = "COMPLETED" ]; then
      connected=1
      break
    fi
    sleep 1
  done

  if [ $connected -eq 1 ]; then
    # 7. Request DHCP lease (using busybox udhcpc or dhcpcd)
    if command -v udhcpc >/dev/null 2>&1; then
      udhcpc -i wlan0 -n -q -t 5 >/dev/null 2>&1
    elif command -v dhcpcd >/dev/null 2>&1; then
      dhcpcd -n wlan0 >/dev/null 2>&1
    fi
    NM_STATUS=0
  else
    NM_STATUS=1
  fi
fi

echo ""
if [ $NM_STATUS -eq 0 ]; then
  echo "SUCCESS: Connected to $TARGET_SSID!"  
  systemctl restart ctohm-menu.service
else
  echo "FAILED: Could not connect to $TARGET_SSID."
  echo "Check your credentials or signal and try again."
fi

echo ""
echo "Press [Enter] to disconnect session..."
read -r dummy
exit $NM_STATUS
