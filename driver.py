# this script is used to detect the mouted drives and storages

'''
since this is a cross-platform software and we need to access areas restricted by HPA/DCO, i am writing os specific scripts 
to get the information we need

'''
import platform
import json
import re
import subprocess
import datetime
import threading
import sys
import os
from system_os.linux.linux_disks import get_disks_linux
from system_os.windows.windows_disks import get_disks_windows
from system_os.darwin.darwin_disks import get_disks_darwin
from system_os.android.android_disks import get_disks_android
from wipe_disk import do_wipe
from generate_report.generate_report import ReportGenerator
from system_os.darwin.fetch_details_darwin import get_disk_info_darwin
from system_os.windows.fetch_details_windows import get_disk_info_windows
from system_os.linux.fetch_details_linux import get_disk_info_linux
try:
    from system_os.android.fetch_details_android import get_disk_info_android
except ImportError:
    def get_disk_info_android(disk_id):
        return {"mountpoint": disk_id}
from device_watcher import DriveWatcher

from bootable import start_usb_creation_gui
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,QPushButton, QComboBox, QLabel, QMessageBox, QDialog, QTextEdit, QDialogButtonBox, QSpacerItem, QSizePolicy, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal, pyqtSlot, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QFontDatabase, QMovie, QFont, QPixmap
import qtawesome as qta

# --- Global variables that will be updated ---
os_name = platform.system()
disk_info = {}
name_to_id = {}
name_to_details = {} # Added to support the new UI
display_options = []
print(f'Detected System: {os_name}')

def refresh_disk_info():
    """
    Scans the system for disks and updates the global variables.
    This function is called on startup and whenever a drive change is detected.
    """
    global disk_info, name_to_id, name_to_details, display_options
    
    print(f"Refreshing disk list for {os_name}...")

    if os_name == 'Linux':
        disk_info, name_to_id = get_disks_linux()
    elif os_name == 'Windows':
        disk_info, name_to_id = get_disks_windows()
    elif os_name == 'Darwin':
        disk_info, name_to_id = get_disks_darwin()
    # Android is not treated as an OS, but as an external device
    # To add Android devices, append them to disk_info and name_to_id separately
    try:
        from system_os.android.android_storage_detector import get_disks_android
        android_disks = get_disks_android()
    except ImportError:
        try:
            android_disks = get_disks_android()  # Use the imported version
        except:
            android_disks = []  # Fallback if neither works
    for idx, disk in enumerate(android_disks):
        label = f"Android Device {idx+1}: {disk['mountpoint']}"
        disk_info[label] = disk['mountpoint']
        name_to_id[label] = disk['mountpoint']
    
    # Create name_to_details for the new UI (this is a simplified implementation)
    name_to_details = {}
    for name, disk_id in name_to_id.items():
        # Create simplified details - you can enhance this with your fetch_details functions
        name_to_details[name] = {
            'model': name.split(' - ')[0] if ' - ' in name else name,
            'serial': f"Serial_{hash(disk_id) % 10000}",  # Placeholder
            'size': disk_info.get(name, 'Unknown'),
            'bus': 'USB' if 'USB' in name.upper() else 'SATA',
            'type': 'Android Device' if 'Android' in name else 'External Drive'
        }
    
    # Re-create the display options from the new disk_info
    display_options = [f"{k} - {v}" for k, v in disk_info.items()]
    print(f"Disk list refreshed. Found: {display_options}")

# --- Initial scan on startup ---
refresh_disk_info()

# this is the variable to hold the method selected by the user 
selectedWipeMethod = "DoD 5220.22-M"

'''
VARIABLES FOR THE REPORT GENERATOR 
'''

start_time = None
end_time = None
model = None
serialNumber = None
bus = None
method = None
status = None
size = None

def on_download_report(final_wipe_data):
    """
    This function is called when the button is clicked. It generates the report.
    """
    print("Generating report with the following data:")
    print(json.dumps(final_wipe_data, indent=2))
    report_gen = ReportGenerator(config_path="config.json")
    report_gen.generate_pdf(final_wipe_data)

# --- STYLESHEET - THE EPITOME OF MODERN DESIGN ---
STYLESHEET = """
    /* === FOUNDATION: Pure Elegance === */
    * {
        font-family: 'SF Pro Display', 'Inter', 'Segoe UI Variable', system-ui, -apple-system, sans-serif;
        font-optical-sizing: auto;
    }

    /* === MAIN CANVAS === */
    QWidget#MainWindow {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #fafbfc, stop:0.05 #ffffff, stop:1 #f8fafc);
        border: none;
    }

    /* === DIVINE HEADER === */
    #Header {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(255,255,255,0.95), stop:1 rgba(248,250,252,0.8));
        border: none;
        border-bottom: 1px solid rgba(226,232,240,0.6);
        backdrop-filter: blur(20px);
    }

    #BrandName {
        font-family: 'SF Pro Display', 'Inter', system-ui, sans-serif;
        font-size: 24pt;
        font-weight: 700;
        color: #1a202c;
        letter-spacing: -0.5px;
        text-rendering: optimizeLegibility;
    }

    #InfoLabel {
        font-family: 'SF Pro Text', 'Inter', system-ui, sans-serif;
        font-size: 11pt;
        font-weight: 500;
        color: #64748b;
        letter-spacing: 0.2px;
    }

    /* === CELESTIAL TYPOGRAPHY === */
    #PageTitle {
        font-family: 'SF Pro Display', 'Inter', system-ui, sans-serif;
        font-size: 32pt;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -1px;
        margin-bottom: 8px;
        text-rendering: optimizeLegibility;
    }

    #PageSubtitle {
        font-family: 'SF Pro Text', 'Inter', system-ui, sans-serif;
        font-size: 16pt;
        font-weight: 400;
        color: #64748b;
        letter-spacing: 0.1px;
        margin-bottom: 32px;
    }

    /* === DEVICE CARD: MASTERPIECE OF INTERACTION === */
    QPushButton#DeviceCard {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(255,255,255,0.9), stop:1 rgba(248,250,252,0.7));
        border: 1px solid rgba(226,232,240,0.5);
        border-radius: 16px;
        text-align: left;
        padding: 24px;
        min-height: 120px;
        margin: 4px;
        backdrop-filter: blur(10px);
        box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.1);
    }

    QPushButton#DeviceCard:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(255,255,255,0.95), stop:1 rgba(248,250,252,0.85));
        border: 1.5px solid rgba(59,130,246,0.3);
        box-shadow: 0 4px 12px rgba(59,130,246,0.1), 0 2px 4px rgba(0,0,0,0.05);
        transform: translateY(-1px);
    }

    QPushButton#DeviceCard:checked {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(239,246,255,0.95), stop:1 rgba(219,234,254,0.8));
        border: 2px solid rgba(59,130,246,0.6);
        box-shadow: 0 8px 24px rgba(59,130,246,0.15), 0 4px 8px rgba(0,0,0,0.05);
        transform: translateY(-2px);
    }

    /* === DEVICE CARD TYPOGRAPHY === */
    QLabel#DeviceName {
        font-family: 'SF Pro Display', 'Inter', system-ui, sans-serif;
        font-size: 18pt;
        font-weight: 700;
        color: #1e293b;
        letter-spacing: -0.3px;
        margin-bottom: 6px;
        text-rendering: optimizeLegibility;
    }

    QLabel#DeviceType {
        font-family: 'SF Pro Text', 'Inter', system-ui, sans-serif;
        font-size: 12pt;
        font-weight: 600;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }

    QLabel#DeviceDetails {
        font-family: 'SF Mono', 'Menlo', 'Monaco', 'Consolas', monospace;
        font-size: 11pt;
        font-weight: 500;
        color: #64748b;
        line-height: 1.4;
        letter-spacing: 0.1px;
    }

    QLabel#DeviceStatus {
        font-family: 'SF Pro Text', 'Inter', system-ui, sans-serif;
        font-size: 11pt;
        font-weight: 600;
        color: #059669;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(16,185,129,0.1), stop:1 rgba(5,150,105,0.08));
        border: 1px solid rgba(16,185,129,0.2);
        border-radius: 8px;
        padding: 6px 12px;
        margin: 4px 0px;
    }

    /* === MORE BUTTON: SUBTLE ELEGANCE === */
    QPushButton#MoreButton {
        font-family: 'SF Pro Text', 'Inter', system-ui, sans-serif;
        font-size: 11pt;
        font-weight: 500;
        color: #3b82f6;
        background: rgba(59,130,246,0.05);
        border: 1px solid rgba(59,130,246,0.15);
        border-radius: 8px;
        padding: 8px 16px;
        min-width: 80px;
    }

    QPushButton#MoreButton:hover {
        background: rgba(59,130,246,0.1);
        border: 1px solid rgba(59,130,246,0.25);
        color: #2563eb;
    }

    QPushButton#MoreButton:pressed {
        background: rgba(59,130,246,0.15);
        transform: translateY(1px);
    }

    /* === PRIMARY ACTION BUTTON: DIVINE POWER === */
    QPushButton#WipeButton {
        font-family: 'SF Pro Text', 'Inter', system-ui, sans-serif;
        font-size: 14pt;
        font-weight: 500;
        color: #ff0000;
        background: #000000;
        border: 2px solid rgba(225,0,0,0.6);
        border-radius: 10px;
        padding: 12px 24px;
        margin-right: 16px;
    }

    QPushButton#WipeButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #2563eb, stop:1 #1d4ed8);
        border: 3px solid rgba(225,0,0,0.6);
        transform: translateY(-1px);
    }

    QPushButton#WipeButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #1d4ed8, stop:1 #1e40af);
        transform: translateY(0px);
    }

    QPushButton#WipeButton:disabled {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #f1f5f9, stop:1 #e2e8f0);
        color: #94a3b8;
        border: 2px solid rgba(148, 163, 184,0.6);
        box-shadow: none;
        transform: none;
    }

    /* === ADVANCED OPTIONS: REFINED MINIMALISM === */
    QPushButton#AdvancedButton {
        font-family: 'SF Pro Text', 'Inter', system-ui, sans-serif;
        font-size: 14pt;
        font-weight: 500;
        color: #64748b;
        background: #000000;
        padding: 12px 24px;
        margin-right: 16px;
    }

    QPushButton#AdvancedButton:hover {
        color: #475569;
        background: rgba(241,245,249,0.9);
    }

    /* === BOOTABLE BUTTON: === */
    QPushButton#BootableButton {
        font-family: 'SF Pro Text', 'Inter', system-ui, sans-serif;
        font-size: 14pt;
        font-weight: 500;
        color: #2f9419;
        background: rgba(241,245,249,0.9);
        border: 2px solid rgba(47, 148, 25,0.6);
        border-radius: 10px;
        padding: 12px 24px;
        margin-right: 16px;
    }

    QPushButton#BootableButton:hover {
        color: #74e65c;
        background: rgba(241,245,249,0.9);
        border: 3px solid rgba(115, 230, 92,0.6);
    }
    QPushButton#BootableButton:disabled {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #f1f5f9, stop:1 #e2e8f0);
        color: #94a3b8;
        border: 2px solid rgba(148, 163, 184,0.6);
        box-shadow: none;
        transform: none;
    }

    /* === DETAILS DIALOG: FLOATING PERFECTION === */
    QDialog#DetailsDialog {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(255,255,255,0.95), stop:1 rgba(248,250,252,0.9));
        border: 1px solid rgba(226,232,240,0.6);
        border-radius: 20px;
        backdrop-filter: blur(40px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.1), 0 8px 16px rgba(0,0,0,0.05);
    }

    QLabel#DialogTitle {
        font-family: 'SF Pro Display', 'Inter', system-ui, sans-serif;
        font-size: 20pt;
        font-weight: 700;
        color: #1e293b;
        letter-spacing: -0.3px;
        margin-bottom: 16px;
    }

    QLabel#DialogContent {
        font-family: 'SF Pro Text', 'Inter', system-ui, sans-serif;
        font-size: 13pt;
        font-weight: 400;
        color: #475569;
        line-height: 1.6;
        letter-spacing: 0.1px;
    }

    /* === SCROLL AREA: INVISIBLE PERFECTION === */
    QScrollArea {
        border: none;
        background: transparent;
    }

    QScrollArea > QWidget > QWidget {
        background: transparent;
    }

    QScrollBar:vertical {
        background: rgba(241,245,249,0.5);
        width: 8px;
        border-radius: 4px;
        margin: 0px;
    }

    QScrollBar::handle:vertical {
        background: rgba(148,163,184,0.6);
        border-radius: 4px;
        min-height: 20px;
    }

    QScrollBar::handle:vertical:hover {
        background: rgba(100,116,139,0.8);
    }

    /* === GENERAL REFINEMENTS === */
    QPushButton {
        font-family: 'SF Pro Text', 'Inter', system-ui, sans-serif;
        font-size: 13pt;
        font-weight: 500;
        color: #475569;
        background: rgba(248,250,252,0.8);
        border: 1px solid rgba(226,232,240,0.6);
        border-radius: 10px;
        padding: 12px 20px;
    }

    QPushButton:hover {
        background: rgba(241,245,249,0.9);
        border: 1px solid rgba(203,213,225,0.8);
    }

    QPushButton:pressed {
        background: rgba(226,232,240,0.9);
        transform: translateY(1px);
    }

    QTextEdit {
        background: rgba(248,250,252,0.7);
        color: #475569;
        border: 1px solid rgba(226,232,240,0.5);
        border-radius: 12px;
        font-family: 'SF Mono', 'Menlo', 'Monaco', 'Consolas', monospace;
        font-size: 11pt;
        padding: 12px;
    }

    QMessageBox {
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(20px);
    }

    QMessageBox QLabel {
        color: #334155;
        font-family: 'SF Pro Text', 'Inter', system-ui, sans-serif;
        font-size: 13pt;
    }
"""

class WipeWorker(QObject):
    """
    Runs the wipe process in a separate thread to keep the UI responsive.
    """
    state_changed = pyqtSignal(str, str)  # state_name, message
    log_updated = pyqtSignal(str)
    wipe_finished = pyqtSignal(bool, str, object) # success, message, final_data

    def __init__(self, disk_id):
        super().__init__()
        self.disk_id = disk_id
        self.is_running = True

    @pyqtSlot()
    def run_wipe(self):
        def state_callback(state, **kwargs):
            if state == "wiping":
                self.state_changed.emit("wiping", kwargs.get("message", f"Wiping {self.disk_id}..."))
            elif state == "logging":
                self.log_updated.emit(kwargs.get("line", ""))
            elif state == "progress":
                msg = f"Pass {kwargs.get('current', '?')}/{kwargs.get('total', '?')}: {kwargs.get('message', '')}"
                self.state_changed.emit("progress", msg)

        success, message = (False, "")
        end_time_obj = None # Initialize to None for clarity
        try:
            '''
            HERE WE NEED TO IMPLEMENT THE DIFFERENT METHDOS ON THE BASIS OF THE SELECTED ALGORITHM
             algorithms = ["DoD 5220.22-M", "Gutmann", "Random Overwrite", "Single Pass Zero", "hdparm"]

             MAYBE CHANGE THIS TO MATCH CASE LATER AND THEN ADD SPECIAL CHECKS AND HANDLE ELSE BLOCKS
            '''
            # Check if this is an Android device
            if self.disk_id.startswith('/storage') or self.disk_id.startswith('/sdcard'):
                # Android device wipe
                success, message = do_wipe.do_wipe_android(self.disk_id, state_callback=state_callback)
            elif os_name == 'Linux':

                if selectedWipeMethod == "DoD 5220.22-M":
                    success, message = do_wipe.DoD_5220_22M.for_linux(self.disk_id, state_callback)

                if selectedWipeMethod == "Gutmann":
                    success, message = do_wipe.Gutmann.for_linux(self.disk_id, state_callback)

                if selectedWipeMethod == "Single Pass Zero":
                    success, message = do_wipe.FillZeros.for_linux(self.disk_id, state_callback)
                
                if selectedWipeMethod == "hdparm":
                    success, message = do_wipe.HDParm.for_linux(self.disk_id, state_callback)

            elif os_name == 'Windows':

                if selectedWipeMethod == "DoD 5220.22-M":
                    success, message = do_wipe.DoD_5220_22M.for_windows(self.disk_id, state_callback)

                if selectedWipeMethod == "Gutmann":
                    success, message = do_wipe.Gutmann.for_windows(self.disk_id, state_callback)

                if selectedWipeMethod == "Single Pass Zero":
                    success, message = do_wipe.FillZeros.for_windows(self.disk_id, state_callback)
                
                if selectedWipeMethod == "hdparm":
                    success, message = do_wipe.HDParm.for_windows(self.disk_id, state_callback)

            elif os_name == 'Darwin':

                if selectedWipeMethod == "DoD 5220.22-M":
                    success, message = do_wipe.DoD_5220_22M.for_darwin(self.disk_id, state_callback)

                if selectedWipeMethod == "Gutmann":
                    success, message = do_wipe.Gutmann.for_darwin(self.disk_id, state_callback)

                if selectedWipeMethod == "Single Pass Zero":
                    success, message = do_wipe.FillZeros.for_darwin(self.disk_id, state_callback)
                
                if selectedWipeMethod == "hdparm":
                    success, message = do_wipe.HDParm.for_darwin(self.disk_id, state_callback)

        finally:
            print(message)
            end_time_obj = datetime.datetime.now() 
            self.wipe_finished.emit(success, message, end_time_obj)


class AdvancedWipeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Wipe Options")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.selected_algorithm = "DoD 5220.22-M" # Default
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel("Select Wipe Algorithm:")
        label.setFont(QFont("Inter", 11))
        layout.addWidget(label)
        
        self.algo_combo = QComboBox()
        algorithms = ["DoD 5220.22-M", "Gutmann", "Single Pass Zero", "hdparm"]
        self.algo_combo.addItems(algorithms)
        layout.addWidget(self.algo_combo)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        global selectedWipeMethod
        self.selected_algorithm = self.algo_combo.currentText()
        selectedWipeMethod = self.selected_algorithm
        print(f"Selected wipe algorithm: {self.selected_algorithm}")
        
        super().accept()

class WipeProgressDialog(QDialog):
    def __init__(self, disk_id, display_name, fetched_data, parent=None):
        super().__init__(parent)
        self.disk_id = disk_id
        self.display_name = display_name
        self.final_wipe_data = None
        self.fetched_data = fetched_data
        
        self.setWindowTitle("Wipe in Progress")
        self.setModal(True)
        self.setMinimumSize(600, 450)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Status layout
        status_layout = QHBoxLayout()
        self.spinner_label = QLabel()
        self.status_label = QLabel(f"Preparing to wipe {self.display_name}...")
        self.status_label.setFont(QFont("Inter", 12))
        
        # --- QMovie Spinner Implementation ---
        self.movie = QMovie("spinner.gif")
        if not self.movie.isValid():
            print("Warning: 'spinner.gif' not found or is invalid. Spinner will not be shown.")
            self.spinner_label.setText("⏳")
        else:
            self.spinner_label.setMovie(self.movie)
            self.movie.setScaledSize(QSize(40, 40))
        
        status_layout.addWidget(self.spinner_label)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # Log box
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        layout.addWidget(self.log_box)
        
        # Report button
        self.report_button = QPushButton("Download Report")
        self.report_button.setEnabled(False)
        self.report_button.clicked.connect(self.download_report)

        layout.addWidget(self.report_button, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.start_wipe_process()

    def start_wipe_process(self):
        self.thread = QThread()
        self.worker = WipeWorker(self.disk_id)
        self.worker.moveToThread(self.thread)
        
        self.worker.state_changed.connect(self.update_status)
        self.worker.log_updated.connect(self.append_log)
        self.worker.wipe_finished.connect(self.on_wipe_finished)
        
        if self.movie.isValid():
            self.movie.start()

        self.thread.started.connect(self.worker.run_wipe)
        self.thread.start()

    def update_status(self, state, message):
        self.status_label.setText(message)
    
    def append_log(self, line):
        self.log_box.append(line)
    
    def on_wipe_finished(self, success, message, end_time_obj):
        global start_time
        if self.movie.isValid():
            self.movie.stop()

        self.thread.quit()
        self.thread.wait()

        self.final_wipe_data = {
            "disk_id": self.disk_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time_obj.isoformat(),
            "duration": str(end_time_obj - start_time),
            "status": "Success" if success else "Failed"
        }

        if self.fetched_data:
            self.final_wipe_data.update(self.fetched_data)
        else:
            print("No data is Fetched!!")
            
        self.report_button.setEnabled(True)

        if success:
            self.status_label.setText(message)
            success_icon = qta.icon('fa5s.check-circle', color='#48BB78') # Green
            self.spinner_label.setPixmap(success_icon.pixmap(40, 40))
        else:
            self.status_label.setText("Wipe Failed!")
            fail_icon = qta.icon('fa5s.times-circle', color='#F56565') # Red
            self.spinner_label.setPixmap(fail_icon.pixmap(40, 40))
            QMessageBox.critical(self, "Wipe Failed", message)

    def download_report(self):
        if self.final_wipe_data:
            on_download_report(self.final_wipe_data)
            QMessageBox.information(self, "Report", "Report Downloaded Successfully.")
            self.close()

# --- DEVICE CARD: THE EPITOME OF INTERACTIVE DESIGN ---
class DeviceCard(QPushButton):
    more_info_requested = pyqtSignal(dict)

    def __init__(self, device_name, device_details):
        super().__init__()
        self.setObjectName("DeviceCard")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(140)
        
        self.device_name = device_name
        self.device_details = device_details

        # === DIVINE LAYOUT ORCHESTRATION ===
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(24, 20, 24, 20)

        # === CELESTIAL HEADER ROW ===
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        
        # TRANSCENDENT ICON SYSTEM
        icon_container = QLabel()
        icon_container.setFixedSize(48, 48)
        icon_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # DIVINE ICON SELECTION BASED ON DEVICE NATURE
        device_type = self.device_details.get('type', '').lower()
        bus_type = self.device_details.get('bus', '').lower()
        
        if 'android' in device_type:
            icon = qta.icon('fa5s.mobile-alt', color='#1e293b', color_active='#3b82f6')
        elif 'usb' in bus_type or 'usb' in device_type:
            # Changed 'fa5s.usb' to 'fa5s.plug'
            icon = qta.icon('fa5s.plug', color='#1e293b', color_active='#3b82f6') 
        elif 'ssd' in device_type or 'nvme' in bus_type:
            icon = qta.icon('fa5s.microchip', color='#1e293b', color_active='#3b82f6')
        elif 'hdd' in device_type or 'hard' in device_type:
            icon = qta.icon('fa5s.hdd', color='#1e293b', color_active='#3b82f6')
        elif 'external' in device_type:
            icon = qta.icon('fa5s.external-link-alt', color='#1e293b', color_active='#3b82f6')
        else:
            icon = qta.icon('fa5s.database', color='#1e293b', color_active='#3b82f6')
            
        icon_container.setPixmap(icon.pixmap(QSize(44, 44)))
        
        # MAJESTIC TEXT CONTAINER
        text_container = QVBoxLayout()
        text_container.setSpacing(4)
        
        # DEVICE NAME: THE CROWN JEWEL
        name_label = QLabel(device_name)
        name_label.setObjectName("DeviceName")
        name_label.setWordWrap(False)
        
        # DEVICE TYPE: ELEGANT IDENTIFIER
        device_type_display = self.device_details.get('bus', 'Unknown').upper()
        type_label = QLabel(device_type_display)
        type_label.setObjectName("DeviceType")
        
        text_container.addWidget(name_label)
        text_container.addWidget(type_label)
        text_container.addStretch()
        
        header_layout.addWidget(icon_container)
        header_layout.addLayout(text_container, 1)
        header_layout.addStretch()

        # === ETHEREAL DETAILS SECTION ===
        details_layout = QVBoxLayout()
        details_layout.setSpacing(6)
        
        # REFINED TECHNICAL SPECIFICATIONS
        model_text = f"Model: {self.device_details.get('model', 'Unknown')}"
        serial_text = f"Serial: {self.device_details.get('serial', 'N/A')}"
        size_text = f"Size: {self.device_details.get('size', 'Unknown')}"
        
        details_combined = f"{model_text} • {serial_text} • {size_text}"
        details_label = QLabel(details_combined)
        details_label.setObjectName("DeviceDetails")
        details_label.setWordWrap(True)
        
        details_layout.addWidget(details_label)

        # === TRANSCENDENT FOOTER ===
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(12)
        
        # STATUS INDICATOR: LIVING BADGE OF HONOR
        status_text = self.device_details.get('type', 'External Drive')
        if 'android' in status_text.lower():
            status_text = "Connected"
        elif 'external' in status_text.lower():
            status_text = "External Drive"
        elif 'internal' in status_text.lower():
            status_text = "Internal Drive"
        else:
            status_text = "Ready"
            
        status_label = QLabel(status_text)
        status_label.setObjectName("DeviceStatus")
        
        # MORE BUTTON: GATEWAY TO ENLIGHTENMENT
        more_button = QPushButton("More Details")
        more_button.setObjectName("MoreButton")
        more_button.setCursor(Qt.CursorShape.PointingHandCursor)
        more_button.clicked.connect(self.show_more_info)
        
        footer_layout.addWidget(status_label)
        footer_layout.addStretch()
        footer_layout.addWidget(more_button)

        # === DIVINE ASSEMBLY ===
        main_layout.addLayout(header_layout)
        main_layout.addLayout(details_layout)
        main_layout.addLayout(footer_layout)

    def show_more_info(self):
        self.more_info_requested.emit(self.device_details)

# --- DETAILS DIALOG: FLOATING REVELATION ---
class DetailsDialog(QDialog):
    def __init__(self, device_name, device_details, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setObjectName("DetailsDialog")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(400, 300)
        self.setMaximumSize(500, 400)
        
        # === TRANSCENDENT ANIMATION ORCHESTRATION ===
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(300)
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # === DIVINE LAYOUT FOUNDATION ===
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(20)
        
        # === CELESTIAL HEADER ===
        header_layout = QHBoxLayout()
        
        # MAGNIFICENT DEVICE ICON
        icon_label = QLabel()
        icon_label.setFixedSize(56, 56)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        device_type = device_details.get('type', '').lower()
        bus_type = device_details.get('bus', '').lower()
        
        if 'android' in device_type:
            icon = qta.icon('fa5s.mobile-alt', color='#3b82f6')
        elif 'usb' in bus_type:
            # Changed 'fa5s.usb' to 'fa5s.plug'
            icon = qta.icon('fa5s.plug', color='#3b82f6') 
        elif 'ssd' in device_type or 'nvme' in bus_type:
            icon = qta.icon('fa5s.microchip', color='#3b82f6')
        elif 'hdd' in device_type:
            icon = qta.icon('fa5s.hdd', color='#3b82f6')
        else:
            icon = qta.icon('fa5s.database', color='#3b82f6')
            
        icon_label.setPixmap(icon.pixmap(QSize(48, 48)))
        
        # MAJESTIC TITLE
        title_layout = QVBoxLayout()
        title_label = QLabel(f"{device_name}")
        title_label.setObjectName("DialogTitle")
        title_label.setWordWrap(True)
        
        subtitle_label = QLabel("Device Information")
        subtitle_label.setObjectName("PageSubtitle")
        subtitle_label.setStyleSheet("font-size: 14pt; color: #64748b; margin-bottom: 0px;")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        
        header_layout.addWidget(icon_label)
        header_layout.addSpacing(16)
        header_layout.addLayout(title_layout, 1)
        
        # === ETHEREAL SEPARATOR ===
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(226,232,240,0), stop:0.5 rgba(226,232,240,0.8), stop:1 rgba(226,232,240,0));
                border: none;
                height: 1px;
                margin: 8px 0px;
            }
        """)
        
        # === ENLIGHTENING CONTENT ===
        content_scroll = QScrollArea()
        content_scroll.setFrameShape(QFrame.Shape.NoFrame)
        content_scroll.setWidgetResizable(True)
        content_scroll.setStyleSheet("QScrollArea { background: transparent; }")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(12)
        
        # TRANSCENDENT DETAILS PRESENTATION
        details_to_show = [
            ("Device Name", device_name),
            ("Model", device_details.get('model', 'Unknown')),
            ("Serial Number", device_details.get('serial', 'N/A')),
            ("Size", device_details.get('size', 'Unknown')),
            ("Bus Type", device_details.get('bus', 'Unknown')),
            ("Device Type", device_details.get('type', 'Unknown'))
        ]
        
        for label_text, value_text in details_to_show:
            detail_row = QHBoxLayout()
            
            label = QLabel(f"{label_text}:")
            label.setStyleSheet("""
                font-family: 'SF Pro Text', 'Inter', system-ui, sans-serif;
                font-size: 13pt;
                font-weight: 600;
                color: #374151;
                min-width: 120px;
            """)
            
            value = QLabel(str(value_text))
            value.setStyleSheet("""
                font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
                font-size: 12pt;
                font-weight: 500;
                color: #6b7280;
                background: rgba(243,244,246,0.5);
                border-radius: 6px;
                padding: 4px 8px;
            """)
            value.setWordWrap(True)
            
            detail_row.addWidget(label)
            detail_row.addWidget(value, 1)
            content_layout.addLayout(detail_row)
        
        content_scroll.setWidget(content_widget)
        
        # === DIVINE ASSEMBLY ===
        main_layout.addLayout(header_layout)
        main_layout.addWidget(separator)
        main_layout.addWidget(content_scroll, 1)
        
    def showEvent(self, event):
        # CELESTIAL ENTRANCE ANIMATION
        self.opacity_animation.start()
        super().showEvent(event)
        
    def mousePressEvent(self, event):
        # GRACEFUL DISMISSAL ON OUTSIDE CLICK
        if not self.rect().contains(event.pos()):
            self.close()
        super().mousePressEvent(event)

# --- The Main Application Window ---
class ShudhhiApp(QWidget):
    def __init__(self):
        super().__init__()
        self.device_cards = []
        self.selected_card = None
        self.no_devices_message_widget = None # <--- NEW: Keep track of the 'no devices' widget
        self.init_ui()
        self.setup_device_watcher()

    def init_ui(self):
        self.setObjectName("MainWindow")
        self.setWindowTitle("Shudhhi - Secure Disk Wiper")
        self.setMinimumSize(1200, 800)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        # === DIVINE MAIN ORCHESTRATION ===
        cosmic_layout = QVBoxLayout(self)
        cosmic_layout.setContentsMargins(0, 0, 0, 0)
        cosmic_layout.setSpacing(0)

        # === TRANSCENDENT HEADER REALM ===
        header_sanctuary = QWidget()
        header_sanctuary.setObjectName("Header")
        header_sanctuary.setFixedHeight(80)
        
        header_cosmos = QHBoxLayout(header_sanctuary)
        header_cosmos.setContentsMargins(32, 16, 32, 16)
        header_cosmos.setSpacing(20)

        # DIVINE LOGO MANIFESTATION
        logo_vessel = QLabel()
        logo_vessel.setFixedSize(48, 48)
        logo_vessel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo_essence = QPixmap("logo.png")
        if not logo_essence.isNull():
            logo_essence = logo_essence.scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_vessel.setPixmap(logo_essence)
        else:
            # FALLBACK DIVINE SYMBOL
            logo_icon = qta.icon('fa5s.shield-alt', color='#3b82f6')
            logo_vessel.setPixmap(logo_icon.pixmap(QSize(44, 44)))
        
        # CELESTIAL BRAND IDENTITY
        brand_essence = QLabel("Shudhhi")
        brand_essence.setObjectName("BrandName")
        
        # ETHEREAL SYSTEM INDICATOR
        system_beacon = QLabel(f"System: {os_name}")
        system_beacon.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        system_beacon.setObjectName("InfoLabel")

        # DIVINE ASSEMBLY OF HEADER
        header_cosmos.addWidget(logo_vessel)
        header_cosmos.addWidget(brand_essence)
        header_cosmos.addStretch()
        header_cosmos.addWidget(system_beacon)

        # === TRANSCENDENT CONTENT UNIVERSE ===
        content_sanctuary = QWidget()
        content_sanctuary.setStyleSheet("QWidget { background: transparent; }")
        
        content_cosmos = QVBoxLayout(content_sanctuary)
        content_cosmos.setContentsMargins(64, 48, 64, 48)
        content_cosmos.setSpacing(24)

        # CELESTIAL TITLE MANIFESTATION
        title_vessel = QLabel("Connected Devices")
        title_vessel.setObjectName("PageTitle")
        title_vessel.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        subtitle_essence = QLabel("Select a device to securely wipe its data")
        subtitle_essence.setObjectName("PageSubtitle")
        subtitle_essence.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        content_cosmos.addWidget(title_vessel)
        content_cosmos.addWidget(subtitle_essence)

        # === INFINITE SCROLL REALM FOR DEVICES ===
        scroll_universe = QScrollArea()
        scroll_universe.setWidgetResizable(True)
        scroll_universe.setFrameShape(QFrame.Shape.NoFrame)
        scroll_universe.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)
        
        self.device_cosmos = QWidget()
        self.device_cosmos.setStyleSheet("QWidget { background: transparent; }")
        
        self.device_constellation = QVBoxLayout(self.device_cosmos)
        self.device_constellation.setSpacing(16)
        self.device_constellation.setContentsMargins(8, 8, 8, 8)
        self.device_constellation.setAlignment(Qt.AlignmentFlag.AlignTop)

        # INITIAL DEVICE MANIFESTATION
        self.update_device_list()
        
        scroll_universe.setWidget(self.device_cosmos)
        content_cosmos.addWidget(scroll_universe, 1)

        # === DIVINE ACTION SANCTUARY ===
        action_realm = QWidget()
        action_realm.setFixedHeight(100)
        action_realm.setStyleSheet("QWidget { background: transparent; }")
        
        action_cosmos = QHBoxLayout(action_realm)
        action_cosmos.setContentsMargins(0, 24, 0, 24)
        action_cosmos.setSpacing(20)
        
        # ENLIGHTENED ADVANCED OPTIONS
        self.advanced_gateway = QPushButton("Advanced Options")
        self.advanced_gateway.setObjectName("AdvancedButton")
        self.advanced_gateway.clicked.connect(self.on_click_advanced_options)
        self.advanced_gateway.setCursor(Qt.CursorShape.PointingHandCursor)

        self.boot_button = QPushButton("Create Bootable Media")
        self.boot_button.setObjectName("BootableButton")
        self.boot_button.setEnabled(False)
        self.boot_button.clicked.connect(self.on_click_bootable)  # implement this handler if needed
        self.boot_button.setCursor(Qt.CursorShape.PointingHandCursor)

        
        # THE ULTIMATE WIPE BUTTON - APEX OF POWER
        self.wipe_divinity = QPushButton("Wipe Now")
        self.wipe_divinity.setObjectName("WipeButton")
        wipe_icon = qta.icon('fa5s.eraser', color='red')
        self.wipe_divinity.setIcon(wipe_icon)
        self.wipe_divinity.setIconSize(QSize(20, 20))
        self.wipe_divinity.setEnabled(False)
        self.wipe_divinity.clicked.connect(self.on_button_click)
        self.wipe_divinity.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # TRANSCENDENT ACTION ASSEMBLY
        action_cosmos.addWidget(self.advanced_gateway)
        action_cosmos.addStretch()
        action_cosmos.addStretch()
        action_cosmos.addWidget(self.boot_button)
        action_cosmos.addWidget(self.wipe_divinity)
        
        content_cosmos.addWidget(action_realm)

        # === FINAL COSMIC ASSEMBLY ===
        cosmic_layout.addWidget(header_sanctuary)
        cosmic_layout.addWidget(content_sanctuary, 1)

    def update_device_list(self):
        # PURGE PREVIOUS MANIFESTATIONS (device cards)
        for card in self.device_cards:
            card.setParent(None)
            card.deleteLater() # Ensure the widgets are properly cleaned up
        self.device_cards = []
        
        # <--- NEW: Remove existing 'no devices' message if it's there
        if self.no_devices_message_widget:
            self.no_devices_message_widget.setParent(None)
            self.no_devices_message_widget.deleteLater()
            self.no_devices_message_widget = None

        # MANIFEST NEW DEVICE CARDS OR SHOW ETHEREAL EMPTINESS
        if name_to_details:
            # Hide the 'no devices' message if it was previously visible
            if self.no_devices_message_widget:
                self.no_devices_message_widget.setParent(None)
                self.no_devices_message_widget.deleteLater()
                self.no_devices_message_widget = None

            for device_name, device_essence in name_to_details.items():
                # CREATE DIVINE DEVICE CARD
                card_manifestation = DeviceCard(device_name, device_essence)
                card_manifestation.clicked.connect(self.on_device_selected)
                card_manifestation.more_info_requested.connect(self.show_more_info_dialog)
                
                self.device_constellation.addWidget(card_manifestation)
                self.device_cards.append(card_manifestation)
        else:
            # MANIFEST EMPTINESS MESSAGE WITH CELESTIAL GRACE
            # <--- NEW: Only create and add the message if it doesn't already exist
            if not self.no_devices_message_widget:
                emptiness_vessel = QWidget()
                emptiness_cosmos = QVBoxLayout(emptiness_vessel)
                emptiness_cosmos.setAlignment(Qt.AlignmentFlag.AlignCenter)
                emptiness_cosmos.setSpacing(16)
                
                # DIVINE EMPTY STATE ICON
                empty_icon_label = QLabel()
                empty_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_icon = qta.icon('fa5s.inbox', color='#94a3b8')
                empty_icon_label.setPixmap(empty_icon.pixmap(QSize(64, 64)))
                
                # TRANSCENDENT EMPTY MESSAGE
                empty_message = QLabel("No devices detected")
                empty_message.setStyleSheet("""
                    font-family: 'SF Pro Display', 'Inter', system-ui, sans-serif;
                    font-size: 20pt;
                    font-weight: 600;
                    color: #64748b;
                    text-align: center;
                """)
                
                empty_subtitle = QLabel("Connect a storage device to begin secure wiping")
                empty_subtitle.setStyleSheet("""
                    font-family: 'SF Pro Text', 'Inter', system-ui, sans-serif;
                    font-size: 14pt;
                    color: #94a3b8;
                    text-align: center;
                """)
                
                emptiness_cosmos.addWidget(empty_icon_label)
                emptiness_cosmos.addWidget(empty_message)
                emptiness_cosmos.addWidget(empty_subtitle)
                
                self.device_constellation.addWidget(emptiness_vessel)
                self.no_devices_message_widget = emptiness_vessel # <--- NEW: Store reference
            
        # Ensure that if devices were removed, the layout is updated, and if the message appeared, it's at the top.
        # Adding a stretch to the end of the layout to push everything to the top.
        # This will clear any existing stretch items before adding a new one.
        for i in reversed(range(self.device_constellation.count())): 
            item = self.device_constellation.itemAt(i)
            if item and item.spacerItem():
                self.device_constellation.removeItem(item)
        self.device_constellation.addStretch(1) # Add stretch to push content to top

    def on_device_selected(self):
        divine_selection = self.sender()
        
        # CLEAR ALL OTHER SELECTIONS - ONLY ONE MAY RULE
        for card in self.device_cards:
            if card is not divine_selection:
                card.setChecked(False)

        if divine_selection.isChecked():
            self.selected_card = divine_selection
            self.wipe_divinity.setEnabled(True)
            self.boot_button.setEnabled(True)
            print(f"Selected: {self.selected_card.device_name}")
        else:
            self.selected_card = None
            self.wipe_divinity.setEnabled(False)
            self.boot_button.setEnabled(False)
            print("Selection cleared.")

    def show_more_info_dialog(self, device_essence):
        if self.selected_card:
            # MANIFEST ENLIGHTENING DIALOG
            revelation_dialog = DetailsDialog(self.selected_card.device_name, device_essence, self)
            
            # POSITION WITH DIVINE PRECISION
            cursor_position = self.cursor().pos()
            dialog_x = max(50, cursor_position.x() - 200)
            dialog_y = max(50, cursor_position.y() - 150)
            
            revelation_dialog.move(dialog_x, dialog_y)
            revelation_dialog.show()

    def on_click_advanced_options(self):
        dialog = AdvancedWipeDialog(self)
        dialog.exec()
    
    def on_click_bootable(self):
        print("device selected for boot", self.selected_card.device_name)
        selected_key = self.selected_card.device_name
        disk_id = name_to_id[selected_key]
        print(f"Starting USB creation process for {disk_id}...")
        was_successful = start_usb_creation_gui(disk_id)

        if was_successful:
            print("\nProcess finished: Success!")
        else:
            print("\nProcess finished: Failed or was cancelled.")

    # --- YOUR ORIGINAL LOGIC (ADAPTED) ---
    def on_button_click(self):
        if self.selected_card:
            selected_display = f"{self.selected_card.device_name} - {self.selected_card.device_details['size']}"
            self.show_warning(selected_display)
        else:
            QMessageBox.warning(self, "No Selection", "Please select a valid disk first!")

    def show_warning(self, selected_display):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Permanent Deletion")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(
            f"You are about to permanently erase all data on:\n\n"
            f"<b>{selected_display}</b>\n\n"
            f"This action cannot be undone."
        )
        msg_box.setInformativeText("Are you absolutely sure you want to proceed?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Cancel)
        
        yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
        yes_button.setText("Yes, Erase")
        yes_button.setStyleSheet("background-color: #E53E3E; color: white; border: none; padding: 8px 16px; border-radius: 6px;")

        reply = msg_box.exec()

        if reply == QMessageBox.StandardButton.Yes:
            self.proceed_with_wipe(selected_display)
            
    def proceed_with_wipe(self, selected_display):
        global start_time
        selected_key = self.selected_card.device_name
        disk_id = name_to_id[selected_key]
        start_time = datetime.datetime.now()
        print(f"User chose CONTINUE — wiping {disk_id}...")
        
        fetched_data = None
        if selected_display.startswith("Android Device"):
            # For Android, just show the mountpoint info
            fetched_data = {"mountpoint": disk_id}
        elif os_name == 'Linux':
            fetched_data = get_disk_info_linux(disk_id)
        elif os_name == 'Windows':
            fetched_data = get_disk_info_windows(disk_id)
        elif os_name == 'Darwin':
            fetched_data = get_disk_info_darwin(disk_id)
            print("fetched data:", fetched_data)
            
        progress_dialog = WipeProgressDialog(disk_id, selected_display, fetched_data, self)
        progress_dialog.exec()

    def setup_device_watcher(self):
        """Creates and starts the background thread for monitoring disk changes."""
        self.device_watcher = DriveWatcher()
        
        # Connect the signal from the watcher to our new handler slot
        self.device_watcher.drives_changed.connect(self.handle_drive_change)
        
        # Start the background thread
        self.device_watcher.start()

    @pyqtSlot(list)
    def handle_drive_change(self, detected_drives):
        """
        This slot is triggered when the DriveWatcher detects a change.
        It re-scans for disks and updates the UI with divine precision.
        """
        print("Signal received from watcher. Re-evaluating disk list.")
        
        # REFRESH THE COSMIC DISK KNOWLEDGE
        refresh_disk_info()
        
        # MANIFEST THE NEW DEVICE REALITY
        self.update_device_list()
        
        # RESET DIVINE SELECTION STATE
        self.selected_card = None
        self.wipe_divinity.setEnabled(False)

    def closeEvent(self, event):
        """Stops the watcher thread when the main window is closed."""
        print("Closing application, stopping drive watcher...")
        self.device_watcher.stop()
        self.device_watcher.wait() # Wait for the thread to finish
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Load custom font if available
    QFontDatabase.addApplicationFont("Inter-Regular.ttf") 
    app.setStyleSheet(STYLESHEET)
    ex = ShudhhiApp()
    ex.show()   
    sys.exit(app.exec())