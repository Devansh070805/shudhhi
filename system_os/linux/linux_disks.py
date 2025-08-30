import subprocess
import json

def get_disks_linux():

    disk_info = {}
    name_to_id = {}

    try:
        cmd = ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MODEL"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        for device in data.get("blockdevices", []):
            if device.get("type") == "disk":
                path_to_wipe = f"/dev/{device['name']}"
                
                friendly_name = device.get("model", "Unknown Device")
                size = device.get("size", "Unknown Size")

                if not friendly_name or friendly_name.isspace():
                    friendly_name = f"Disk ({device['name']})"

                original_friendly_name = friendly_name
                counter = 2
                while friendly_name in disk_info:
                    friendly_name = f"{original_friendly_name} ({counter})"
                    counter += 1

                disk_info[friendly_name] = size
                name_to_id[friendly_name] = path_to_wipe

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Could not execute 'lsblk'. Is it installed and in your PATH?")
    except json.JSONDecodeError:
        print("Error: Failed to parse JSON output from lsblk.")
    except Exception as e:
        print(f"An unexpected error occurred in get_disks_linux: {e}")

    return disk_info, name_to_id

