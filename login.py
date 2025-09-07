import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QCheckBox, QFrame, QStackedWidget, QMessageBox, QTextEdit,
    QGridLayout
)
from PyQt6.QtGui import QFont, QPixmap, QCursor, QPainter, QBrush, QColor, QPainterPath
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QRect, QEasingCurve, QRectF, QSize

# Import our Firebase handler
from firebase_auth import FirebaseAuthHandler

# Custom QLabel for drawing rounded images
class RoundedImageLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("border-radius: 15px; background-color: transparent;")
        self.setScaledContents(False)

    def setPixmap(self, pixmap):
        self.pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        if hasattr(self, 'pixmap') and not self.pixmap.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = self.rect()
            path = QPainterPath()
            path.addRoundedRect(QRectF(rect), 15, 15)
            painter.setClipPath(path)
            scaled_pixmap = self.pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            point = self.rect().center() - scaled_pixmap.rect().center()
            painter.drawPixmap(point, scaled_pixmap)

class RoundedSlide(QWidget):
    def __init__(self, radius=15, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.radius = radius
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), self.radius, self.radius)
        painter.setClipPath(path)
        # We don't call super().paintEvent() because we are handling the background
        # and clipping, and the children (image, caption) will paint themselves.

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
        self.dot_animations = []
        self.init_ui()
        self.apply_stylesheet()
        self.slide_timer = QTimer(self)
        self.slide_timer.timeout.connect(self.next_slide)
        self.slide_timer.start(3000)

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        left_panel = QWidget()
        left_panel.setObjectName("leftPanel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 20, 20, 20)
        
        self.image_stack = QStackedWidget()
        slide1 = self.create_image_slide("slide1.jpg", "Showcase your product\nin a beautiful way.")
        slide2 = self.create_image_slide("slide2.jpg", "Engage users with\nvibrant visuals.")
        slide3 = self.create_image_slide("slide3.jpg", "Highlight key features\nand benefits.")
        for slide in [slide1, slide2, slide3]:
            self.image_stack.addWidget(slide)
        
        slide_master_container = QWidget()
        slide_master_layout = QGridLayout(slide_master_container)
        slide_master_layout.setContentsMargins(0,0,0,0)
        
        indicator_container = QWidget()
        indicator_container.setObjectName("indicatorContainer")
        indicator_layout = QHBoxLayout(indicator_container)
        indicator_layout.setContentsMargins(0, 0, 0, 20)
        indicator_layout.setSpacing(10)
        indicator_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        
        self.indicator_dots = []
        for i in range(self.image_stack.count()):
            dot = QWidget()
            dot.setFixedSize(8, 8)
            self.indicator_dots.append(dot)
            indicator_layout.addWidget(dot)
            anim = QPropertyAnimation(dot, b"minimumSize")
            anim.setDuration(300)
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            self.dot_animations.append(anim)

        slide_master_layout.addWidget(self.image_stack, 0, 0)
        slide_master_layout.addWidget(indicator_container, 0, 0)
        left_layout.addWidget(slide_master_container)
        
        self.stacked_widget = QStackedWidget()
        self.signup_panel = SignUpPanel(self.firebase_auth)
        self.login_panel = LoginPanel(self.firebase_auth)
        self.stacked_widget.addWidget(self.signup_panel)
        self.stacked_widget.addWidget(self.login_panel)
    
        self.signup_panel.show_login_requested.connect(self.show_login)
        self.login_panel.show_signup_requested.connect(self.show_signup)
        self.signup_panel.signup_successful.connect(self.show_login)
        self.login_panel.login_successful.connect(self.login_successful.emit)
    
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(self.stacked_widget, 1)
    
        self.update_indicators(0)

    def create_image_slide(self, image_path, caption_text):
        slide = RoundedSlide(radius=15)
        layout = QGridLayout(slide)
        layout.setContentsMargins(0, 0, 0, 0)
        image_label = RoundedImageLabel()
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print(f"Error: Image not found at '{image_path}'.")
            error_label = QLabel(f"Image Not Found:\n{image_path}")
            error_label.setStyleSheet("background-color: #555; color: white; font-size: 20px; border-radius: 15px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(error_label, 0, 0)
        else:
            image_label.setPixmap(pixmap)
            layout.addWidget(image_label, 0, 0)
        caption_label = QLabel(caption_text)
        caption_label.setObjectName("captionLabel")
        caption_label.setWordWrap(True)
        caption_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        caption_label.setContentsMargins(40, 40, 40, 60)
        layout.addWidget(caption_label, 0, 0)
        return slide

    def next_slide(self):
        current_index = self.image_stack.currentIndex()
        next_index = (current_index + 1) % self.image_stack.count()
        self.image_stack.setCurrentIndex(next_index)
        self.update_indicators(next_index)

    def update_indicators(self, index):
        for i, dot in enumerate(self.indicator_dots):
            dot.setObjectName("indicatorDotActive" if i == index else "indicatorDotInactive")
            animation = self.dot_animations[i]
            if i == index:
                animation.setEndValue(QSize(24, 8))
            else:
                animation.setEndValue(QSize(8, 8))
            animation.start()
            dot.style().unpolish(dot)
            dot.style().polish(dot)

    def show_login(self):
        self.stacked_widget.setCurrentWidget(self.login_panel)
        self.setWindowTitle("Sign In")

    def show_signup(self):
        self.stacked_widget.setCurrentWidget(self.signup_panel)
        self.setWindowTitle("Create an Account")

    def apply_stylesheet(self):
        # ++ CORRECTED STYLESHEET ++
        self.setStyleSheet("""
            /* This dark background makes the left panel visible and provides contrast. */
            #leftPanel { 
                background-color: #ffffff; 
            }

            /* This ensures the right panel has the clean white background you want. */
            #rightPanel { 
                background-color: #ffffff; 
            }
            
            #indicatorContainer { background-color: transparent; }
            #indicatorDotInactive { 
                background-color: rgba(255, 255, 255, 0.5); 
                border-radius: 4px; 
            }
            #indicatorDotActive { 
                background-color: #ffffff; 
                border-radius: 4px; 
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

            /* A dark, semi-transparent background for the caption looks best on images. */
            #captionLabel {
                color: #ffffff;
                font-size: 28px;
                font-weight: bold;
                background-color: rgba(0, 0, 0, 0.4);
            }
        """)

# This block is for testing login.py independently. 
# Your main.py will not use this.
if __name__ == '__main__':
    app = QApplication(sys.argv)
    auth_window = AuthWindow()
    auth_window.show()
    sys.exit(app.exec())
