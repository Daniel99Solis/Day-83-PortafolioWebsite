import smtplib
import os

# Data of the email emisor
my_email = os.environ["EMAIL"]
password = os.environ["PASSWORD"]


class EmailSender:
    def __init__(self):
        self.message_send = False

    def send_mail(self, data):
        with smtplib.SMTP("smtp.gmail.com") as connection:
            connection.starttls()
            connection.login(user=my_email, password=password)
            connection.sendmail(from_addr=my_email,
                                to_addrs="solis.alcantar.daniel@gmail.com",
                                msg=f"Subject:New Message Portfolio\n\n"
                                    f"Name: {data['name']}\n\n"
                                    f"Email: {data['email']}\n\n"
                                    f"Phone: {data['phone']}\n\n"
                                    f"Message: {data['message']}")