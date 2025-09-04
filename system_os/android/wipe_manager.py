# Implements wipe algorithms for Android external disks
import subprocess

def wipe_disk(disk_path, algorithm="zero_pass"):
    """
    Securely wipes the disk at disk_path using the specified algorithm via adb shell.
    Supported: 'zero_pass' (overwrite with zeroes)
    Returns True if successful, False otherwise.
    """
    try:
        if algorithm == "zero_pass":
            # Overwrite with zeroes using dd
            cmd = f"adb shell dd if=/dev/zero of={disk_path} bs=1M"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0
        # Add more algorithms as needed
        else:
            print(f"Algorithm '{algorithm}' not supported.")
            return False
    except Exception as e:
        print(f"Error wiping disk: {e}")
        return False
