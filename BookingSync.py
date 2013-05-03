
"""BookingSync.py: BookingSync related API objects.  """

__author__      = "Travis Wu"
__copyright__   = "Copyright 2013, NYCAPT"

import slumber
import datetime
import vrDB
import sys

reload(sys);
sys.setdefaultencoding("utf8")

userName = "traviswu@gmail.com"
passwd = "ktxdabcd"


class BSHelper(object):
    def __init__(self):
        self.allBookings = None

    def getAllBookings(self, rentalID):
        existingBookings = BSAPI.API().rentals(rentalID).bookings.get()
        return existingBookings

    def load(self):
#        slber = slumber.API("https://www.bookingsync.com/bookings.xml?from=20130101&status=booked&per_page=500", auth=(userName, passwd))
#        self.allBookings = slber.get()
        self.allBookings = BSAPI.API().bookings.get(status="booked",per_page="500")

class BSAPI(object):
    @staticmethod
    def API():
        return slumber.API("https://www.bookingsync.com/", auth=(userName, passwd))



class BSBooking(object):
    def __init__(self):
        self.account_id = None
        self.adults = None
        self.booked = None
        self.canceled_at = None
        self.children = None
        self.client_id = None
        self.created_at = None
        self.currency = None
        self.deposit = None
        self.discount = None
        self.end_at = None
        self.final_price = None
        self.id = None
        self.initial_price = None
        self.notes = None
        self.rental_id = None
        self.source_id = None
        self.start_at = None
        self.tentative_expires_at = None
        self.unavailable = None
        self.updated_at = None

    def popuateFromBooking(self, _booking):  # book here is the booking parsed outta a email
        tmpBooking = _booking
        self.adults = tmpBooking.guestCount
        self.booked = True
        self.currency = 'USD'
        self.end_at = datetime.datetime.strftime(datetime.datetime(tmpBooking.checkOutDate.year, tmpBooking.checkOutDate.month, tmpBooking.checkOutDate.day, 12), '%Y-%m-%dT%H:%M:%SZ')
        self.final_price = tmpBooking.price
        self.notes = tmpBooking.note  # 'Booked from ' + tmpBooking.bookingSource + "\r\n" + ' '.join(tmpBooking.note.split('\\r\\n'))
        self.start_at = datetime.datetime.strftime(datetime.datetime(tmpBooking.checkInDate.year, tmpBooking.checkInDate.month, tmpBooking.checkInDate.day, 16), '%Y-%m-%dT%H:%M:%SZ')
        self.rental_id = tmpBooking.BS_aptID

    def update(self):
        # need to convert the date to the date BS can recognize
        for attr, value in vars(self).items():
            if attr.endswith('_at') and getattr(self, attr) is not None:
                # need to check the check in / out time here. very important
                newDateFormat = datetime.datetime.strftime(getattr(self, attr), '%Y-%m-%dT%H:%M:%SZ')
                setattr(self, attr, newDateFormat)
        updBSBooking = {}
        updBSBooking['booking'] = self.__dict__
        BSAPI.API().bookings(self.id).put(updBSBooking)

    def post(self):
        newBSBooking = {}
        newBSBooking['booking'] = self.__dict__
        BSAPI.API().bookings.post(newBSBooking)

    def copyFrom(self, cBooking):   # cBooking - booking from BS
    # if we have this booking, populate self with the values from BS
        for attr, value in vars(self).items():
            if attr.endswith('_at') and cBooking[attr] is not None: setattr(self, attr, datetime.datetime.strptime(cBooking[attr], '%Y-%m-%dT%H:%M:%SZ'))
            else: setattr(self, attr, cBooking[attr])


    def exists(self, currBooking):  # booking: from email confirmation
        for apt in BSAPI.API().rentals.get():  # first: find the apt ID
            aptNum = apt["rental"]['name'].split('.')[1]
            if aptNum == currBooking.aptNum:
                currBooking.BS_aptID = apt['rental']['id']
                break

#        print currBooking.aptNum, currBooking.BS_aptID
        # retrieve all existing bookings from BS for this apt
        existingBookings = BSAPI.API().rentals(currBooking.BS_aptID).bookings.get() #.get('20121104')
        #        existingBookings = BSAPI.API().rentals(currBooking.BS_aptID).bookings.get(20130104)

        # check if this booking confirmation already exists on BS
        thisBookingExists = False
        cBooking = None

        for booking in existingBookings:
            cBooking = booking['booking']  # current (matched) booking from BS
            cBookingCheckInDate = datetime.datetime.strptime(cBooking['start_at'], '%Y-%m-%dT%H:%M:%SZ').date()
            cBookingCheckOutDate = datetime.datetime.strptime(cBooking['end_at'], '%Y-%m-%dT%H:%M:%SZ').date()
            if currBooking.checkInDate.date() == cBookingCheckInDate and currBooking.checkOutDate.date() == cBookingCheckOutDate:
                thisBookingExists = True
                break
        return {'booking' : cBooking, 'exists' : thisBookingExists}
    #        return thisBookingExists

class BSGuest(object):
    def __init__(self):
        self.account_id = None
        self.id = None
        self.created_at = None
        self.update_at = None
        self.address1 = None
        self.address2 = None
        self.city = None
        self.country_code = None
        self.state = None
        self.zip = None
        self.email = None
        self.fax = None
        self.fullname = None
        self.mobile = None
        self.phone = None
        self.notes = None

    def exists(self, emailAddr):
        val = BSAPI.API().clients.get(query=emailAddr)
        if len(val) == 0:
            return {'exists' : False, 'id' : -1 }
        else:
            return {'exists' : True, 'id' : val[0]['client']['id'] }

    def getID(self, emailAddr):
        val = BSAPI.API().clients.get(query=emailAddr)
        if len(val) > 0:
            return val[0]['client']['id']
        else:
            return -1

    def post(self):
        newGuest = {}
        newGuest['client'] = self.__dict__
        returnVal = BSAPI.API().clients.post(newGuest)
        self.id = returnVal['client']['id']
