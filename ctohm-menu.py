#!/usr/bin/env python3
import time
import os
import threading
import subprocess
import signal
import re
from gpiozero import Button
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont, Image, ImageDraw

# Initialize display
try:
    serial = i2c(port=1, address=0x3c)
    device = ssd1306(serial)
    device.cleanup = lambda: None
except Exception as e:
    print(f"Hardware initialization failed: {e}")
    exit(1)

# Load font
oledfont = ImageFont.load("/usr/local/lib/connectohm/oledfont.pil")

mode_programs = ["pppd", "tcpser", "slirp", "agetty"]
# Menu data structures
main_menu = ["select mode", "select bitrate", "select data bits", "select parity", "select stop bits", "REBOOT", "SHUT DOWN"]
mode_menu = ["  PPP", "  HAYES", "  SLIP/CSLIP", "  SHELL"]
mode_status = ["PPP  ", "HAYES", "CSLIP", "SHELL"]
bitrate_menu = ["  300", "  1200", "  2400", "  4800", "  9600", "  19200", "  38400", "  57600", "  115200", "  230400"]
databits_menu = ["  5", "  6", "  7", "  8"]
parity_menu = ["  NONE", "  EVEN", "  ODD"]
stopbits_menu = ["  1", "  2"]
confirm_menu = ["", "  NO", "  YES"]
menu_y = [16, 28, 40]

# Config structures and functions
config = {
    "mode": 0,        # Default: PPP
    "bitrate": 8,     # Default: 115200
    "databits": 3,    # Default: 8
    "parity": 0,      # Default: NONE
    "stopbits": 0     # Default: 1
}
config_file = "/etc/connectohm.conf"

# Global reference to hold the active drawing image
current_image = None

def save_oled_gif(signum=None, frame=None):
    """Signal handler for SIGUSR1 to dump the current OLED screen to a 2x scaled GIF."""
    global current_image
    if current_image is None:
        return
    try:
        oled_w, oled_h = 128, 64
        scale = 2
        
        # Color definitions (RGB)
        c_off = (0, 0, 0)          # Black
        c_yellow = (255, 255, 0)   # Yellow (Rows 0-15)
        c_cyan = (0, 255, 255)     # Cyan (Rows 16-63)

        rgb_img = Image.new("RGB", (oled_w, oled_h+2), c_off)
        mono_pixels = current_image.convert("1").load()
        rgb_pixels = rgb_img.load()

        for y in range(oled_h):
            active_color = c_yellow if y < 16 else c_cyan
            this_y = y
            if y > 15:
                this_y += 2
            for x in range(oled_w):
                if mono_pixels[x, y]:
                    rgb_pixels[x, this_y] = active_color
                else:
                    rgb_pixels[x, this_y] = c_off

        # Black out lines 16 & 17
        for x in range(oled_w):
            rgb_pixels[x, 16] = c_off
            rgb_pixels[x, 17] = c_off

        # Scale 2x with NEAREST for crisp square pixel blocks
        scaled_img = rgb_img.resize((oled_w * scale, oled_h * scale), resample=Image.NEAREST)
        gif_img = scaled_img.convert("P", palette=Image.ADAPTIVE)
        
        # Save to web root (or wherever you want it accessible)
        out_path = "/root/connectohm/oled.gif"
        gif_img.save(out_path, format="GIF")
        print(f"[ctohm-menu] Screenshot saved to {out_path}")
    except Exception as e:
        print(f"[ctohm-menu] Failed to save screenshot: {e}")

# Register SIGUSR1 signal handler
signal.signal(signal.SIGUSR1, save_oled_gif)

def new_settings():
    with open(config_file, "w") as f:
        f.write("# All options start from 0.\n")
        f.write("\n")
        f.write("# Modes: PPP, Hayes, SLIP/CSLIP, shell\n")
        f.write("# Default: PPP\n")
        f.write("mode=0\n")
        f.write("\n")
        f.write("# Bitrates: 300, 1200, 2400, 4800, 9600, 19200, 28400, 57600, 115200, 230400\n")
        f.write("# Default: 115200\n")
        f.write("bitrate=8\n")
        f.write("\n")
        f.write("# Data bits: 5, 6, 7, 8\n")
        f.write("# Default: 8\n")
        f.write("databits=3\n")
        f.write("\n")
        f.write("# Parity: none, even, odd\n")
        f.write("# Default: none\n")
        f.write("parity: 0\n")
        f.write("\n")
        f.write("# Stop bits: 1, 2\n")
        f.write("# Default: 1\n")
        f.write("stopbits=0\n")


def save_settings():
    updated_lines = []
    seen_keys = set()

    # 1. Read and update existing lines if the file exists
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            for line in f:
                stripped = line.strip()

                # Preserve comment lines and blank lines exactly as they are
                if not stripped or stripped.startswith("#"):
                    updated_lines.append(line)
                    continue

                # Process key=value lines
                if "=" in stripped:
                    key = stripped.split("=", 1)[0].strip()
                    if key in config:
                        # Replace with the new value from config dict
                        updated_lines.append(f"{key}={config[key]}\n")
                        seen_keys.add(key)
                    else:
                        # Keep untouched if not present in our config dict
                        updated_lines.append(line)
                else:
                    # Keep any malformed/other lines untouched
                    updated_lines.append(line)

    # 2. Append any new keys from config that weren't already in the file
    for key, val in config.items():
        if key not in seen_keys:
            updated_lines.append(f"{key}={val}\n")

    # 3. Write back the updated content
    with open(config_file, "w") as f:
        f.writelines(updated_lines)

def load_settings():
    try:
        with open(config_file, "r") as f:
            for line in f:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if not "=" in stripped:
                    continue
                key, val = stripped.split("=")
                if not key in config:
                    continue
                config[key]=int(val)
    except FileNotFoundError:
        print(f"{config_file} not found, recreating.")
        new_settings()
    else:
        return

load_settings()

# Menu state tracking
current_menu = "MAIN"
main_cursor = 0
sub_cursor = 0
window_top = 0
inverted_item = None
pppd_process = None

# Button setup (GPIO 26 -> GND)
button = Button(26, pull_up=True, bounce_time=0.05)
last_release_time = 0
tap_timer = None
DOUBLE_TAP_THRESHOLD = 0.3

def kill_mode_processes():
    """
    Loops through mode_programs and terminates any process whose command-line
    contains BOTH the program name AND 'ctohm' immediately followed by a digit.
    """
    # Regex to match 'ctohm' followed immediately by a digit (e.g., ctohm0, ctohm1)
    ctohm_pattern = re.compile(r'ctohm\d')
    my_pid = os.getpid()

    # Get all running numeric PIDs from /proc
    pids = [int(p) for p in os.listdir('/proc') if p.isdigit()]

    for pid in pids:
        if pid == my_pid:
            continue

        cmdline_path = f'/proc/{pid}/cmdline'
        try:
            with open(cmdline_path, 'rb') as f:
                # /proc/[pid]/cmdline separates arguments by null bytes (\x00)
                cmdline = f.read().decode('utf-8', errors='ignore').replace('\x00', ' ')
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            # Process may have terminated or belongs to another user
            continue

        # Check if the process matches our ctohm<digit> pattern
        if ctohm_pattern.search(cmdline):
            for prog in mode_programs:
                # Check if the target program name is also present in the command line
                if prog in cmdline:
                    try:
                        print(f"Killing PID {pid}: {cmdline.strip()}")
                        # Send SIGTERM first for graceful exit, fallback to SIGKILL if needed
                        os.kill(pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    except PermissionError:
                        print(f"Permission denied killing PID {pid}. (Run with sudo)")
                    break

# Drawing helper functions
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
    with canvas(device) as draw:
        draw.rectangle((0, 0, 127, 16), fill="white")
        draw.text((1, 2), "ConnectOhm Notice", font=oledfont, fill="black") # Header fallback
        draw.text((1, 24), line1, font=oledfont, fill="white")
        if line2:
            draw.text((1, 38), line2, font=oledfont, fill="white")

def get_active_menu():
    match current_menu:
        case "MAIN": return main_menu, main_cursor
        case "MODE": return mode_menu, sub_cursor
        case "BITRATE": return bitrate_menu, sub_cursor
        case "DATABITS": return databits_menu, sub_cursor
        case "PARITY": return parity_menu, sub_cursor
        case "STOPBITS": return stopbits_menu, sub_cursor
        case _: return confirm_menu, sub_cursor

def get_wifi_ssid():
    """
    Returns 'SSID: <SSID>' if connected to Wi-Fi, or 'SSID: not connected'.
    """
    ssid = None

    try:
        res = subprocess.run(["iwgetid", "-r"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0 and res.stdout.strip():
            ssid = res.stdout.strip()
    except Exception:
        pass

    if ssid:
        # "SSID: " is 6 chars, so clamp SSID to 12 chars
        max_ssid_len = 12
        truncated_ssid = ssid[:max_ssid_len]
        return f"SSID: {truncated_ssid}"
    else:
        return "SSID: not connected"
    
# Main drawing function, updates the screen
def render_display():
    global window_top
    global current_image
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

    # img = Image.new("1", (device.width, device.height), 0)
    # draw = ImageDraw.Draw(img)

    c = canvas(device)
    with c as draw:
        # Draw our status box and fill it in
        draw.rectangle((0, 0, 127, 16), fill="white")
        draw.text((1, 2), header_str, font=oledfont, fill="black")
        draw_ohm(draw, x=7, y=6, fill="black")

        # Draw our menus and highlights (if any)
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

            # 4. Scroll Arrows (Disable during confirmations)
            if current_menu not in ["CONFIRM_REBOOT", "CONFIRM_SHUTDOWN"]:
                if window_top > 0:
                    draw_arrow_up(draw)
                if window_top + 3 < len(active_list):
                    draw_arrow_down(draw)

            # 5. SSID status line
            status_str = get_wifi_ssid()
            draw.line((0, 52, 127, 52), fill="white")
            draw.text((1, 52), status_str, font=oledfont, fill="white")

            # 6. Save screen in case save_oled_gif gets triggered
            current_image = c.image.copy()

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

    # Invert visual feedback
    inverted_item = cursor_pos 
    render_display()
    time.sleep(0.2)
    inverted_item = None
    if current_menu == "MAIN":
        window_top = 0
        match main_cursor:
            case 0: current_menu = "MODE"; sub_cursor = config["mode"]
            case 1: current_menu = "BITRATE"; sub_cursor = config["bitrate"]
            case 2: current_menu = "DATABITS"; sub_cursor = config["databits"]
            case 3: current_menu = "PARITY"; sub_cursor = config["parity"]
            case 4: current_menu = "STOPBITS"; sub_cursor = config["stopbits"]
            case 5:
                current_menu = "CONFIRM_REBOOT"
                sub_cursor = 1  # Default cursor position on 'NO'
            case 6:
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
                display_message("SHUTTING DOWN...", "Please wait...")
                time.sleep(2.0)
                device.clear()
                os.system("sudo poweroff")
                return
    else:
        # Save selection from Submenu & Return to Main
        match current_menu:
            case "MODE": config["mode"] = sub_cursor
            case "BITRATE": config["bitrate"] = sub_cursor
            case "DATABITS": config["databits"] = sub_cursor
            case "PARITY": config["parity"] = sub_cursor
            case "STOPBITS": config["stopbits"] = sub_cursor

        save_settings()
        selected_mode_name = mode_status[config["mode"]].strip()
        kill_mode_processes()
        subprocess.run(["udevadm", "trigger", "--subsystem-match=tty", "--action=add"], check=True)
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

# *** MAIN CODE BEGINS HERE ***

# Initial Render
render_display()

print("ConnectOhm Full UI Running...")
try:
    # I think I'd rather loop until <ESC> is pressed
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nExiting UI...")
