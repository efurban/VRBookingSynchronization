import datetime
import imaplib

import sys
reload(sys)
sys.setdefaultencoding("utf8")

user_agent = 'Mozilla/5 (Solaris 10) Gecko'
headers = { 'User-Agent' : user_agent }


userName = "nycaptapt@gmail.com"
passwd = "vavanyc99"

class AirbnbConfirmation(object):
    def __init__(self):
        self.emails = []

    def GetAll(self, numOfDaysLookback):
        self.emails = []

        date = (datetime.date.today() - datetime.timedelta(numOfDaysLookback)).strftime("%d-%b-%Y")
        imapSession = imaplib.IMAP4_SSL('imap.gmail.com')
        typ, accountDetails = imapSession.login(userName, passwd)
        if typ != 'OK':
            print('Not able to sign in!')
            raise 0

        imapSession.select('[Gmail]/All Mail', True)
        typ, data = imapSession.uid('search', None, '(SENTSINCE {date} HEADER Subject "Reservation Confirmed - " FROM "@airbnb.com")'.format(date=date))
        if typ != 'OK':
            print('Error searching Inbox.')
            raise 0

        # Iterating over all emails
        messageID_list = data[0].split()
        print 'total airbnb email confirmation count: %s' % ( len(messageID_list) )
        for messageID in messageID_list:
            typ, messageParts = imapSession.uid('fetch', messageID, '(RFC822)')
            if typ != 'OK':
                print('Error fetching mail.')
                raise 0
            emailBody = messageParts[0][1] # take the raw email. the parser later will get the proper payload
            if 'Fwd:' not in emailBody and 'Re:' not in emailBody:
                self.emails.append(emailBody)

        imapSession.close()
        imapSession.logout()


    # note that if you want to get text content (body) and the email contains
    # multiple payloads (plaintext/ html), you must parse each message separately.
    # use something like the following: (taken from a stackoverflow post)
    def get_first_text_block(self, email_message_instance):
        maintype = email_message_instance.get_content_maintype()
        if maintype == 'multipart':
            for part in email_message_instance.get_payload():
                if part.get_content_maintype() == 'text':
                    return part.get_payload()
        elif maintype == 'text':
            return email_message_instance.get_payload()


class WimduConfirmation(object):
    def __init__(self):
        self.emails = []

    def GetAll(self, numOfDaysLookback):
        self.emails = []

        date = (datetime.date.today() - datetime.timedelta(numOfDaysLookback)).strftime("%d-%b-%Y")
        imapSession = imaplib.IMAP4_SSL('imap.gmail.com')
        typ, accountDetails = imapSession.login(userName, passwd)
        if typ != 'OK':
            print('Not able to sign in!')
            raise 0

        imapSession.select('[Gmail]/All Mail', True)
        typ, data = imapSession.uid('search', None, '(SENTSINCE {date} HEADER Subject "Booking successfully accepted!")'.format(date=date))
        if typ != 'OK':
            print('Error searching Inbox.')
            raise 0

        # Iterating over all emails
        messageID_list = data[0].split()
        print 'total Wimdu email confirmation count: %s' % ( len(messageID_list) )
        for messageID in messageID_list:
            typ, messageParts = imapSession.uid('fetch', messageID, '(RFC822)')
            if typ != 'OK':
                print('Error fetching mail.')
                raise 0
            emailBody = messageParts[0][1] # take the raw email. the parser later will get the proper payload
            self.emails.append(emailBody)

        imapSession.close()
        imapSession.logout()

class BookingComConfirmation(object):
    def __init__(self):
        self.emails = []

    def GetAll(self, numOfDaysLookback):
        self.emails = []

        date = (datetime.date.today() - datetime.timedelta(numOfDaysLookback)).strftime("%d-%b-%Y")
        imapSession = imaplib.IMAP4_SSL('imap.gmail.com')
        typ, accountDetails = imapSession.login(userName, passwd)
        if typ != 'OK':
            print('Not able to sign in!')
            raise 0

        imapSession.select('[Gmail]/All Mail', True)
#        typ, data = imapSession.uid('search', None, '(SENTSINCE {date} HEADER Subject "Please confirm: new reservation! (206018895, Wednesday, 24 July 13)")'.format(date=date))
        typ, data = imapSession.uid('search', None, '(SENTSINCE {date} HEADER Subject "Please confirm: new reservation! ")'.format(date=date))
        if typ != 'OK':
            print('Error searching Inbox.')
            raise 0

        # Iterating over all emails
        messageID_list = data[0].split()
        print 'total Booking.com email confirmation count: %s' % ( len(messageID_list) )
        for messageID in messageID_list:
            typ, messageParts = imapSession.uid('fetch', messageID, '(RFC822)')
            if typ != 'OK':
                print('Error fetching mail.')
                raise 0
            emailBody = messageParts[0][1] # take the raw email. the parser later will get the proper payload
            self.emails.append(emailBody)

        imapSession.close()
        imapSession.logout()