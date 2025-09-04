# Handles detection and info retrieval for external disks on Android

import subprocess
import json

def list_external_disks():
    """
    Returns a list of detected external disks (USB/SD) connected to the Android device using adb.
    Each disk is represented as a dictionary with basic info.
    """
    try:
        # Use 'adb shell lsblk' to list block devices
        result = subprocess.run(["adb", "shell", "lsblk -J"], capture_output=True, text=True)
        if not result.stdout:
            return []
        data = json.loads(result.stdout)
        disks = []
        for block in data.get('blockdevices', []):
            # Filter for removable devices (e.g., SD card, USB)
            if block.get('rm', False):
                disks.append({
                    'name': block.get('name'),
                    'size': block.get('size'),
                    'mountpoint': block.get('mountpoint', None)
                })
        return disks
    except Exception as e:
        print(f"Error listing external disks: {e}")
        return []

if __name__ == "__main__":
    disks = list_external_disks()
    print(disks)
