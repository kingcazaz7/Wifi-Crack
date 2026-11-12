import os
import re
import glob
import shutil
import subprocess
from datetime import datetime

CYAN = "\033[96m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

BASE = os.path.dirname(os.path.abspath(__file__))
CAP_DIR = os.path.join(BASE, "captures")
REPORT = os.path.join(BASE, "WPA Handshake")


def banner():
    os.system("clear")
    print(CYAN + """
           _____ _____      _         ____  
     /\   |_   _|  __ \    | |  /\   |  _ \ 
    /  \    | | | |__) |   | | /  \  | |_) |
   / /\ \   | | |  _  /_   | |/ /\ \ |  _ < 
  / ____ \ _| |_| | \ \ |__| / ____ \| |_) |
 /_/    \_\_____|_|  \_\____/_/    \_\____/

==========================================
   GitHub | https://github.com/Kingcazaz7
==========================================
""" + RESET)


def tools_check():
    tools = ["iw", "airodump-ng", "aircrack-ng"]

    missing = [t for t in tools if not shutil.which(t)]

    if missing:
        print(RED + "Missing tools: " + ", ".join(missing))
        print("Install: sudo apt install aircrack-ng iw")
        return False

    return True


def interfaces():
    result = subprocess.run(
        ["iw", "dev"],
        capture_output=True,
        text=True
    )

    found = re.findall(
        r"^\s*Interface\s+(\S+)",
        result.stdout,
        re.M
    )

    return found


def monitor_check():
    print(CYAN + "\n[*] Checking wireless interfaces..." + RESET)

    found = interfaces()

    if not found:
        print(RED + "No wireless interface found.")
        return

    for iface in found:
        result = subprocess.run(
            ["iw", "dev", iface, "info"],
            capture_output=True,
            text=True
        )

        mode = "Monitor" if "type monitor" in result.stdout else "Managed"

        print(f"{iface} : {mode}")


def select_monitor():
    found = interfaces()

    for iface in found:
        result = subprocess.run(
            ["iw", "dev", iface, "info"],
            capture_output=True,
            text=True
        )

        if "type monitor" in result.stdout:
            return iface

    print(RED + "No Monitor Mode interface found.")
    print("Check your adapter and monitor mode.")
    return None


def scan_wifi():
    iface = select_monitor()

    if not iface:
        return

    print(GREEN + f"\nScanning with {iface}")
    print(YELLOW + "Press CTRL+C to stop scanning.\n" + RESET)

    try:
        subprocess.run(["airodump-ng", iface])
    except KeyboardInterrupt:
        print(GREEN + "\nScan stopped." + RESET)


def verify_handshake(cap_file, bssid):
    print(CYAN + "\n[*] Verifying capture..." + RESET)

    result = subprocess.run(
        ["aircrack-ng", "-b", bssid, cap_file],
        capture_output=True,
        text=True
    )

    output = result.stdout + result.stderr

    if re.search(r"WPA\s*\(\s*\d+\s*handshake", output, re.I):
        status = "Handshake detected"
        print(GREEN + "[+] " + status + RESET)

    elif re.search(r"WPA\s*\(\s*0\s*handshake", output, re.I):
        status = "No handshake detected"
        print(YELLOW + "[-] " + status + RESET)

    else:
        status = "Handshake not confirmed"
        print(YELLOW + "[?] " + status + RESET)

    with open(REPORT, "a") as f:
        f.write(
            f"{datetime.now()} | {bssid} | "
            f"{cap_file} | {status}\n"
        )

    print(GREEN + f"[+] Report: {REPORT}" + RESET)


def capture_wifi():
    iface = select_monitor()

    if not iface:
        return

    print(CYAN + "\nCAPTURE YOUR OWN ROUTER")
    print("Use only a network you own or have permission to test.\n")

    bssid = input("Router BSSID: ").strip()

    if not re.fullmatch(
        r"(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}",
        bssid
    ):
        print(RED + "Invalid BSSID")
        return

    channel = input("Router channel: ").strip()

    if not channel.isdigit() or not 1 <= int(channel) <= 233:
        print(RED + "Invalid channel")
        return

    name = datetime.now().strftime("capture_%Y%m%d_%H%M%S")
    prefix = os.path.join(CAP_DIR, name)

    os.makedirs(CAP_DIR, exist_ok=True)

    print(GREEN + "\n[*] Starting passive capture...")
    print("[*] Reconnect your own device normally.")
    print("[*] Press CTRL+C to stop.\n" + RESET)

    try:
        subprocess.run([
            "airodump-ng",
            "-c", channel,
            "--bssid", bssid,
            "-w", prefix,
            iface
        ])
    except KeyboardInterrupt:
        print(YELLOW + "\nCapture stopped." + RESET)

    files = glob.glob(prefix + "*.cap")

    if not files:
        print(RED + "No CAP file was created.")
        return

    cap_file = max(files, key=os.path.getmtime)

    print(GREEN + f"\nCAP file: {cap_file}" + RESET)

    verify_handshake(cap_file, bssid)


def analyze_existing():
    files = glob.glob(os.path.join(CAP_DIR, "*.cap"))

    if not files:
        print(YELLOW + "No CAP files found.")
        return

    print(CYAN + "\nAvailable CAP files:" + RESET)

    for i, file in enumerate(files, 1):
        print(f"{i}. {os.path.basename(file)}")

    choice = input("\nChoose file number: ").strip()

    if not choice.isdigit() or not 1 <= int(choice) <= len(files):
        print(RED + "Invalid selection.")
        return

    bssid = input("Router BSSID: ").strip()

    if not re.fullmatch(
        r"(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}",
        bssid
    ):
        print(RED + "Invalid BSSID")
        return

    verify_handshake(files[int(choice) - 1], bssid)


def main():
    os.makedirs(CAP_DIR, exist_ok=True)

    if not tools_check():
        return

    while True:
        banner()

        print("1. Airodump-ng")
        print("2. Interface Check")
        print("3. Capture Handshake")
        print("4. Analyze Handshake Cap")
        print("5. Exit")

        choice = input("\nSelect: ").strip()

        if choice == "1":
            scan_wifi()

        elif choice == "2":
            monitor_check()

        elif choice == "3":
            capture_wifi()

        elif choice == "4":
            analyze_existing()

        elif choice == "5":
            print(GREEN + "Airjab signing out!")
            break

        else:
            print(RED + "Invalid option.")

        input("\nPress ENTER to continue...")


if __name__ == "__main__":
    main()
