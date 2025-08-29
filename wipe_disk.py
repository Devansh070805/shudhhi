# this file will be used to wipe the data from a particular data storage

import subprocess

class do_wipe:
    def do_wipe_darwin(disk_identifier : str):
        try:
            subprocess.run(["diskutil", "unmountDisk", disk_identifier], check=True)
            cmd = ["diskutil", "secureErase", "0", disk_identifier]
            subprocess.run(cmd, check=True)
            print(f"Successfully wiped {disk_identifier}")

        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e}") 


            