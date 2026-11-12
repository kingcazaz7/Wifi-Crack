import subprocess
import re
from datetime import datetime

INTERFACE = "wlan0"
LOG_FILE = "Scan-wifi"


def scan_wifi():
    print("\n[*] Airscan found")
    print("[*] Scanning nearby networks...\n")

    try:
        result = subprocess.run(
            ["iw", "dev", INTERFACE, "scan"],
            capture_output=True,
            text=True,
            check=True
        )
    except FileNotFoundError:
        print("[!] Install iw first: sudo apt install iw")
        return
    except subprocess.CalledProcessError:
        print("[!] Scan failed. Check interface and permissions.")
        return

    networks = []
    blocks = re.split(r"(?=^BSS )", result.stdout, flags=re.M)

    for block in blocks:
        if not block.startswith("BSS "):
            continue

        bssid_match = re.search(r"BSS ([0-9a-fA-F:]+)", block)
        ssid_match = re.search(r"^\s*SSID: ?(.*)$", block, re.M)
        freq_match = re.search(r"^\s*freq: (\d+)", block, re.M)
        signal_match = re.search(r"^\s*signal: ([-\d.]+)", block, re.M)

        if not bssid_match:
            continue

        bssid = bssid_match.group(1)
        ssid = ssid_match.group(1).strip() if ssid_match else "Hidden"
        freq = int(freq_match.group(1)) if freq_match else 0
        signal = signal_match.group(1) if signal_match else "Unknown"

        if 2412 <= freq <= 2484:
            channel = 14 if freq == 2484 else (freq - 2407) // 5
        elif 5000 <= freq <= 5895:
            channel = (freq - 5000) // 5
        elif 5955 <= freq <= 7115:
            channel = (freq - 5950) // 5
        else:
            channel = "Unknown"

        if "SAE" in block:
            security = "WPA3 / SAE"
        elif "RSN:" in block:
            security = "WPA2 / RSN"
        elif "WPA:" in block:
            security = "WPA"
        else:
            security = "Open / Unknown"

        networks.append(
            (ssid, bssid, channel, signal, security)
        )

    print("=" * 85)
    print(f"{'SSID':22} {'BSSID':20} {'CH':5} {'SIGNAL':10} SECURITY")
    print("=" * 85)

    for n in networks:
        print(f"{n[0][:21]:22} {n[1]:20} {str(n[2]):5} "
              f"{n[3]:10} {n[4]}")

    print("=" * 85)
    print(f"Total networks found: {len(networks)}")

    with open(LOG_FILE, "w") as f:
        f.write(f"Airscan: {datetime.now()}\n\n")
        for n in networks:
            f.write(
                f"SSID: {n[0]} | BSSID: {n[1]} | "
                f"Channel: {n[2]} | Signal: {n[3]} | "
                f"Security: {n[4]}\n"
            )

    print(f"\n[+] Saved results to {LOG_FILE}")
#copyright to (Kingcazaz7)

if __name__ == "__main__":
    scan_wifi()
