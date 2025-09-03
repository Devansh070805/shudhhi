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
from system_os.linux.linux_disks import get_disks_linux
from system_os.windows.windows_disks import get_disks_windows
from system_os.darwin.darwin_disks import get_disks_darwin
from system_os.android.android_disks import get_disks_android
from wipe_disk import do_wipe
from generate_report.generate_report import ReportGenerator
from system_os.darwin.fetch_details_darwin import get_disk_info_darwin
from system_os.windows.fetch_details_windows import get_disk_info_windows
from system_os.linux.fetch_details_linux import get_disk_info_linux
from system_os.android.fetch_details_android import get_disk_info_android
import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,QPushButton, QComboBox, QLabel, QMessageBox, QDialog, QTextEdit, QDialogButtonBox, QSpacerItem, QSizePolicy, QFrame)
from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtGui import QIcon, QFontDatabase, QMovie, QFont, QPixmap
import qtawesome as qta


os_name = platform.system() # this is used to store the name of the operating system
print(f'Detected System: {os_name}')

if os_name == 'Linux':
    disk_info, name_to_id = get_disks_linux()
elif os_name == 'Windows':
    disk_info, name_to_id = get_disks_windows()
elif os_name == 'Darwin':
    disk_info, name_to_id  = get_disks_darwin()
else:
    disk_info, name_to_id = get_disks_android()

    # need to handle the else case

# REQUIREMENTS:
# disk_info -> {disk_name: disk_size}
# name_to_id -> {disk_name: disk_id}

display_options = [f"{k} - {v}" for k, v in disk_info.items()]

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


# --- STYLESHEET for a modern look ---
STYLESHEET = """
    * {
        font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
    }
    
    /* Main Window and Dialog Styling */
    QWidget, QDialog {
        background-color: #FFFFFF;
        color: #1A202C; /* Dark Gray for text */
    }

    /* Brand Name Label */
    QLabel#BrandName {
        font-size: 26pt;
        font-weight: 600; /* Semi-bold */
        color: #2D3748;
    }

    /* Main Action Title Label */
    QLabel#ActionTitle {
        font-size: 22pt;
        font-weight: 500; /* Medium */
        color: #2D3748;
        padding-top: 20px;
    }
    
    /* Subtitle/Informational Label */
    QLabel#InfoLabel {
        font-size: 12pt;
        color: #718096; /* Medium Gray */
        padding-bottom: 20px;
    }

    /* Primary Action Button (Wipe Now) */
    QPushButton#WipeButton {
        background-color: #4299E1; /* Bright Blue */
        color: #FFFFFF;
        font-size: 14pt;
        font-weight: bold;
        padding: 10px 36px;
        border-radius: 10px;
        border: none;
        min-width: 400px;
    }
    QPushButton#WipeButton:hover {
        background-color: #3182CE; /* Darker Blue */
    }
    QPushButton#WipeButton:pressed {
        background-color: #2B6CB0; /* Even Darker Blue */
    }
    QPushButton#WipeButton:disabled {
        background-color: #E2E8F0; /* Light Gray */
        color: #A0AEC0; /* Medium Gray */
    }

    /* Secondary Link-style Button (Advanced Options) */
    QPushButton#AdvancedButton {
        background-color: transparent;
        color: #4A5568; /* Dark Gray */
        font-size: 11pt;
        font-weight: 500;
        border: none;
        padding: 8px;
    }
    QPushButton#AdvancedButton:hover {
        color: #2B6CB0;
        text-decoration: underline;
    }
    QPushButton#AdvancedButton:pressed {
        color: #1A202C;
    }

    /* General Buttons (in dialogs) */
    QPushButton {
        background-color: #EDF2F7;
        color: #4A5568;
        font-size: 11pt;
        font-weight: 500;
        padding: 10px 20px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
    }
     QPushButton:hover {
        background-color: #E2E8F0;
        border-color: #CBD5E0;
    }
    QPushButton:pressed {
        background-color: #CBD5E0;
    }
    
    /* Dropdown Menu (ComboBox) */
    QComboBox {
        background-color: #FFFFFF;
        color: #2D3748;
        border: 1px solid #CBD5E0;
        padding: 15px;
        border-radius: 10px;
        font-size: 12pt;
    }
    QComboBox::drop-down {
        border: none;
        width: 25px;
        padding-right: 10px;
    }
    QComboBox::down-arrow {
        image: url(down_arrow_icon.png); /* You need to provide this icon */
    }
    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        selection-background-color: #EBF8FF;
        selection-color: #2D3748;
        border: 1px solid #E2E8F0;
        outline: 0px;
        padding: 5px;
        font-size: 11pt;
    }

    /* Log Box */
    QTextEdit {
        background-color: #F7FAFC; /* Very Light Gray */
        color: #4A5568;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 10pt;
    }

    /* Message Box Styling */
    QMessageBox {
        background-color: #FFFFFF;
    }
    QMessageBox QLabel {
        color: #2D3748;
        font-size: 11pt;
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
        def state_callback(state, line=None):
            if state == "wiping":
                self.state_changed.emit("wiping", f"Wiping {self.disk_id}...")
            elif state == "logging":
                self.log_updated.emit(line)
            elif state == "finalizing":
                self.state_changed.emit("finalizing", "Almost done, finalizing... This may take a while.")

        success, message = (False, "")
        end_time_obj = None # Initialize to None for clarity
        try:
            if os_name == 'Linux':
                success, message = do_wipe.do_wipe_linux(self.disk_id, state_callback)
            elif os_name == 'Windows':
                success, message = do_wipe.do_wipe_windows(self.disk_id, state_callback)
            elif os_name == 'Darwin':
                success, message = do_wipe.do_wipe_darwin(self.disk_id, state_callback)
            else:
                success, message = do_wipe.do_wipe_android(self.disk_id, state_callback)
        finally:
            # ✅ **FIX:** Set the end time HERE, so it always has a value.
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
        algorithms = ["DoD 5220.22-M", "Gutmann", "Random Overwrite", "Single Pass Zero"]
        self.algo_combo.addItems(algorithms)
        layout.addWidget(self.algo_combo)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        self.selected_algorithm = self.algo_combo.currentText()
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

class ShudhhiApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Shudhhi - Secure Disk Wiper")
        self.setMinimumSize(800, 600)
        
        # --- Header Section ---
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 15, 20, 15)

        logo_label = QLabel()
        logo_pixmap = QPixmap("logo.png")
        if not logo_pixmap.isNull():
            logo_pixmap = logo_pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        
        brand_label = QLabel("Shudhhi")
        brand_label.setObjectName("BrandName")

        os_label = QLabel(f"System: {os_name}")
        os_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        os_label.setObjectName("InfoLabel")

        header_layout.addWidget(logo_label)
        header_layout.addWidget(brand_label)
        header_layout.addStretch()
        header_layout.addWidget(os_label)

        # --- Main Content Section ---
        main_content_widget = QWidget()
        main_content_layout = QVBoxLayout(main_content_widget)
        main_content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_content_layout.setContentsMargins(80, 20, 80, 50)
        main_content_layout.setSpacing(15)

        action_title = QLabel("Securely Erase Your Drive")
        action_title.setObjectName("ActionTitle")
        action_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info_label = QLabel("Select a drive from the list below to permanently wipe all its data. This action is irreversible.")
        info_label.setObjectName("InfoLabel")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        
        self.combo = QComboBox()
        self.combo.setMinimumHeight(50)
        if display_options:
            self.combo.addItems(display_options)
        else:
            self.combo.addItem("No external disks detected")
            self.combo.setEnabled(False)
        self.combo.currentIndexChanged.connect(self.on_select)
        
        main_content_layout.addWidget(action_title)
        main_content_layout.addWidget(info_label)
        main_content_layout.addWidget(self.combo)
        main_content_layout.addStretch(1)

        # --- Footer/Actions Section ---
        self.wipe_button = QPushButton("Wipe Now")
        self.wipe_button.setObjectName("WipeButton")
        self.wipe_button.setIcon(qta.icon('fa5s.eraser', color='white'))
        self.wipe_button.setIconSize(QSize(22, 22))
        self.wipe_button.clicked.connect(self.on_button_click)
        if not display_options:
            self.wipe_button.setEnabled(False)

        self.advanced_button = QPushButton("Advanced Options")
        self.advanced_button.setObjectName("AdvancedButton")
        self.advanced_button.clicked.connect(self.on_click_advanced_options)

        main_content_layout.addWidget(self.wipe_button, 0, Qt.AlignmentFlag.AlignCenter)
        main_content_layout.addWidget(self.advanced_button, 0, Qt.AlignmentFlag.AlignCenter)
        main_content_layout.addStretch(2)


        # --- Final Assembly ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #E2E8F0;")

        main_layout.addWidget(header_widget)
        main_layout.addWidget(line)
        main_layout.addWidget(main_content_widget, 1)

        self.on_select(0)

    def on_select(self, index):
        selected_display = self.combo.currentText()
        if " - " in selected_display:
            selected_key = selected_display.split(" - ")[0]
            selected_info = disk_info[selected_key]
            print(f"You selected: {selected_key} - {selected_info}")

    def on_click_advanced_options(self):
        dialog = AdvancedWipeDialog(self)
        dialog.exec()

    def on_button_click(self):
        selected_disk = self.combo.currentText()
        if selected_disk and " - " in selected_disk:
            self.show_warning(selected_disk)
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
        global start_time, fetched_data
        selected_key = selected_display.split(" - ")[0]
        disk_id = name_to_id[selected_key]
        start_time = datetime.datetime.now()
        print(f"User chose CONTINUE — wiping {disk_id}...")
        
        fetched_data = None
        if os_name == 'Linux':
            fetched_data = get_disk_info_linux(disk_id)
        elif os_name == 'Windows':
            fetched_data = get_disk_info_windows(disk_id)
        elif os_name == 'Darwin':
            fetched_data = get_disk_info_darwin(disk_id)
            print("fetched data:", fetched_data)
        else:
            fetched_data = get_disk_info_android(disk_id)
            
        progress_dialog = WipeProgressDialog(disk_id, selected_display, fetched_data, self)
        progress_dialog.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QFontDatabase.addApplicationFont("Inter-Regular.ttf") 
    app.setStyleSheet(STYLESHEET)
    ex = ShudhhiApp()
    ex.show()   
    sys.exit(app.exec())