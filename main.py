# THIS FILE IS THE MAIN CONTROLLER BETWEEN THE LOGIN/SIGNUP PAGE AND THE MAIN WIPING PAGE

from driver import ShudhhiApp, STYLESHEET
from login import AuthWindow

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase

app = None
auth_window = None
main_window = None

def main():
    global app, auth_window, main_window
    
    app = QApplication(sys.argv)
    QFontDatabase.addApplicationFont("Inter-Regular.ttf")
    app.setStyleSheet(STYLESHEET)

    # Create AuthWindow first
    auth_window = AuthWindow() 

    def on_auth_success(user):
        global main_window
        print(f"Login/Signup successful for {user['email']} (UID: {user['localId']})! Closing auth window.")
        
        auth_window.close()  

        # Keep reference alive
        main_window = ShudhhiApp()
        main_window.show()

    # Connect the signal (now receives dict, not email string)
    auth_window.login_successful.connect(on_auth_success)

    # Show AuthWindow
    auth_window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
