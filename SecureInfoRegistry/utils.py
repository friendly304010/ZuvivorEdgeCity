import os
import json
from cryptography.fernet import Fernet
from app import mail
from flask_mail import Message

# Initialize Fernet with the encryption key
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY is not set in the environment variables")

fernet = Fernet(ENCRYPTION_KEY)

def encrypt_data(data):
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    return fernet.decrypt(encrypted_data.encode()).decode()

def check_overlap_between_reports(report1, reports):
    overlap_count = 0
    
    try:
        report1_data = json.loads(decrypt_data(report1.encrypted_data))
    except Exception as e:
        print(f"Error decrypting report1 data: {str(e)}")
        return 0
    
    for report2 in reports:
        if report1.id != report2.id:
            try:
                report2_data = json.loads(decrypt_data(report2.encrypted_data))
                if report1_data.get('perpetratorName') == report2_data.get('perpetratorName'):
                    overlap_count += 1
            except Exception as e:
                print(f"Error decrypting report2 data (ID: {report2.id}): {str(e)}")
    
    return overlap_count

def send_notification_to_victim(email, overlap_count):
    msg = Message("New Report Overlap Notification",
                  sender="noreply@example.com",
                  recipients=[email])
    msg.body = f"A new report has been submitted about the same perpetrator. There are now {overlap_count} overlapping reports."
    mail.send(msg)
