import subprocess

def get_disks_darwin():
    cmd = ["diskutil", "list"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout   


# New function to get external disks info and name-to-id mapping for Darwin/macOS
def get_external_disks_darwin():
    disk_info = {}
    name_to_id = {}
    disk_name = ''
    disks = get_disks_darwin()
    for line in disks.split("\n"):
        if line.startswith("/dev/") and line.endswith("(external, physical):"):
            disk_name = line.split()[0][5:]
        if '*' in line:
            if disk_name == '':
                continue
            sp = line.split()
            size = sp[2][1:] + " " +  sp[3]
            # Get device/media name
            name = subprocess.getoutput(f"diskutil info {disk_name} | grep 'Device / Media Name'").split(":")[-1].strip()
            disk_info[name] = size
            name_to_id[name] = "/dev/" + disk_name
            disk_name = ''
    return disk_info, name_to_id

