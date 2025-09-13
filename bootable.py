import sys
import subprocess
import os
import signal
import threading
import re
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                             QDialog, QLabel, QProgressBar, QMessageBox, QLineEdit)
from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtGui import QMovie

global iso_file 
iso_file = "ubuntu-24.04.3-2025.09.01-live-server-amd64.iso"

# --- Worker Object for Threading ---
class CreatorWorker(QObject):
    status_changed = pyqtSignal(str)
    writing_started = pyqtSignal(int)
    progress_updated = pyqtSignal(int)
    task_finished = pyqtSignal(bool, str)

    def __init__(self, disk_identifier, iso_file):
        super().__init__()
        self.disk_identifier = disk_identifier
        self.iso_file = iso_file

    @pyqtSlot()
    def run(self):
        try:
            # --- Part 1: Formatting ---
            self.status_changed.emit("Formatting disk...")
            cmd_format = ["diskutil", "eraseDisk", "FAT32", "BOOTABLE", "MBRFormat", self.disk_identifier]
            proc_format = subprocess.run(cmd_format, capture_output=True, text=True)
            if proc_format.returncode != 0:
                raise subprocess.CalledProcessError(proc_format.returncode, cmd_format, stderr=proc_format.stderr)
            self.status_changed.emit("Formatting successful.")

            # --- Part 2: Unmounting ---
            self.status_changed.emit("Unmounting disk...")
            cmd_unmount = ["diskutil", "unmountDisk", self.disk_identifier]
            proc_unmount = subprocess.run(cmd_unmount, capture_output=True, text=True)
            if proc_unmount.returncode != 0 and "disks appeared to be unmounted" not in proc_unmount.stderr:
                raise subprocess.CalledProcessError(proc_unmount.returncode, cmd_unmount, stderr=proc_unmount.stderr)
            self.status_changed.emit("Unmounting successful.")

            # --- Part 3: DD Write with Progress ---
            self.status_changed.emit("Writing ISO image...")
            raw_disk_identifier = "/dev/r" + self.disk_identifier.split('/')[-1]
            
            iso_size = os.path.getsize(self.iso_file)
            self.writing_started.emit(iso_size)

            # FIX: 'sudo' is REMOVED. The script itself is now run with sudo.
            cmd_dd = ["dd", f"if={self.iso_file}", f"of={raw_disk_identifier}","status=progress", "bs=1m"]
            
            # Start the dd process in the background
            process = subprocess.Popen(cmd_dd, stderr=subprocess.PIPE, text=True, bufsize=1)
            
            def send_signals():
                """Helper thread to send SIGINFO signals to dd for progress."""
                while process.poll() is None:
                    try:
                        os.kill(process.pid, signal.SIGINFO)
                    except ProcessLookupError: # Process finished between checks
                        break
                    threading.Event().wait(1)

            signal_thread = threading.Thread(target=send_signals, daemon=True)
            signal_thread.start()

            last_bytes = 0
            if process.stderr:
                for line in iter(process.stderr.readline, ''):
                    match = re.search(r"(\d+) bytes transferred", line)
                    if match:
                        current_bytes = int(match.group(1))
                        self.progress_updated.emit(current_bytes)
            
            process.wait()
            
            if process.returncode == 0:
                self.progress_updated.emit(iso_size)
                self.task_finished.emit(True, "Bootable USB created successfully!")
            else:
                raise Exception(f"dd process failed with exit code {process.returncode}.")

        except FileNotFoundError as e:
            self.task_finished.emit(False, f"Error: Command not found ({e.filename}).")
        except subprocess.CalledProcessError as e:
            self.task_finished.emit(False, f"A critical step failed:\n\n{e.stderr}")
        except Exception as e:
            self.task_finished.emit(False, f"An unexpected error occurred: {e}")

# --- PyQt6 UI Classes (Unchanged) ---
class ProgressDialog(QDialog):
    def __init__(self, disk_identifier, iso_file, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Creating Bootable USB")
        self.setFixedSize(400, 150)
        self.setModal(True)
        self.success = False

        self.layout = QVBoxLayout(self)
        self.status_label = QLabel("Starting process...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.spinner_label = QLabel()
        self.movie = QMovie("spinner.gif")
        if self.movie.isValid():
            self.spinner_label.setMovie(self.movie)
            self.movie.setScaledSize(QSize(40, 40))
            self.movie.start()
        else: self.spinner_label.setText("Loading...")
        self.spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.spinner_label)
        self.layout.addWidget(self.progress_bar)

        self.thread = QThread()
        self.worker = CreatorWorker(disk_identifier, iso_file)
        self.worker.moveToThread(self.thread)

        self.worker.status_changed.connect(self.on_status_changed)
        self.worker.writing_started.connect(self.on_writing_started)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.task_finished.connect(self.on_task_finished)

        self.thread.started.connect(self.worker.run)
        self.thread.start()

    @pyqtSlot(str)
    def on_status_changed(self, status):
        self.status_label.setText(status)

    @pyqtSlot(int)
    def on_writing_started(self, total_size):
        self.status_label.setText("Writing ISO image... Please wait.")
        self.spinner_label.setVisible(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(total_size)
        self.progress_bar.setValue(0)

    @pyqtSlot(int)
    def on_progress_updated(self, value):
        self.progress_bar.setValue(value)

    @pyqtSlot(bool, str)
    def on_task_finished(self, success, message):
        self.thread.quit(); self.thread.wait()
        self.success = success
        if success: QMessageBox.information(self, "Success", message)
        else: QMessageBox.critical(self, "Error", message)
        self.accept()

# --- Main function to be called from a larger app ---
def start_usb_creation_gui(disk_identifier: str):
    app = QApplication.instance() or QApplication(sys.argv)
    
    # FIX: Check for root/admin privileges at the start.
    # This is for macOS/Linux. For Windows, you'd check for an admin shell.
    if hasattr(os, 'geteuid') and os.geteuid() != 0:
        QMessageBox.critical(None, "Permissions Error", "This application must be run with administrator (sudo) privileges to write to a disk.")
        return False

    dialog = ProgressDialog(disk_identifier, iso_file)
    dialog.exec()
    return dialog.success
