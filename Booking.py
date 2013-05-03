# This Python file uses the following encoding: utf-8

"""Booking.py: a generic booking object to hold a booking """

__author__      = "Travis Wu"
__copyright__   = "Copyright 2013, NYCAPT"

import email
import quopri
import re
import datetime
from BeautifulSoup import BeautifulSoup
#import urllib
import urllib2
import locale
#import parsedatetime
import mx.DateTime.Parser as mxparser
from email.header import decode_header

from dateutil import parser


import sys
reload(sys)
sys.setdefaultencoding("utf8")

# remove annoying characters
chars = {
    '\xc2\x82' : ',',        # High code comma
    '\xc2\x84' : ',,',       # High code double comma
    '\xc2\x85' : '...',      # Tripple dot
    '\xc2\x88' : '^',        # High carat
    '\xc2\x91' : '\x27',     # Forward single quote
    '\xc2\x92' : '\x27',     # Reverse single quote
    '\xc2\x93' : '\x22',     # Forward double quote
    '\xc2\x94' : '\x22',     # Reverse double quote
    '\xc2\x95' : ' ',
    '\xc2\x96' : '-',        # High hyphen
    '\xc2\x97' : '--',       # Double hyphen
    '\xc2\x99' : ' ',
    '\xc2\xa0' : ' ',
    '\xc2\xa6' : '|',        # Split vertical bar
    '\xc2\xab' : '<<',       # Double less than
    '\xc2\xbb' : '>>',       # Double greater than
    '\xc2\xbc' : '1/4',      # one quarter
    '\xc2\xbd' : '1/2',      # one half
    '\xc2\xbe' : '3/4',      # three quarters
    '\xca\xbf' : '\x27',     # c-single quote
    '\xcc\xa8' : '',         # modifier - under curve
    '\xcc\xb1' : ''          # modifier - under line
}

def replace_chars(match):
    char = match.group(0)
    return chars[char]

class Booking:
    def __init__(self):
        self.bookingSource = None
        self.bookingDate = None
        self.aptNum = None
        self.aptName = None
        self.confirmationCode = None
        self.checkInDate = None
        self.checkOutDate = None
        self.guestName = ''.encode('utf-8')
        self.guestCount = None
        self.phone = None
        self.email = None
        self.price = None
        self.note = None
        self.BS_aptID = None
        self.deposit = None

    def parseBookingFromAirbnbEmail(self, emailBody):
        raw_email_str = emailBody.decode('utf-8')
        _email = email.message_from_string(raw_email_str)
        emailBody = quopri.decodestring(emailBody)  # remove all 3D quote printable chars
        emailBody = re.sub('(' + '|'.join(chars.keys()) + ')', '', emailBody)  # clean up non ascii chars

        emailSubject = _email['subject']
        bytes, encoding = decode_header(emailSubject)[0]
        if encoding is not None:
            self.guestName = bytes.decode(encoding).replace('Reservation Confirmed - ', '')
        else:
            self.guestName = emailSubject.replace('Reservation Confirmed - ', '')

        print self.guestName

        self.bookingDate = mxparser.DateTimeFromString(str(_email['date'])).pydatetime()

        soup = BeautifulSoup(repr(emailBody))
        twoBlues = soup.findAll("a", style=re.compile(".*color.*:.*#1d95cb.*;.*text-decoration.*:.*none.*"))
        self.aptName = twoBlues[2].string
        aptParts = self.aptName.string.split('.')
        if len(aptParts) > 1:
            self.aptNum = aptParts[len(aptParts)-1]
        if len(aptParts) <= 1:
            self.aptNum = self.aptName

        contacts = soup.findAll("div", { "class" : "contact_info" })
        self.phone = contacts[0].contents[2].string.replace(' &#160;', "")  # phone #      # contacts[0].contents[2].string.replace(' &#160;', "")
        try:
            self.email = contacts[0].contents[6].string
        except Exception, e:
            pass
        try:
            if self.email is None:
                self.email = contacts[0].contents[3].string
        except Exception, e:
            pass
        try:
            if self.email is None:
                self.email = contacts[0].contents[9].string
        except Exception, e:
            pass

        try:
            dates = soup.findAll("td", { "class" : 'heading' })
            locale.setlocale(locale.LC_ALL, '')
            self.guestCount = dates[3].contents[0].string
            payout = soup.findAll('table', { 'class':'receipt'})
            self.price = payout[0].contents[3].contents[3].contents[3].string.replace('$','')
            confirmationCode = soup.findAll('h3', {'class':'confirmation_code'})
            self.confirmationCode = confirmationCode[0].string
            self.note = "Booked from Airbnb\n%s\n%s\n%s" % (self.phone, self.email, self.confirmationCode)     #' '.join(contacts_text.split('\\r\\n'))
            self.bookingSource = "Airbnb"
            # turned out dates are most difficult to parse since we have dates in different locale (languages)

            try:   # handle en locale
                locale.setlocale(locale.LC_ALL, '')
                checkinStr = str(dates[0].contents[0].string)
                checkoutStr = str(dates[1].contents[0].string)
                checkinStr = checkinStr.replace(' de ', ' ')
                checkoutStr = checkoutStr.replace(' de ', ' ')

#                self.checkInDate = parser.parse(checkinStr)
#                self.checkOutDate = parser.parse(checkoutStr)
                self.checkInDate = mxparser.DateFromString(checkinStr.replace('ç', 'c').replace('á', 'a'))
                self.checkInDate = self.checkInDate.pydatetime()
                self.checkOutDate = mxparser.DateFromString(checkoutStr.replace('ç', 'c').replace('á', 'a'))
                self.checkOutDate = self.checkOutDate.pydatetime()
                if self.checkInDate is None or self.checkOutDate is None:
                    print "not cool: checkin date can't be None - confirmation code " , self.confirmationCode
            except Exception, e:
            #                try:  # strangely we have spanish email confirmation.
            #                    locale.setlocale(locale.LC_ALL, 'es_ES')
            ##                    self.checkInDate = datetime.datetime.strptime(dates[0].contents[0].string, '%a, %d de %B de %Y')
            ##                    self.checkOutDate = datetime.datetime.strptime(dates[1].contents[0].string, '%a, %d de %B de %Y')
            #                    self.checkInDate = parser.parse(checkinStr)
            #                    self.checkOutDate = parser.parse(checkoutStr)
            #                except Exception, e:
            #                    try:
            #                        locale.setlocale(locale.LC_ALL, 'fr_FR')
            ##                        self.checkInDate = datetime.datetime.strptime(dates[0].contents[0].string, '%a, %B %d, %Y')
            ##                        self.checkOutDate = datetime.datetime.strptime(dates[1].contents[0].string, '%a, %B %d, %Y')
            #                        self.checkInDate = parser.parse(checkinStr)
            #                        self.checkOutDate = parser.parse(checkoutStr)
            #                    except Exception, e:
            #                        print e
            #                        pass
            #                    pass
                print e
                print 'error: ' , self.confirmationCode, checkinStr, checkoutStr, self.guestName
                pass

        except Exception, e:
            print e


    def parseBookingFromWimduEmail(self, emailBody):
        _email = email.message_from_string(emailBody)

        emailBody = quopri.decodestring(emailBody)  # remove all 3D quote printable chars
        emailBody = re.sub('(' + '|'.join(chars.keys()) + ')', '', emailBody)  # clean up non ascii chars
        self.bookingDate = mxparser.DateTimeFromString(str(_email['date'])).pydatetime()

        soup = BeautifulSoup(repr(emailBody))
        rightColumns = soup.findAll("td", style=re.compile("font-size.*:14px.*;.*border.*:.*1px.*solid.*cccccc"))

        self.bookingSource = "Wimdu"
        try:
            self.confirmationCode = rightColumns[1].string
            self.price = rightColumns[3].string.replace('USD ', '')
            self.aptName = rightColumns[7].contents[0].string
            if '.' in self.aptName:
                self.aptNum = self.aptName.string.split('.')[1]
            else:
                self.aptNum = self.aptName
            self.checkInDate = datetime.datetime.strptime(rightColumns[9].string, '%B %d, %Y')
            self.checkOutDate = datetime.datetime.strptime(rightColumns[11].string, '%B %d, %Y')
            self.guestCount = rightColumns[15].string
#            self.guestName = rightColumns[23].string
#            self.phone = rightColumns[25].string
#            self.email = rightColumns[27].contents[0].string

            self.guestName = rightColumns[25].string.decode('unicode_escape').encode('latin1').decode('utf-8')
            self.phone = rightColumns[27].string
            self.email = rightColumns[29].contents[0].string

            self.note = "Booked from Wimdu\n%s\n%s\n%s" % (self.phone, self.email, self.confirmationCode)
        except Exception, e:
            self.aptName = rightColumns[5].contents[0].string
            if '.' in self.aptName:
                self.aptNum = self.aptName.string.split('.')[1]
            else:
                self.aptNum = self.aptName
            self.confirmationCode = rightColumns[1].string
            self.price = rightColumns[3].string.replace('USD ', '')
            self.checkInDate = datetime.datetime.strptime(rightColumns[7].string, '%B %d, %Y')
            self.checkOutDate = datetime.datetime.strptime(rightColumns[9].string, '%B %d, %Y')
            self.guestCount = rightColumns[13].string
            self.guestName = rightColumns[21].string
            self.phone = rightColumns[23].string
            self.email = rightColumns[25].contents[0].string
            self.note = "Booked from Wimdu\n%s\n%s\n%s" % (self.phone, self.email, self.confirmationCode)
