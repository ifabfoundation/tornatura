from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from  core import config
import smtplib
from typing import List

from fastapi import logger


def paginate(queryset: List, page=1, limit=25):
    start = (page - 1) * limit
    end = start + limit
    return queryset[start:end]

def send_email(receiver_email, subject, email_body):
    sender_email = config.APIConfig.SMTP_EMAIL
    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email
   
    # Create HTML version of your message
    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(email_body, "html")

    # The email client will try to render the last part first
    message.attach(part1)

    try:
        server = smtplib.SMTP_SSL(config.APIConfig.SMTP_HOST, config.APIConfig.SMTP_PORT)
        server.ehlo()
        server.login(sender_email, config.APIConfig.SMTP_PASSWORD)
        server.sendmail(sender_email, receiver_email, message.as_string())
        logger.logger.info('Email sent to %s' % receiver_email)
        server.quit()
    except Exception as e:
        logger.logger.error("Email sent failed to %s with error %s" % (receiver_email, e))
