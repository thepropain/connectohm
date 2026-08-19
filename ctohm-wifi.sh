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
nmcli -t -f SSID,SECURITY,SIGNAL dev wifi list 2>/dev/null | while IFS=':' read -r ssid sec sig; do
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

if [ -n "$PASS" ]; then
  nmcli dev wifi connect "$TARGET_SSID" password "$PASS"
else
  nmcli dev wifi connect "$TARGET_SSID"
fi
NM_STATUS=$?

echo ""
if [ $NM_STATUS -eq 0 ]; then
  echo "SUCCESS: Connected to $TARGET_SSID!"
  
  # Allow network state to settle and trigger OLED update
  sleep 1
  systemctl restart ctohm-menu.service
else
  echo "FAILED: Could not connect to $TARGET_SSID."
  echo "Check your credentials or signal and try again."
fi

echo ""
echo "Press [Enter] to disconnect session..."
read -r dummy
exit $NM_STATUS
