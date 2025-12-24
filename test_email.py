import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# PASTE YOUR EXACT 16-CHAR APP PASSWORD BELOW
# ==========================================
email_sender = 'Cresttechnocrat@gmail.com'
email_password = 'PUT_YOUR_16_CHAR_APP_PASSWORD_HERE' # <--- PASTE IT HERE
email_receiver = 'Cresttechnocrat@gmail.com'

subject = "Test Email"
body = "If you receive this, your credentials are correct!"

message = MIMEMultipart()
message["From"] = email_sender
message["To"] = email_receiver
message["Subject"] = subject
message.attach(MIMEText(body, "plain"))

try:
    # Connect to Gmail
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    
    print("Attempting to log in...")
    server.login(email_sender, email_password)
    print("Login SUCCESSFUL! Sending mail...")
    
    server.sendmail(email_sender, email_receiver, message.as_string())
    server.quit()
    print("\n✅ EMAIL SENT SUCCESSFULLY!")
    
except Exception as e:
    print(f"\n❌ FAILED! Error: {e}")
    print("This means your Username or Password is incorrect.")