# this file will be used to wipe the data from a particular data storage

import subprocess
import re

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
                print(clean_line) # for console debugging
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
        return

    def do_wipe_android(disk_identifier: str, state_callback=None):
        return