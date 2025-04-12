import smtplib
import mimetypes
import os
from email import encoders
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()


def send_mail(email, subject, text, attachments=None):
    if attachments is None:
        attachments = []

    addr_from = os.getenv("FROM")
    password = os.getenv("PASSWORD")
    host = os.getenv("HOST")
    port = int(os.getenv("PORT", 465))

    if not all([addr_from, password, host]):
        print("Ошибка: Не заданы параметры SMTP в переменных окружения")
        return False

    msg = MIMEMultipart()
    msg["From"] = addr_from
    msg['To'] = email
    msg['Subject'] = subject

    body = text
    msg.attach(MIMEText(body, 'plain'))

    try:
        process_attachments(msg, attachments)
    except Exception as e:
        print(f"Ошибка при обработке вложений: {e}")
        return False

    try:
        server = smtplib.SMTP_SSL(host, port)
        server.login(addr_from, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False


def process_attachments(msg, attachments):
    for f in attachments:
        if os.path.isfile(f):
            attach_file(msg, f)
        elif os.path.exists(f):
            dir_files = os.listdir(f)
            for file in dir_files:
                attach_file(msg, os.path.join(f, file))


def attach_file(msg, filepath):
    attach_types = {
        'text': MIMEText,
        'image': MIMEImage,
        'audio': MIMEAudio
    }

    filename = os.path.basename(filepath)
    ctype, encoding = mimetypes.guess_type(filepath)
    if ctype is None or encoding is not None:
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)

    with open(filepath, 'rb' if maintype != 'text' else 'r') as fp:
        if maintype in attach_types:
            file = attach_types[maintype](fp.read(), _subtype=subtype)
        else:
            file = MIMEBase(maintype, subtype)
            file.set_payload(fp.read())
            encoders.encode_base64(file)
        file.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(file)