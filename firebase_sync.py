import os
import pyrebase
from dotenv import load_dotenv

# Load environment variables (same as your auth file)
load_dotenv()

class FirebaseSyncHandler:
    """
    Handles all Firebase Firestore and Cloud Storage operations for reports.
    """
    def __init__(self):
        # Your exact Firebase configuration from firebase_auth.py
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
            self.db = self.firebase.firestore()
            self.storage = self.firebase.storage()
            print("Firebase Sync Handler Initialized Successfully!")
        except Exception as e:
            # Handle initialization error
            print(f"Error initializing Firebase Sync Handler: {e}")
            raise

    def sync_report(self, user_session, report_data, local_pdf_path):
        """
        Uploads the report JSON to Firestore and the PDF to Cloud Storage.

        Args:
            user_session (dict): The full user object from a successful login.
            report_data (dict): The final dictionary of report data.
            local_pdf_path (str): The local path to the generated PDF file.
        """
        if not all([user_session, report_data, local_pdf_path]):
            return False, "Missing required data for sync."

        try:
            user_uid = user_session['localId']
            report_id = report_data.get("report_id")
            
            if not report_id:
                return False, "Report ID is missing from report data."

            print(f"Starting report sync for user {user_uid}...")

            # 1. Upload the JSON data to Firestore
            # Creates a document in a 'reports' subcollection under the user's document.
            print("Uploading report data to Firestore...")
            self.db.collection("users").document(user_uid).collection("reports").document(report_id).set(report_data)
            
            # 2. Upload the PDF file to Cloud Storage
            # The path in the cloud will be: reports/{user_uid}/{report_id}.pdf
            cloud_path = f"reports/{user_uid}/{os.path.basename(local_pdf_path)}"
            print(f"Uploading PDF to Cloud Storage at: {cloud_path}")
            
            # The user's ID token is required to authenticate the file upload.
            self.storage.child(cloud_path).put(local_pdf_path, user_session['idToken'])
            
            print("Report and PDF successfully synced to Firebase!")
            return True, "Report successfully synced to your account."

        except KeyError as e:
            print(f"Error during report sync: Missing key '{e}' in user session.")
            return False, f"User session is invalid. Please log in again. Missing: {e}"
        except Exception as e:
            print(f"Error during report sync: {e}")
            return False, f"Failed to sync report to the cloud. Error: {e}"