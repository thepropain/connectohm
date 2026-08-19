#!/bin/sh
echo "Content-Type: text/html; charset=iso-8859-1"
echo ""

cat << 'EOF'
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
<head>
  <title>ConnectOhm Wi-Fi Setup</title>
</head>
<body bgcolor="#FFFFFF" text="#000000">

<h2>ConnectOhm Wi-Fi Setup</h2>
<hr>

<form action="/cgi-bin/set_wifi.cgi" method="GET">

  <p><b>1. Select Available Network:</b><br>
  <select name="scanned_ssid" size="6">
    <option value="" selected>-- [Select Scanned SSID] --</option>
EOF

# Query SSID, SECURITY, and numeric SIGNAL (0-100) via iwlist
iwlist wlan0 scan 2>/dev/null | awk '
  /Cell [0-9]+/ {
    if (ssid != "") {
      if (sec == "") sec = "Open"
      print ssid ":" sec ":" sig
    }
    ssid = ""; sec = ""; sig = 0;
  }
  /Quality=/ {
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
    # Default open networks
    [ -z "$sec" ] && sec="Open"

    # Convert numeric signal percentage into stars & text
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

    echo "    <option value=\"$ssid\">$ssid [$sec] $qual</option>"
  fi
done

cat << 'EOF'
  </select>
  </p>

  <p><b>2. Or Enter Hidden / Manual SSID:</b><br>
  <input type="text" name="manual_ssid" size="25" maxlength="32">
  </p>

  <p><b>3. Password / Key:</b><br>
  <input type="password" name="password" size="25" maxlength="64">
  </p>

  <hr>
  <p>
    <input type="submit" value="Connect">
    <input type="reset" value="Clear">
  </p>
</form>

</body>
</html>
EOF
