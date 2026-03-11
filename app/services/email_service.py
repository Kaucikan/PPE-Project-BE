# import smtplib
# import time
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.mime.image import MIMEImage
# from datetime import datetime
# from app.config import settings

# last_email_time = 0
# EMAIL_COOLDOWN = 15


# def send_violation_email(image_path: str):
#     global last_email_time

#     now = time.time()

#     # ⭐ cooldown protection
#     if now - last_email_time < EMAIL_COOLDOWN:
#         return

#     sender = settings.EMAIL
#     password = settings.APP_PASS
#     receivers = [settings.RECEIVER_EMAIL]

#     msg = MIMEMultipart()
#     msg["Subject"] = "🚨 PPE Violation Alert"
#     msg["From"] = sender
#     msg["To"] = ", ".join(receivers)

#     html = f"""
#     <h2 style="color:red;">🚨 PPE Violation Detected</h2>
#     <p>Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
#     """

#     msg.attach(MIMEText(html, "html"))

#     # attach snapshot
#     try:
#         with open(image_path, "rb") as f:
#             img = MIMEImage(f.read())
#             msg.attach(img)
#     except Exception as e:
#         print("Image error:", e)

#     try:
#         server = smtplib.SMTP("smtp.gmail.com", 587)
#         server.starttls()
#         server.login(sender, password)
#         server.sendmail(sender, receivers, msg.as_string())
#         server.quit()

#         print("EMAIL SENT")
#         last_email_time = now

#     except Exception as e:
#         print("EMAIL ERROR:", e)

import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from datetime import datetime

from app.config import settings

EMAIL_COOLDOWN = 15
last_email_time = 0


def send_violation_email(image_path):

    global last_email_time

    now = time.time()

    if now - last_email_time < EMAIL_COOLDOWN:
        return

    sender = settings.EMAIL
    password = settings.APP_PASS
    receiver = settings.RECEIVER_EMAIL

    msg = MIMEMultipart()

    msg["Subject"] = "PPE Violation Detected"
    msg["From"] = sender
    msg["To"] = receiver

    msg.attach(MIMEText(
        f"Violation detected at {datetime.now()}",
        "plain"
    ))

    with open(image_path,"rb") as f:
        img = MIMEImage(f.read())
        msg.attach(img)

    server = smtplib.SMTP("smtp.gmail.com",587)
    server.starttls()
    server.login(sender,password)
    server.sendmail(sender,receiver,msg.as_string())
    server.quit()

    last_email_time = now