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

  if [ -n "$PASS" ]; then
    nmcli dev wifi connect "$TARGET_SSID" password "$PASS" >/dev/null 2>&1 &
  else
    nmcli dev wifi connect "$TARGET_SSID" >/dev/null 2>&1 &
  fi

  # Sleep briefly and trigger your screen updater
  (sleep 3 && systemctl restart ctohm-menu.service) &

  echo "<p>Connection command initiated! Check the OLED display for updated status.</p>"
else
  echo "<p><font color=\"red\"><b>Error:</b> No SSID was selected or entered.</font></p>"
  echo "<p><small>Debug received payload: <code>${POST_DATA}</code></small></p>"
fi

echo '<hr>'
echo '<p><a href="/cgi-bin/wifi.cgi">&lt;&lt; Back to Setup</a></p>'
echo '</body></html>'
