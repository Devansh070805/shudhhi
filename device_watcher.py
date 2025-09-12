# device_watcher.py

import psutil
import time
import sys
import os
from PyQt6.QtCore import QThread, pyqtSignal

class DriveWatcher(QThread):
    drives_changed = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self._is_running = True

    def get_attached_drives(self):
        drives = set()
        system_platform = sys.platform

        for partition in psutil.disk_partitions(all=False):
            mountpoint = partition.mountpoint
            opts = partition.opts

            if system_platform == "darwin":
                if mountpoint.startswith("/Volumes/"):
                    drives.add(mountpoint)

            elif system_platform == "win32":
                system_drive = os.getenv("SystemDrive", "C:").upper()
                if not mountpoint.upper().startswith(system_drive):
                    drives.add(mountpoint)

            elif system_platform == "linux":
                is_removable = "removable" in opts
                is_media_mount = mountpoint.startswith(('/media/', '/run/media/'))
                
                is_system_fs = partition.fstype in ['squashfs', 'tmpfs']
                
                if (is_removable or is_media_mount) and not is_system_fs:
                    drives.add(mountpoint)

        return sorted(list(drives))

    def run(self):
        previous_drives = []

        while self._is_running:
            try:
                current_drives = self.get_attached_drives()
                
                if set(current_drives) != set(previous_drives):
                    print(f"Drive change detected! New list: {current_drives}")
                    previous_drives = current_drives
                    self.drives_changed.emit(current_drives)
            except Exception as e:
                print(f"Error in drive watcher loop: {e}")

            time.sleep(2)
    
    def stop(self):
        self._is_running = False
        print("Drive watcher stopped.")