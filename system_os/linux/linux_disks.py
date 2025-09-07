import subprocess
import json

def get_disks_linux():
    """
    Gets a list of all external physical disk devices on Linux.
    This version is more robust as it checks the transport type (e.g., 'usb')
    in addition to the 'removable' flag.
    
    Returns two dictionaries in the required format:
    1. disk_info: {friendly_name: human_readable_size}
    2. name_to_id: {friendly_name: device_path_to_wipe}
    """
    disk_info = {}
    name_to_id = {}
    # NOTE: A third dictionary for details might be needed by your main app.
    # name_to_details = {} 

    try:
        # --- FIX: Added 'TRAN' (transport type) to the output columns ---
        cmd = ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MODEL,RM,TRAN"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        for device in data.get("blockdevices", []):
            # First, ensure it's a whole physical disk, not a partition.
            if device.get("type") == "disk":
                
                # --- FIX: The core logic change is here ---
                # A drive is considered external if it's either flagged as removable (like a thumb drive)
                # OR if its connection type is USB (like most external HDDs).
                is_removable = device.get("rm", False) # Default to False if key is missing
                transport_type = device.get("tran", "").lower() # Default to empty string

                if is_removable or transport_type == "usb":
                    
                    path_to_wipe = f"/dev/{device['name']}"
                
                    friendly_name = device.get("model", "Unknown External Device")
                    size = device.get("size", "Unknown Size")

                    if not friendly_name or friendly_name.isspace():
                        friendly_name = f"External Disk ({device['name']})"

                    # Handle potential duplicate friendly names to ensure unique keys
                    original_friendly_name = friendly_name
                    counter = 2
                    while friendly_name in disk_info:
                        friendly_name = f"{original_friendly_name} ({counter})"
                        counter += 1

                    disk_info[friendly_name] = size
                    name_to_id[friendly_name] = path_to_wipe
                    # You would also populate name_to_details here if your main app needs it.

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Could not execute 'lsblk'. Is it installed and in your PATH?")
    except json.JSONDecodeError:
        print("Error: Failed to parse JSON output from lsblk.")
    except Exception as e:
        print(f"An unexpected error occurred in get_disks_linux: {e}")

    # For compatibility with your main script which might expect three return values
    # return disk_info, name_to_id, name_to_details
    return disk_info, name_to_id
