# this file will be used to wipe the data from a particular data storage

import subprocess
import re
import os
import tempfile

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
        script_path = None 
        try:
            try:
                ps_cmd = f'(Get-Partition -DriveLetter (Get-Volume -FilePath "{os.getenv("SystemDrive")}\\").DriveLetter).DiskNumber'
                os_disk_number = subprocess.check_output(["powershell", "-Command", ps_cmd], text=True).strip()
                target_disk_number = ''.join(filter(str.isdigit, disk_identifier))
                
                print(f"Safety Check: Detected OS disk is Number {os_disk_number}")
                
                if target_disk_number == os_disk_number:
                    return False, f"SAFETY_ERROR: Refusing to wipe the active OS disk (Disk {os_disk_number})."
            except Exception as e:
                return False, f"CRITICAL_ERROR: The OS disk safety check failed: {e}. Aborting wipe."

            disk_number = ''.join(filter(str.isdigit, disk_identifier))
            script_content = f"select disk {disk_number}\nclean all"
            
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding='utf-8') as f:
                script_path = f.name
                f.write(script_content)
            
            print(f"Temporary diskpart script created at: {script_path}")

            cmd = ["diskpart", "/s", script_path]
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

            WIPE_TIMEOUT_SECONDS = 86400 # 24 hours
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
            error_output = str(e.output)
            if "Access is denied" in error_output or "requires elevation" in error_output:
                error_message = "Access denied. Please run this application as Administrator."
            else:
                error_message = f"Process failed with return code {e.returncode}."
            
            print(f"Command failed: {e}\nError: {error_message}")
            return False, error_message

        except Exception as e:
            return False, str(e)
            
        finally:
            if script_path and os.path.exists(script_path):
                print(f"Cleaning up temporary script: {script_path}")
                os.remove(script_path)



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