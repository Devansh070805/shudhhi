import subprocess

def get_disks_darwin():
    cmd = ["diskutil", "list"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    disks = result.stdout
    disk_info = {} # this is the FINAL dictionary that will store the name of the devices -> {'device_name' : 'device_size'}
    disk_name = '' # jsut a temporary variable to store the name of the disks
    
    print(disks)
    
    name_to_id = {} # dictionary to map the selected name to its disk_id
    
    # function to get the manufacturers name to make it easier for the user
    def replace_with_name(disk_id):
         name =  subprocess.getoutput(f"diskutil info {disk_id} | grep 'Device / Media Name'").split(":")[-1].strip()
         name_to_id[name] = "/dev/" + disk_id
         return name
    
    # a dictionary to story data of format -> disk_name: storage
    for line in disks.split("\n"):
        # for Darwin
        if '*' in line:
            if disk_name == '':
                continue
            sp = line.split()
            size = sp[2][1:] + " " +  sp[3]
            disk_info[replace_with_name(disk_name)] = size
            disk_name = ''
            
        if line.startswith("/dev/") and line.endswith("(external, physical):"): # extracting only the physical devices and not their partitions
            disk_name = line.split()[0][5:] # this extracts the name of the disk 
            '''
            on analyzing the outptu format we can see that the storage capacity
            of physical devices is marked with '*', so we can write a simple logic for that
            coudl also arguably use the 'identifier' name is above '*' logic to simply fetch the name check once later.
            NOTE -> FOR KNOW I AM ONLY ALLOWING EXTERNAL DRIVES TO SHOW UP FOR WIPING TO PREVENT ANY MISTAKE
            WRITE LOGIC TO HANDLE NO EXTERNAL DEVICES CONNECTED
            '''
        
    print(disk_info)
    print(name_to_id)

    return disk_info, name_to_id
    
