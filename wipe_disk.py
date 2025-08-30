# this file will be used to wipe the data from a particular data storage

import subprocess
import re
import os

class do_wipe:
    def do_wipe_darwin(disk_identifier: str, state_callback=None):
        try:
            subprocess.run(["diskutil", "unmountDisk", disk_identifier], check=True, capture_output=True)
            cmd = ["diskutil", "secureErase", "0", disk_identifier]
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True, 
                bufsize=1 
            )

            if state_callback:
                state_callback("wiping")

            for line in iter(process.stdout.readline, ''):
                clean_line = line.strip()
                print(clean_line) 
                if state_callback:
                    state_callback("logging", line=clean_line)

            process.stdout.close()

            if state_callback:
                state_callback("finalizing")

            WIPE_TIMEOUT_SECONDS = 86400 # 24 hours
            return_code = process.wait(timeout=WIPE_TIMEOUT_SECONDS)

            if return_code != 0:
                raise subprocess.CalledProcessError(return_code, process.args)

            print(f"Successfully wiped device.")
            return True, "Wipe completed successfully!"

        except subprocess.TimeoutExpired:
            print("Wipe process timed out and is likely stuck.")
            process.kill()
            return False, "The wipe process became unresponsive and was terminated. Please reboot."
            
        except subprocess.CalledProcessError as e:
            error_message = f"Process failed with return code {e.returncode}."
            print(f"Command failed: {e}\nError: {error_message}")
            return False, error_message
        except Exception as e:
            return False, str(e)
        

    def do_wipe_windows(disk_identifier: str, state_callback=None):
        return



    def do_wipe_linux(disk_identifier: str, state_callback=None):
        try:
            print(disk_identifier)
            base_disk = os.path.basename(disk_identifier)
            partitions_cmd = f"lsblk -ln -o NAME,MOUNTPOINT {base_disk}"
            mounted_partitions = subprocess.getoutput(partitions_cmd).splitlines()

            for line in mounted_partitions:
                parts = line.split()
                if len(parts) > 1 and not parts[1].startswith("["): 
                    partition = f"/dev/{parts[0]}"
                    print(f"Attempting to unmount {partition}...")
                    subprocess.run(["umount", partition], check=False, capture_output=True)

            cmd = ["dd", "if=/dev/zero", f"of={disk_identifier}", "bs=1M", "status=progress", "oflag=direct"]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            if state_callback:
                state_callback("wiping")

            logs = []
            for line in iter(process.stdout.readline, ''):
                clean_line = line.strip()
                if clean_line:
                    logs.append(clean_line)
                    print(clean_line)
                    if state_callback:
                        state_callback("logging", line=clean_line)

            process.stdout.close()

            if state_callback:
                state_callback("finalizing")

            WIPE_TIMEOUT_SECONDS = 86400
            return_code = process.wait(timeout=WIPE_TIMEOUT_SECONDS)

            if return_code != 0:
                raise subprocess.CalledProcessError(return_code, process.args, output="\n".join(logs))

            print(f"Successfully wiped device {disk_identifier}.")
            return True, f"Wipe of {disk_identifier} completed successfully!"

        except subprocess.TimeoutExpired:
            print("Wipe process timed out and is likely stuck.")
            process.kill()
            return False, "The wipe process became unresponsive and was terminated. Please reboot."

        except subprocess.CalledProcessError as e:
            
            # this is addedd to treat error status 1 as complted
            if e.output and "No space left on device" in e.output:
                print("dd finished with expected 'No space left' message. This is a successful wipe.")
                return True, f"Wipe of {disk_identifier} completed successfully!"
     
            if "Permission denied" in str(e.output):
                error_message = "Permission denied. Please run this application with 'sudo'."
            else:
                error_message = f"Process failed with return code {e.returncode}."
            
            print(f"Command failed: {e}\nError: {error_message}")
            return False, error_message

        except Exception as e:
            return False, str(e)


    def do_wipe_android(disk_identifier: str, state_callback=None):
        return