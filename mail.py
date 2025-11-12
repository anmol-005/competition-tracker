import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

def send_price_alert():
    """
    Sends a fixed HTML email alert about a competitor price drop.
    Reads SMTP and recipient info from .env file.
    """

    # Load environment variables from .env
    load_dotenv()

    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

    # === Email content ===
    sender = SMTP_USER
    recipient = ADMIN_EMAIL
    subject = "🚨 Competitor Price Drop Alert"

    html_content = """
    <html>
      <body style="font-family: Arial, sans-serif; background-color:#fafafa; padding:20px;">
        <h2 style="color:#d9534f;">Competitor Just Dropped Their Price!</h2>
        <p>Hey Admin,</p>
        <p>We noticed that one of your competitors just reduced their product price.</p>
        <p><b>Action Required:</b> Log in to your dashboard to review and adjust your pricing strategy.</p>
        <p><a href="https://yourwebsite.com/admin"
              style="background:#0275d8;color:white;padding:10px 15px;text-decoration:none;border-radius:5px;">
              Login as Admin
            </a></p>
        <p style="color:#555;">– Automated Price Monitor</p>
      </body>
    </html>
    """

    # === Construct the email ===
    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html"))

    # === Send the email ===
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print(f"✅ Price alert email sent successfully to {recipient}")
    except Exception as e:
        print("❌ Failed to send email:", e)
