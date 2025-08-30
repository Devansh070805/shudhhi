import subprocess
import json

def get_disks_windows():

    disk_info = {}
    name_to_id = {}

    try:
        ps_cmd = (
            'Get-CimInstance Win32_DiskDrive | '
            'Where-Object { $_.InterfaceType -eq "USB" -or $_.MediaType -eq "Removable Media" } | '
            'Select-Object DeviceID, Model, Size | '
            'ConvertTo-Json -Compress' 
        )
        
        result = subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True, text=True, check=True
        )

        if not result.stdout.strip():
            return {}, {}

        data = json.loads(result.stdout)
        
        if isinstance(data, dict):
            data = [data]

        for device in data:
            path_to_wipe = device.get("DeviceID")
            friendly_name = device.get("Model", "Unknown Removable Device")
            
            try:
                size_bytes = int(float(device.get("Size", 0)))
            except (TypeError, ValueError):
                size_bytes = 0

            if size_bytes > 0:
                size_gb = size_bytes / (1024 ** 3)
                size = f"{size_gb:.2f} GB"
            else:
                size = "Unknown Size"

            if not friendly_name or friendly_name.isspace():
                friendly_name = f"Removable Disk ({path_to_wipe})"

            original_friendly_name = friendly_name
            counter = 2
            while friendly_name in disk_info:
                friendly_name = f"{original_friendly_name} ({counter})"
                counter += 1

            disk_info[friendly_name] = size
            name_to_id[friendly_name] = path_to_wipe
            
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: PowerShell command failed. Ensure PowerShell is in PATH and the script is run as Administrator.")
    except json.JSONDecodeError:
        print("Error: Failed to parse JSON from PowerShell.")
    except Exception as e:
        print(f"An unexpected error occurred in get_disks_windows: {e}")
        
    return disk_info, name_to_id