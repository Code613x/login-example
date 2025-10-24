import resend
import os
API_Key = os.environ.get("email_api_key")
def send_password_reset(user_email, reset_url, user_name):
    
    resp = "This is not avilable yet", 500
    return resp