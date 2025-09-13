import pyrebase
from PyQt6.QtWidgets import QMessageBox
import json
import os
from dotenv import load_dotenv

load_dotenv()

class FirebaseAuthHandler:
    def __init__(self):
        firebase_config = {
          "apiKey": os.getenv("FIREBASE_API_KEY"),
          "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
          "projectId": os.getenv("FIREBASE_PROJECT_ID"),
          "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
          "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
          "appId": os.getenv("FIREBASE_APP_ID"),
          "databaseURL": os.getenv("FIREBASE_DATABASE_URL") 
        }
        
        try:
            self.firebase = pyrebase.initialize_app(firebase_config)
            self.auth = self.firebase.auth()
            self.db = self.firebase.database() # Initialize the database
            print("Firebase Initialized Successfully!")
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setText("Failed to connect to Firebase.")
            msg_box.setInformativeText("Please check your configuration and internet connection.")
            msg_box.setWindowTitle("Connection Error")
            msg_box.exec()
            exit()

    def create_account(self, email, password, first_name, last_name, address):
        try:
            # Step 1: Create the user in Firebase Authentication
            user = self.auth.create_user_with_email_and_password(email, password)
            print(f"Successfully created auth account for {email}")

            # Step 2: Prepare the user's profile data
            user_data = {
                "first_name": first_name,
                "last_name": last_name,
                "address": address,
                "email": email
            }
            
            # Step 3: Save the data to the Realtime Database
            # We use the user's unique ID (localId) as the key for their data.
            uid = user['localId']
            self.db.child("users").child(uid).set(user_data)
            print(f"Successfully saved user data for UID: {uid}")

            return user
            
        except Exception as e:
            # This general exception handling will catch errors from both
            # authentication and database operations.
            self.handle_firebase_error(e)

    def sign_in(self, email, password):
        try:
            user = self.auth.sign_in_with_email_and_password(email, password)
            print(f"Successfully signed in as {email}")
            return user
        except Exception as e:
            self.handle_firebase_error(e)
            
    def handle_firebase_error(self, e):
        try:
            error_json = e.args[1]
            error_data = json.loads(error_json)
            error_message = error_data['error']['message']

            if error_message == "EMAIL_EXISTS":
                raise Exception("This email address is already in use.")
            elif "WEAK_PASSWORD" in error_message:
                raise Exception("Password must be at least 6 characters long.")
            elif error_message == "INVALID_LOGIN_CREDENTIALS":
                raise Exception("Invalid email or password. Please try again.")
            else:
                raise Exception(f"An unknown error occurred: {error_message}")
        except (IndexError, KeyError, json.JSONDecodeError):
            raise Exception(f"An unexpected error occurred: {e}")

