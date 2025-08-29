import subprocess

def get_disks_darwin():
    cmd = ["diskutil", "list"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout   

