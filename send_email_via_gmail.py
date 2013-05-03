#!/usr/bin/env python

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
import os

gmail_user = "nycaptapt@gmail.com"
gmail_name = "NYC Apt <nycaptapt@gmail.com>"
gmail_pwd = "vavanyc99"

def mail(to, subject, text, attach):
    msg = MIMEMultipart()

    msg['From'] = gmail_name
    msg['To'] = to
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

#    part = MIMEBase('application', 'octet-stream')
#    part.set_payload(open(attach, 'rb').read())
#    Encoders.encode_base64(part)
#
#    part.add_header('Content-Disposition',
#        'attachment; filename="%s"' % os.path.basename(attach))
#    msg.attach(part)

    mailServer = smtplib.SMTP("smtp.gmail.com", 587)
    #mailServer = smtplib.SMTP_SSL("smtp.gmail.com", 465)   # didn't work for me
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(gmail_user, gmail_pwd)
    #mailServer.sendmail(gmail_user, to, msg.as_string())   # just e-mail address in the From: field
    mailServer.sendmail(gmail_name, to, msg.as_string())   # name + e-mail address in the From: field
    # Should be mailServer.quit(), but that crashes...
    mailServer.close()

if __name__ == "__main__":
    mail("send-mail-to-this-person@address.com",
        "Hello from Python!",
        "This is an e-mail sent with Python.",
        "/tmp/some-image.jpg")
