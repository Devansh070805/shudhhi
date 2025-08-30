import subprocess, json

def get_disks_windows():
    ps_cmd = 'Get-Disk | Select-Object Number, FriendlyName, Size | ConvertTo-Json'
    result = subprocess.run(["powershell", "-Command", ps_cmd],
                            capture_output=True, text=True)
    return json.loads(result.stdout)
