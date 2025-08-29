import subprocess, json

def get_disks_windows():
    ps_cmd = 'Get-WmiObject Win32_DiskDrive | Select-Object DeviceID, Model, InterfaceType, Size | ConvertTo-Json'
    result = subprocess.run(["powershell", "-Command", ps_cmd],
                            capture_output=True, text=True)
    if not result.stdout:
        return {}
    disks = json.loads(result.stdout)
    # Always work with a list
    if isinstance(disks, dict):
        disks = [disks]
    disk_info = {}
    for disk in disks:
        name = disk.get("Model", disk.get("DeviceID"))
        size_bytes = disk.get("Size", None)
        if size_bytes and str(size_bytes).isdigit():
            size_gb = int(size_bytes) / (1024 ** 3)
            size_str = f"{size_gb:.2f} GB"
        else:
            size_str = "Unknown Size"
        disk_info[name] = size_str
    return disk_info