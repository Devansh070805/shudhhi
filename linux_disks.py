import subprocess, json

def get_disks_linux():
    cmd = ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MOUNTPOINT"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)
