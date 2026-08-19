#!/bin/sh
echo "Content-Type: text/html"
echo ""

# Read POST body from stdin (handles both bounded CONTENT_LENGTH and unbounded stream)
if [ "$REQUEST_METHOD" = "POST" ]; then
  if [ -n "$CONTENT_LENGTH" ]; then
    POST_DATA=$(dd bs=1 count="$CONTENT_LENGTH" 2>/dev/null)
  else
    POST_DATA=$(cat)
  fi
else
  POST_DATA="$QUERY_STRING"
fi

# URL decode helper
urldecode() {
  printf '%b' "$(echo "$1" | sed 's/+/ /g; s/%\([0-9A-Fa-f]\{2\}\)/\\x\1/g')"
}

# Parse key=value pairs out of POST_DATA
SCANNED=""
MANUAL=""
PASS=""

IFS='&'
for pair in $POST_DATA; do
  case "$pair" in
    scanned_ssid=*)
      SCANNED=$(urldecode "${pair#scanned_ssid=}")
      ;;
    manual_ssid=*)
      MANUAL=$(urldecode "${pair#manual_ssid=}")
      ;;
    password=*)
      PASS=$(urldecode "${pair#password=}")
      ;;
  esac
done
unset IFS

# Prefer manual entry if typed, otherwise fall back to scanned list selection
TARGET_SSID="$MANUAL"
if [ -z "$TARGET_SSID" ]; then
  TARGET_SSID="$SCANNED"
fi

cat << EOF
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
<head><title>Connecting...</title></head>
<body bgcolor="#FFFFFF" text="#000000">
<h3>Applying Wi-Fi Settings...</h3>
<hr>
<p>Target Network: <b>${TARGET_SSID:-[None]}</b></p>
EOF

if [ -n "$TARGET_SSID" ]; then
  echo "<p>Sending connection request to system...</p>"

# Run wpa_cli connection, DHCP, and menu restart in background
  (
    # 1. Clear old networks
    for net_id in $(wpa_cli -i wlan0 list_networks 2>/dev/null | awk 'NR>1 {print $1}'); do
      wpa_cli -i wlan0 remove_network "$net_id" >/dev/null 2>&1
    done

    # 2. Add new network
    NET_ID=$(wpa_cli -i wlan0 add_network 2>/dev/null | tail -n 1)

    if [ -n "$NET_ID" ] && [ "$NET_ID" != "FAIL" ]; then
      # 3. Configure SSID
      wpa_cli -i wlan0 set_network "$NET_ID" ssid "\"$TARGET_SSID\"" >/dev/null 2>&1

      # 4. Configure Authentication
      if [ -n "$PASS" ]; then
        wpa_cli -i wlan0 set_network "$NET_ID" psk "\"$PASS\"" >/dev/null 2>&1
      else
        wpa_cli -i wlan0 set_network "$NET_ID" key_mgmt NONE >/dev/null 2>&1
      fi

      # 5. Enable & save
      wpa_cli -i wlan0 enable_network "$NET_ID" >/dev/null 2>&1
      wpa_cli -i wlan0 select_network "$NET_ID" >/dev/null 2>&1
      wpa_cli -i wlan0 save_config >/dev/null 2>&1

      # 6. Polling loop: Wait up to 10 seconds for association
      for i in $(seq 1 10); do
        state=$(wpa_cli -i wlan0 status 2>/dev/null | awk -F= '$1=="wpa_state" {print $2}')
        if [ "$state" = "COMPLETED" ]; then
          # 7. Request DHCP lease
          if command -v udhcpc >/dev/null 2>&1; then
            udhcpc -i wlan0 -n -q -t 5 >/dev/null 2>&1
          elif command -v dhcpcd >/dev/null 2>&1; then
            dhcpcd -n wlan0 >/dev/null 2>&1
          fi
          break
        fi
        sleep 1
      done
    fi

    # 8. Restart menu service so OLED refreshes with new SSID/IP
    systemctl restart ctohm-menu.service >/dev/null 2>&1
  ) >/dev/null 2>&1 &
  
  echo "<p>Connection command initiated! Check the OLED display for updated status.</p>"
else
  echo "<p><font color=\"red\"><b>Error:</b> No SSID was selected or entered.</font></p>"
fi

echo '<hr>'
echo '<p><a href="/cgi-bin/wifi.cgi">&lt;&lt; Back to Setup</a></p>'
echo '</body></html>'
