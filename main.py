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
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,QPushButton, QComboBox, QLabel, QMessageBox, QDialog, QTextEdit, QDialogButtonBox, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtGui import QIcon, QFontDatabase, QMovie
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

# display_options = ["Select Drive to Proceed:"]
display_options = [f"{k} - {v}" for k, v in disk_info.items()]
# if not display_options:
#     display_options = ["No external drives detected"]

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
    # The message box is now shown from the PyQt UI thread
    # messagebox.showinfo("Report", "Report Downloaded Successfully.") # add if else here


# --- STYLESHEET for a modern look ---
STYLESHEET = """
    QWidget {
        background-color: #2E3440;
        color: #D8DEE9;
        font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        font-size: 11pt;
    }
    QLabel {
        color: #ECEFF4;
    }
    QLabel#TitleLabel {
        font-size: 18pt;
        font-weight: bold;
        color: #88C0D0;
    }
    QPushButton {
        background-color: #4C566A;
        color: #ECEFF4;
        border: 1px solid #434C5E;
        padding: 8px 16px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #5E81AC;
    }
    QPushButton:pressed {
        background-color: #81A1C1;
    }
    QPushButton:disabled {
        background-color: #3B4252;
        color: #4C566A;
    }
    QComboBox {
        background-color: #434C5E;
        color: #ECEFF4;
        border: 1px solid #4C566A;
        padding: 5px;
        border-radius: 4px;
    }
    QComboBox::drop-down {
        border: none;
    }
    QComboBox::down-arrow {
        image: url(down_arrow.png); /* A proper path or resource is needed */
    }
    QComboBox QAbstractItemView {
        background-color: #3B4252;
        selection-background-color: #5E81AC;
        color: #ECEFF4;
    }
    QTextEdit {
        background-color: #3B4252;
        color: #D8DEE9;
        border: 1px solid #4C566A;
        border-radius: 4px;
    }
    QDialog {
        background-color: #2E3440;
    }
    QMessageBox {
        background-color: #3B4252;
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
        global end_time

        def state_callback(state, line=None):
            if state == "wiping":
                self.state_changed.emit("wiping", f"Wiping {self.disk_id}...")
            elif state == "logging":
                self.log_updated.emit(line)
            elif state == "finalizing":
                self.state_changed.emit("finalizing", "Almost done, finalizing... This may take a while.")

        success, message = (False, "")
        try:
            if os_name == 'Linux':
                success, message = do_wipe.do_wipe_linux(self.disk_id, state_callback)
            elif os_name == 'Windows':
                success, message = do_wipe.do_wipe_windows(self.disk_id, state_callback)
            elif os_name == 'Darwin':
                success, message = do_wipe.do_wipe_darwin(self.disk_id, state_callback)
            else:
                success, message = do_wipe.do_wipe_android(self.disk_id, state_callback)
            
            end_time = datetime.datetime.now()

        finally:
            self.wipe_finished.emit(success, message, end_time)

class AdvancedWipeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Wipe Options")
        self.setModal(True)
        self.setMinimumWidth(350)
        
        self.selected_algorithm = "DoD 5220.22-M" # Default
        
        layout = QVBoxLayout(self)
        
        label = QLabel("Select Wipe Algorithm:")
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
        self.setMinimumSize(500, 350)

        # Main layout
        layout = QVBoxLayout(self)
        
        # Status layout
        status_layout = QHBoxLayout()
        self.spinner_label = QLabel()
        self.status_label = QLabel(f"Preparing to wipe {self.display_name}...")
        
        # self.spinner_animation = qta.Spin(self.spinner_label)
        # self.spinner_icon = qta.icon('fa5s.spinner', color='#5E81AC', animation=self.spinner_animation)
        # self.spinner_label.setPixmap(self.spinner_icon.pixmap(32, 32))

        # --- QMovie Spinner Implementation ---
        # NOTE: You must provide a 'spinner.gif' file in the same directory as the script.
        # This file should be an animated GIF for the loading indicator.
        self.movie = QMovie("spinner.gif")
        if not self.movie.isValid():
            print("Warning: 'spinner.gif' not found or is invalid. Spinner will not be shown.")
            # Fallback to a static character if GIF is missing
            self.spinner_label.setText("⏳")
        else:
            self.spinner_label.setMovie(self.movie)
            self.movie.setScaledSize(QSize(32, 32))
        
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
        self.report_button.setIcon(qta.icon('fa5s.download', color='#ECEFF4'))
        self.report_button.clicked.connect(self.download_report)
        layout.addWidget(self.report_button)
        
        self.start_wipe_process()

    def start_wipe_process(self):
        self.thread = QThread()
        self.worker = WipeWorker(self.disk_id)
        self.worker.moveToThread(self.thread)
        
        self.worker.state_changed.connect(self.update_status)
        self.worker.log_updated.connect(self.append_log)
        self.worker.wipe_finished.connect(self.on_wipe_finished)
        
        # Start the GIF animation
        if self.movie.isValid():
            self.movie.start()

        self.thread.started.connect(self.worker.run_wipe)
        self.thread.start()

    def update_status(self, state, message):
        self.status_label.setText(message)
        # The QMovie is started once, so we no longer need to start it on state change
        # if state == "wiping":
        #     self.spinner_animation.start()
        # no else block needed becasue insteda we just display another static icon instead
        # else: # finalizing or other states
        #     self.spinner_animation.stop() # Stop spinning but icon remains
    
    def append_log(self, line):
        self.log_box.append(line)
    
    def on_wipe_finished(self, success, message, end_time_obj):
        global start_time
        # --- FIX ---
        # The following line was the likely cause of an AttributeError.
        # The animation is stopped implicitly when the spinner icon is replaced
        # by a static icon (check or cross) below. Calling .stop() is redundant
        # and can cause an error. This logic follows your own comment in update_status.
        # self.spinner_animation.stop()
        
        # Stop the QMovie animation
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
            print("final wiped data", self.final_wipe_data)
        else:
            print("No data is Fetched!!")
            
        self.report_button.setEnabled(True)

        if success:
            self.status_label.setText(message)
            self.spinner_label.setPixmap(qta.icon('fa5s.check-circle', color='#A3BE8C').pixmap(32, 32))
        else:
            self.status_label.setText("Wipe Failed!")
            self.spinner_label.setPixmap(qta.icon('fa5s.times-circle', color='#BF616A').pixmap(32, 32))
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
        self.setWindowIcon(qta.icon('fa5s.shield-alt', color='#81A1C1'))
        self.setGeometry(100, 100, 450, 250)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title
        title_label = QLabel("Shudhhi Disk Wiper")
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # OS Label
        os_label = QLabel(f"Detected System: {os_name}")
        os_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        os_label.setStyleSheet("color: #8FBCBB;")
        main_layout.addWidget(os_label)
        
        main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Drive selection
        self.combo = QComboBox()
        if display_options:
            self.combo.addItems(display_options)
        else:
            self.combo.addItem("No external disks detected")
            self.combo.setEnabled(False)
        self.combo.currentIndexChanged.connect(self.on_select)
        main_layout.addWidget(self.combo)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        self.wipe_button = QPushButton("Wipe Now")
        self.wipe_button.setIcon(qta.icon('fa5s.play-circle', color='#ECEFF4'))
        self.wipe_button.clicked.connect(self.on_button_click)
        if not display_options:
            self.wipe_button.setEnabled(False)
            
        self.advanced_button = QPushButton("Advanced Options")
        self.advanced_button.setIcon(qta.icon('fa5s.cogs', color='#ECEFF4'))
        self.advanced_button.clicked.connect(self.on_click_advanced_options)
        
        buttons_layout.addWidget(self.wipe_button)
        buttons_layout.addWidget(self.advanced_button)
        main_layout.addLayout(buttons_layout)

        self.on_select(0) # Trigger initial selection info print

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
        msg_box.setWindowTitle("WARNING!!!")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(
            f"You are about to permanently ERASE all data on:\n\n"
            f"<b>{selected_display}</b>\n\n"
            f"This action cannot be undone!"
        )
        msg_box.setInformativeText("Are you sure you want to proceed?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Cancel)
        
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
    app.setStyleSheet(STYLESHEET)
    # The following line is for potential high-DPI scaling issues
    # app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    ex = ShudhhiApp()
    ex.show()
    sys.exit(app.exec())

