#!/usr/bin/env python3
import time
import os
import threading
import subprocess
import signal
from gpiozero import Button
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont
from pathlib import Path
# 1. Initialize Display
try:
    serial = i2c(port=1, address=0x3c)
    device = ssd1306(serial)
except Exception as e:
    print(f"Hardware initialization failed: {e}")
    exit(1)


oledfont = ImageFont.load("oledfont.pil")
menu_y = [16, 28, 40]

# --- MENU DATA STRUCTURES ---
main_menu = [
    "select mode",
    "select bitrate",
    "select data bits",
    "select parity",
    "select stop bits",
    "REBOOT",
    "SHUT DOWN"
]

mode_menu = ["  PPP", "  HAYES", "  SLIP", "  CSLIP", "  SHELL", "  NULL MODEM", "  LOOPBACK"]
mode_status = ["PPP  ", "HAYES", "SLIP ", "CSLIP", "SHELL", "NULLM", "LOOP "]
bitrate_menu = ["  300", "  1200", "  2400", "  4800", "  9600", "  19200", "  38400", "  57600", "  115200", "  230400"]
databits_menu = ["  5", "  6", "  7", "  8"]
parity_menu = ["  NONE", "  EVEN", "  ODD"]
stopbits_menu = ["  1", "  2"]
config_file = "/etc/connectohm.conf"

# Confirmation menu (Default position: NO)
confirm_menu = ["ARE YOU SURE?", "  NO", "  YES"]

# --- ACTIVE SYSTEM CONFIGURATION ---
config = {
    "mode": 1,        # Default: HAYES
    "bitrate": 8,     # Default: 115200
    "databits": 3,    # Default: 8
    "parity": 0,      # Default: NONE
    "stopbits": 0     # Default: 1
}

def save_settings():
    with open(config_file, "w") as f:
        f.write(str(config))

def load_settings():
    try:
        with open(config_file, "r") as f:
            config = f.read()
    except FileNotFoundError:
        print(f"{config_file} not found, recreating.")
        save_settings();

load_settings()

# --- STATE MACHINE TRACKING ---
current_menu = "MAIN"
main_cursor = 0
sub_cursor = 0
window_top = 0
inverted_item = None
pppd_process = None

# Button Setup (GPIO 26 -> GND)
button = Button(26, pull_up=True, bounce_time=0.05)
last_release_time = 0
tap_timer = None
DOUBLE_TAP_THRESHOLD = 0.3

# --- DRAW HELPERS ---
def draw_ohm(draw, x, y, fill="black"):
    draw.line((x+2, y, x+4, y), fill=fill)
    draw.line((x+1, y+1, x+1, y+3), fill=fill)
    draw.line((x+5, y+1, x+5, y+3), fill=fill)
    draw.point((x+2, y+4), fill=fill)
    draw.point((x+4, y+4), fill=fill)
    draw.line((x, y+5, x+2, y+5), fill=fill)
    draw.line((x+4, y+5, x+6, y+5), fill=fill)

def draw_arrow_up(draw, x=120, y=19, fill="white"):
    draw.polygon([(x + 2, y), (x, y + 4), (x + 4, y + 4)], fill=fill)

def draw_arrow_down(draw, x=120, y=43, fill="white"):
    draw.polygon([(x, y), (x + 4, y), (x + 2, y + 4)], fill=fill)

def display_message(line1, line2=""):
    """Utility to display full screen status messages during shutdown/reboot."""
    with canvas(device) as draw:
        draw.rectangle((0, 0, 127, 16), fill="white")
        draw.text((1, 2), "Connect\u00a9 Notice", font=oledfont, fill="black") # Header fallback
        draw.text((1, 24), line1, font=oledfont, fill="white")
        if line2:
            draw.text((1, 38), line2, font=oledfont, fill="white")

def get_active_menu():
    if current_menu == "MAIN": return main_menu, main_cursor
    elif current_menu == "MODE": return mode_menu, sub_cursor
    elif current_menu == "BITRATE": return bitrate_menu, sub_cursor
    elif current_menu == "DATABITS": return databits_menu, sub_cursor
    elif current_menu == "PARITY": return parity_menu, sub_cursor
    elif current_menu == "STOPBITS": return stopbits_menu, sub_cursor
    elif current_menu in ["CONFIRM_REBOOT", "CONFIRM_SHUTDOWN"]:
        return confirm_menu, sub_cursor

def render_display():
    global window_top
    active_list, cursor_pos = get_active_menu()

    # Windowing scroll math
    if cursor_pos < window_top:
        window_top = cursor_pos
    elif cursor_pos >= window_top + 3:
        window_top = cursor_pos - 2

    # Dynamic Header String
    m_str = mode_status[config["mode"]]
    b_str = bitrate_menu[config["bitrate"]].strip()
    d_str = databits_menu[config["databits"]].strip()
    p_str = parity_menu[config["parity"]].strip()[0]
    s_str = stopbits_menu[config["stopbits"]].strip()

    header_str = f"C  | {m_str} {b_str} {d_str}{p_str}{s_str}"

    with canvas(device) as draw:
        # 1. Header Box
        draw.rectangle((0, 0, 127, 16), fill="white")
        draw.text((1, 2), header_str, font=oledfont, fill="black")
        draw_ohm(draw, x=7, y=6, fill="black")

        # 2. Render Options
        if current_menu in ["CONFIRM_REBOOT", "CONFIRM_SHUTDOWN"]:
            # Custom prompt for confirmation
            title = "REBOOT?" if current_menu == "CONFIRM_REBOOT" else "SHUT DOWN?"
            draw.text((1, menu_y[0]), title, font=oledfont, fill="white")

            # Draw NO (index 1) and YES (index 2)
            for idx in [1, 2]:
                y_pos = menu_y[idx]
                label = "NO" if idx == 1 else "YES"
                if idx == inverted_item:
                    draw.rectangle((0, y_pos, 127, y_pos + 11), fill="white")
                    draw.text((1, y_pos), f"> {label}", font=oledfont, fill="black")
                else:
                    prefix = "> " if idx == sub_cursor else "  "
                    draw.text((1, y_pos), f"{prefix}{label}", font=oledfont, fill="white")
        else:
            # Standard List Rendering
            for row in range(3):
                item_idx = window_top + row
                if item_idx < len(active_list):
                    y_pos = menu_y[row]
                    text_str = active_list[item_idx]
                    display_text = text_str.strip() if current_menu != "MAIN" else text_str

                    if item_idx == inverted_item:
                        draw.rectangle((0, y_pos, 127, y_pos + 11), fill="white")
                        draw.text((1, y_pos), f"> {display_text}", font=oledfont, fill="black")
                    else:
                        prefix = "> " if item_idx == cursor_pos else "  "
                        draw.text((1, y_pos), f"{prefix}{display_text}", font=oledfont, fill="white")

        # 3. Footer Line
        draw.line((0, 52, 127, 52), fill="white")
        draw.text((1, 52), "SSN: not connected", font=oledfont, fill="white")

        # 4. Scroll Arrows (Disable during confirmations)
        if current_menu not in ["CONFIRM_REBOOT", "CONFIRM_SHUTDOWN"]:
            if window_top > 0:
                draw_arrow_up(draw)
            if window_top + 3 < len(active_list):
                draw_arrow_down(draw)

def apply_serial_settings():
    """Applies active menu configuration to the physical Pi serial port."""
    baud = bitrate_menu[config["bitrate"]].strip()
    dbits = databits_menu[config["databits"]].strip()
    parity = parity_menu[config["parity"]].strip()
    sbits = stopbits_menu[config["stopbits"]].strip()

    # Map parity string to stty flags
    if parity == "NONE":
        p_flags = "-parenb"
    elif parity == "EVEN":
        p_flags = "parenb -parodd"
    elif parity == "ODD":
        p_flags = "parenb parodd"

    # Map stop bits flag
    s_flag = "cstopb" if sbits == "2" else "-cstopb"

    # Construct and execute stty command on serial port (e.g., /dev/ttyAMA0)
    cmd = f"stty -F /dev/ttyAMA0 {baud} cs{dbits} {p_flags} {s_flag} raw -echo"
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"Serial port configured: {baud} {dbits}{parity[0]}{sbits}")
    except Exception as e:
        print(f"Failed to apply serial settings: {e}")

def start_ppp_daemon():
    global pppd_process
    stop_ppp_daemon() # Ensure clean state first

    baud = bitrate_menu[config["bitrate"]].strip()
    # Command array based on your governor settings
    cmd = [
        "sudo", "pppd", "/dev/ttyAMA0", baud,
        "192.168.2.1:192.168.2.2",
        "local", "ms-dns", "1.1.1.1",
        "noauth", "passive", "persist"
    ]
    try:
        pppd_process = subprocess.Popen(cmd)
        print("PPP Daemon Started.")
    except Exception as e:
        print(f"Failed to launch pppd: {e}")

def stop_ppp_daemon():
    global pppd_process
    if pppd_process and pppd_process.poll() is None:
        pppd_process.terminate()
        pppd_process.wait()
        pppd_process = None
        print("PPP Daemon Stopped.")
    else:
        # Fallback system sweep
        os.system("sudo killall pppd 2>/dev/null")

def update_system_state():
    """Writes active UI config to /tmp/ for udev and background daemons."""
    selected_mode = mode_status[config["mode"]].strip()
    selected_baud = bitrate_menu[config["bitrate"]].strip()

    with open("/tmp/ctohm_mode", "w") as f:
        f.write(selected_mode)

    with open("/tmp/ctohm_baud", "w") as f:
        f.write(selected_baud)

    # If switching away from PPP, kill any running pppd instances
    if selected_mode != "PPP":
        os.system("sudo killall pppd 2>/dev/null")

def on_single_tap():
    global main_cursor, sub_cursor 

    if current_menu in ["CONFIRM_REBOOT", "CONFIRM_SHUTDOWN"]:
        # Toggle sub_cursor strictly between 1 (NO) and 2 (YES)
        sub_cursor = 2 if sub_cursor == 1 else 1
    else:
        active_list, cursor_pos = get_active_menu()
        next_pos = (cursor_pos + 1) % len(active_list)
        if current_menu == "MAIN":
            main_cursor = next_pos
        else:
            sub_cursor = next_pos

        render_display()

def on_double_tap():
    global current_menu, sub_cursor, window_top, inverted_item, config
    active_list, cursor_pos = get_active_menu()

    # If switching away from PPP, kill any running pppd 
    # instances Invert visual feedback
    inverted_item = cursor_pos 
    render_display()
    time.sleep(0.2)
    inverted_item = None
    if current_menu == "MAIN":
        window_top = 0
        if main_cursor == 0: current_menu = "MODE"; sub_cursor = config["mode"]
        elif main_cursor == 1: current_menu = "BITRATE"; sub_cursor = config["bitrate"]
        elif main_cursor == 2: current_menu = "DATABITS"; sub_cursor = config["databits"]
        elif main_cursor == 3: current_menu = "PARITY"; sub_cursor = config["parity"]
        elif main_cursor == 4: current_menu = "STOPBITS"; sub_cursor = config["stopbits"]
        elif main_cursor == 5:
            current_menu = "CONFIRM_REBOOT"
            sub_cursor = 1  # Default cursor position on 'NO'
        elif main_cursor == 6:
            current_menu = "CONFIRM_SHUTDOWN"
            sub_cursor = 1  # Default cursor position on 'NO'

    elif current_menu in ["CONFIRM_REBOOT", "CONFIRM_SHUTDOWN"]:
        if sub_cursor == 1:
            # NO selected -> Return to Main Menu
            current_menu = "MAIN"
            window_top = 0
            render_display()
        elif sub_cursor == 2:
            # YES selected -> Execute System Action
            if current_menu == "CONFIRM_REBOOT":
                display_message("REBOOTING...", "Please wait...")
                time.sleep(1.5)
                device.clear()
                os.system("sudo reboot")
                return
            elif current_menu == "CONFIRM_SHUTDOWN":
                display_message("SHUTTING DOWN...", "Safe to unplug soon")
                time.sleep(2.0)
                device.clear()
                os.system("sudo poweroff")
                return
    else:
        # Save selection from Submenu & Return to Main
        if current_menu == "MODE": config["mode"] = sub_cursor
        elif current_menu == "BITRATE": config["bitrate"] = sub_cursor
        elif current_menu == "DATABITS": config["databits"] = sub_cursor
        elif current_menu == "PARITY": config["parity"] = sub_cursor
        elif current_menu == "STOPBITS": config["stopbits"] = sub_cursor

        # Apply updated settings to serial hardware
        apply_serial_settings()

        # Handle Mode Setting
        selected_mode_name = mode_status[config["mode"]].strip()
        update_system_state()

#        if selected_mode_name == "PPP":
#            start_ppp_daemon()
#        else:
#            stop_ppp_daemon()

        current_menu = "MAIN"
        window_top = 0

    render_display()

def handle_button_release():
    global last_release_time, tap_timer
    now = time.time()
    elapsed = now - last_release_time
    last_release_time = now

    if elapsed < DOUBLE_TAP_THRESHOLD:
        if tap_timer and tap_timer.is_alive():
            tap_timer.cancel()
        on_double_tap()
    else:
        tap_timer = threading.Timer(DOUBLE_TAP_THRESHOLD, on_single_tap)
        tap_timer.start()

button.when_released = handle_button_release

# Initial Render
render_display()

print("ConnectOhm Full UI Running...")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nExiting UI...")
