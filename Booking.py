# This Python file uses the following encoding: utf-8

"""Booking.py: a generic booking object to hold a booking """

__author__      = "Travis Wu"
__copyright__   = "Copyright 2013, NYCAPT"

import email
import quopri
import re
import datetime
from BeautifulSoup import BeautifulSoup
import locale
import mechanize
import mx.DateTime.Parser as mxparser
from email.header import decode_header
from selenium import webdriver


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
        self.address = ''

        # additional fields only to be used for booking.com bookings
        self.CreditCardType = ''
        self.CreditCardNum = ''
        self.ExpiryDate = ''
        self.CVC = ''

#    def parseBookingFromBS(self, bsObj):


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


    def parseBookingFromBookingComEmail(self, emailBody):
        _email = email.message_from_string(emailBody)
        print _email['subject']
        emailBody = ""
        payload = _email.get_payload(decode=True)
        # there is only one , so this walk is ok
        for part in _email.walk():
            # each part is a either non-multipart, or another multipart message
            # that contains further parts... Message is organized like a tree
            if part.get_content_type() == 'text/html':
                emailBody = part.get_payload(decode=True) # prints the raw text

        # get the url from confirmation email.
        # log into booking admin page
        # retrieves the booking confirmation page
        soup = BeautifulSoup(repr(emailBody))
        confirmLinks = soup.findAll('a', {'href': True})
#        browser = mechanize.Browser()
#        browser.set_handle_robots(False)
#        browser.addheaders = [('User-agent', 'Firefox')]
#        browser.open('https://admin.booking.com/hotel/hoteladmin/?lang=en')
##browser.open('https://admin.booking.com/hotel/hoteladmin/login.html')
#        browser.select_form(name="myform")
#        browser.form["loginname"] = "536676"
#        browser.form["password"] = "nycapt523"
#        browser.submit()
        # get the page content
        url = confirmLinks[0].attrMap['href']
        url = url.replace('\\n','')
#        page = browser.open(url)



        ############## phantomjs + selenium ####################
        driver = webdriver.PhantomJS('/Users/urban/Downloads/phantomjs-1.9.1-macosx/bin/phantomjs')
        driver.set_window_size(1024, 768) # optional

        # has cc
        #https://admin.booking.com/hotel/hoteladmin/bookings/booking.html?hotel_id=536676;bn=290921603;ses=1fc072ac73fdeb471d6a725e5dbbffc3

        # no cc
        #https://admin.booking.com/hotel/hoteladmin/bookings/booking.html?hotel_id=536676;bn=413462216;ses=917d05f85ac757728857a8aa252b6acb

        driver.get(url)
#        driver.save_screenshot( 'screen_1.png') # save a screenshot to disk
        try:
            err = driver.find_element_by_class_name('error')  # if err, means we need to login (session ended)
            if err.text == u'Please login again, your session has expired':
                driver.find_element_by_name('loginname').send_keys('536676')
                driver.find_element_by_name('password').send_keys('nycapt523')
                driver.find_element_by_name("login").click()
        except Exception, e:    # if already logged in, simply continue
            pass

#        driver.save_screenshot( 'screen_2.png') # save a screenshot to disk

        # from here, we have a. has user name , password and login b. nothing
        try:
            driver.find_element_by_name('loginname').send_keys('536676')
            driver.find_element_by_name('password').send_keys('nycapt523')
            driver.find_element_by_name("login").click()
        except Exception, e:
            pass

        confirmationPage = driver.page_source
        driver.save_screenshot( str(self.confirmationCode) + '_' + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + '_CC_.png') # save a screenshot to disk

    #        driver.save_screenshot( 'screen_3.png') # save a screenshot to disk

        ########################



# without credit card info page
#        confirmationPage = page.read().decode("UTF-8")

        # get to the page with credit card information
#        browser.select_form(nr=0)
#        browser.form["loginname"] =  "536676"
#        browser.form["password"] = "nycapt523"
#        creditCardPage = browser.submit()
#        finalPageWithCCURL = creditCardPage.wrapped._url
#        page = browser.open(finalPageWithCCURL)
#        confirmationPage = page.read().decode("UTF-8")


        # soup it
        soup = BeautifulSoup(repr(confirmationPage))
        allItems = soup.findAll('td')
        bookerBookingSoup = soup.findAll("div", { "class" : "booker-booking" })
        bookerBooking = bookerBookingSoup[0].contents[0].replace('\\n','').replace('\\t','').split('&nbsp;')
#self.price = bookerBooking[2].replace('USD','').replace('&nbsp;', '').strip()
        self.price = int(bookerBooking[3])

        contactSoup = soup.findAll("div", { "class" : "booker-contact" })
        contactAddressSoup = soup.findAll("div", { "class" : "booker-address" })
        contact = contactSoup[0].string.replace('\\n','').replace('\\t','').split('\\xb7')
        self.phone = contact[0].strip()
        self.email = contact[1].strip()

        bookerInfoSoup = soup.find("div", { "class" : "booker-info" })
        bookerInfo = bookerInfoSoup.contents[0].replace('\\n','').replace('\\t','').split('\\xb7')
        try:
            self.bookingDate =  datetime.datetime.strptime(bookerInfo[0].strip(), '%A, %B %d, %Y at %H:%M:%S')
        except Exception, e:
            self.bookingDate =  datetime.datetime.strptime(bookerInfo[0].strip(), '%A, %B %d, %Yat%H:%M:%S')

        self.confirmationCode = bookerInfo[1].strip()
        self.guestName = allItems[1].contents[1].contents[0].replace('\\n','').replace('\\t','').strip()
        self.guestName = self.guestName.decode('unicode_escape').encode('utf-8').decode('utf-8')
        self.aptName = allItems[7].string.replace('\\n','').replace('\\t','').strip()
#        self.aptNum
        self.checkInDate = datetime.datetime.strptime(allItems[3].string.strip(), '%d-%m-%Y')
        self.checkOutDate = datetime.datetime.strptime(allItems[5].string.strip(), '%d-%m-%Y')
        self.guestCount = allItems[9].string.replace('\\n','').replace('\\t','').strip()
        self.bookingDate = mxparser.DateTimeFromString(str(_email['date'])).pydatetime()
        self.bookingSource = "Booking.com"
        self.note = "Booked from Booking.com\n%s\n%s\n%s" % (self.phone, self.email, self.confirmationCode)
        self.address = contactAddressSoup[0].string.replace('\\n','').replace('\\t','').strip()
        try:
            if str(allItems[42].string).isdigit():
                # for confirmation emails
                self.CreditCardType = allItems[40].string
                self.CreditCardNum = allItems[42].string
                self.ExpiryDate = allItems[46].string
                self.CVC = allItems[48].string
            elif str(allItems[44].string).isdigit():
                # for cancellation emails
                self.CreditCardType = allItems[42].string
                self.CreditCardNum = allItems[44].string
                self.ExpiryDate = allItems[48].string
                self.CVC = allItems[50].string
        except Exception, e:
            pass


#        ccSoup = BeautifulSoup(repr(creditCardPage))
#        allItems = ccSoup.findAll('td')

