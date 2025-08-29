import subprocess

def get_disks_android():
    cmd = ["lsblk", "-o", "NAME,SIZE,TYPE,MOUNTPOINT"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout
