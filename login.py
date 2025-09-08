import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QCheckBox, QFrame, QStackedWidget, QMessageBox, QTextEdit, # QFrame is already imported
    QGridLayout,QSizePolicy, QVBoxLayout
)
from PyQt6.QtGui import QFont, QCursor
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
# --- Imports for Video Playback ---
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

# Import our Firebase handler
from firebase_auth import FirebaseAuthHandler

class LoginPanel(QWidget):
    show_signup_requested = pyqtSignal()
    login_successful = pyqtSignal(dict) 

    def __init__(self, auth_handler: FirebaseAuthHandler):
        super().__init__()
        self.setObjectName("rightPanel")
        self.auth_handler = auth_handler
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(80, 60, 80, 60)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_container = QWidget()
        form_container.setMaximumWidth(400)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(15)
        title_label = QLabel("Sign In")
        title_label.setObjectName("titleLabel")
        subtitle_label = QLabel("Don't have an account? <a href='#'>Sign up</a>")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.linkActivated.connect(self.show_signup_requested.emit)
        form_layout.addWidget(title_label)
        form_layout.addWidget(subtitle_label)
        form_layout.addSpacing(20)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.password_input)
        form_layout.addSpacing(10)
        login_button = QPushButton("Sign In")
        login_button.setObjectName("createAccountButton")
        login_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        login_button.clicked.connect(self.handle_login)
        form_layout.addWidget(login_button)
        layout.addWidget(form_container)

    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        if not email or not password:
            self.show_error_message("Validation Error", "Please enter both email and password.")
            return
        try:
            user = self.auth_handler.sign_in(email, password)
            print("Login attempt successful!")
            self.login_successful.emit(user) 
        except Exception as e:
            self.show_error_message("Login Failed", str(e))
    
    def show_error_message(self, title, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(message)
        msg_box.setWindowTitle(title)
        msg_box.exec()

class SignUpPanel(QWidget):
    show_login_requested = pyqtSignal()
    signup_successful = pyqtSignal()

    def __init__(self, auth_handler: FirebaseAuthHandler):
        super().__init__()
        self.setObjectName("rightPanel")
        self.auth_handler = auth_handler
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(80, 60, 80, 60)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_container = QWidget()
        form_container.setMaximumWidth(400)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(15)
        title_label = QLabel("Create an account")
        title_label.setObjectName("titleLabel")
        subtitle_label = QLabel("Already have an account? <a href='#'>Log in</a>")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.linkActivated.connect(self.show_login_requested.emit)
        form_layout.addWidget(title_label)
        form_layout.addWidget(subtitle_label)
        form_layout.addSpacing(20)
        name_layout = QHBoxLayout()
        name_layout.setSpacing(15)
        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("First Name")
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Last Name")
        name_layout.addWidget(self.first_name_input)
        name_layout.addWidget(self.last_name_input)
        form_layout.addLayout(name_layout)
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Address")
        form_layout.addWidget(self.address_input)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.password_input)
        self.terms_checkbox = QCheckBox("I agree to the Terms & Conditions")
        form_layout.addWidget(self.terms_checkbox)
        form_layout.addSpacing(10)
        create_account_button = QPushButton("Create account")
        create_account_button.setObjectName("createAccountButton")
        create_account_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        create_account_button.clicked.connect(self.handle_signup)
        form_layout.addWidget(create_account_button)
        layout.addWidget(form_container)

    def handle_signup(self):
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        address = self.address_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        if not self.terms_checkbox.isChecked():
            self.show_error_message("Terms Error", "You must agree to the Terms & Conditions.")
            return
        if not all([email, password, first_name, last_name, address]):
            self.show_error_message("Validation Error", "Please fill in all fields.")
            return
        try:
            self.auth_handler.create_account(email, password, first_name, last_name, address)
            self.show_success_message("Account Created", "Your account has been successfully created! Please log in.")
            self.signup_successful.emit()
        except Exception as e:
            self.show_error_message("Signup Failed", str(e))
    
    def show_error_message(self, title, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(message)
        msg_box.setWindowTitle(title)
        msg_box.exec()

    def show_success_message(self, title, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setText(message)
        msg_box.setWindowTitle(title)
        msg_box.exec()

class AuthWindow(QWidget):
    login_successful = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Create an Account")
        self.setFixedSize(960, 600)
        self.firebase_auth = FirebaseAuthHandler()
        
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput() 
        self.media_player.setAudioOutput(self.audio_output)
        
        self.media_player.errorOccurred.connect(self.media_player_error)
        
        self.init_ui()
        self.apply_stylesheet()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Left Panel ---
        left_panel = QWidget()
        left_panel.setObjectName("leftPanel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.video_widget = QVideoWidget()
        self.video_widget.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatioByExpanding)
        left_layout.addWidget(self.video_widget)
        
        self.media_player.setVideoOutput(self.video_widget)
        script_dir = os.path.dirname(os.path.realpath(__file__))
        video_path = os.path.join(script_dir, "VID.mp4")
        self.media_player.setSource(QUrl.fromLocalFile(video_path))
        self.media_player.setLoops(QMediaPlayer.Loops.Infinite)
        self.media_player.play()
        
        # --- Right Panel ---
        self.stacked_widget = QStackedWidget()
        self.signup_panel = SignUpPanel(self.firebase_auth)
        self.login_panel = LoginPanel(self.firebase_auth)
        self.stacked_widget.addWidget(self.signup_panel)
        self.stacked_widget.addWidget(self.login_panel)
    
        self.signup_panel.show_login_requested.connect(self.show_login)
        self.login_panel.show_signup_requested.connect(self.show_signup)
        self.signup_panel.signup_successful.connect(self.show_login)
        self.login_panel.login_successful.connect(self.login_successful.emit)

    # --- Assemble Main Layout ---
        main_layout.addWidget(left_panel, 1)

        # --- Separator (trimmed, centered) ---
        sep_container = QWidget()
        sep_v = QVBoxLayout(sep_container)
        sep_v.setContentsMargins(0, 40, 0, 40)  # trim from top & bottom
        sep_v.setSpacing(0)

        separator = QFrame()
        separator.setObjectName("separatorLine")
        separator.setFrameShape(QFrame.Shape.NoFrame)  # we'll style it flat
        separator.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        separator.setFixedWidth(2)  # thickness

        sep_v.addStretch()
        sep_v.addWidget(separator, alignment=Qt.AlignmentFlag.AlignHCenter)
        sep_v.addStretch()

        main_layout.addWidget(sep_container, 0)


        main_layout.addWidget(self.stacked_widget, 1)
    
    def media_player_error(self, error, error_string):
        print(f"Video Player Error: {error_string}")
        QMessageBox.critical(self, "Video Error", f"Could not play video: {error_string}")
    
    def show_login(self):
        self.stacked_widget.setCurrentWidget(self.login_panel)
        self.setWindowTitle("Sign In")

    def show_signup(self):
        self.stacked_widget.setCurrentWidget(self.signup_panel)
        self.setWindowTitle("Create an Account")

    def apply_stylesheet(self):
        self.setStyleSheet("""
            #leftPanel, #rightPanel { 
                background-color: #ffffff; 
            }

            #separatorLine {
                background-color: #ced4da;   /* grey */
                border-radius: 1px;           /* soft ends (optional) */
            }

                           
            #titleLabel { color: #212529; font-size: 28px; font-weight: bold; }
            #subtitleLabel { color: #6c757d; font-size: 14px; }
            #subtitleLabel a { color: #4188ff; text-decoration: none; }
                    

            QLineEdit, QTextEdit { 
                background-color: #ffffff; 
                border: 1px solid #ced4da; 
                border-radius: 8px; 
                padding: 12px 15px; 
                color: #212529; 
                font-size: 14px; 
            }
            QLineEdit:focus, QTextEdit:focus { 
                border: 1px solid #4188ff; 
            }

            QPushButton#createAccountButton { 
                background-color: #4188ff; 
                color: #ffffff; 
                font-size: 16px; 
                font-weight: bold; 
                border: none; 
                border-radius: 8px; 
                padding: 14px; 
            }
            QPushButton#createAccountButton:hover { 
                background-color: #3a79e0; 
            }
        """)

# This block is for testing login.py independently. 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    auth_window = AuthWindow()
    auth_window.show()
    sys.exit(app.exec())