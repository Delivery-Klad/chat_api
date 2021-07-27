from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from Service.Logger import error_log
import smtplib
import rsa
import os


def send_mail(email: str, title: str, text: str):
    try:
        password = os.environ.get('email_password')
        mail_login = os.environ.get('email_login')
        server = smtplib.SMTP_SSL("smtp.mail.ru", 465)
        msg = MIMEMultipart()
        msg['Subject'] = title
        msg['From'] = mail_login
        msg.attach(MIMEText(text, 'plain'))
        try:
            server.login(mail_login, password)
            server.sendmail(mail_login, email, msg.as_string())
            return True
        except Exception as e:
            error_log(e)
            return False
    except Exception as er:
        error_log(er)


def encrypt(msg: bytes, pubkey):
    try:
        pubkey = pubkey.split(', ')
        pubkey = rsa.PublicKey(int(pubkey[0]), int(pubkey[1]))
        encrypt_message = rsa.encrypt(msg, pubkey)
        return encrypt_message
    except Exception as e:
        error_log(e)
        return None
