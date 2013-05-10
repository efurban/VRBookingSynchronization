__author__ = 'urban'
import BookingSync as BS
import datetime

bsObj = BS.BSHelper()
bsObj.load()
convertedBSBookingObj = BS.BSBooking()

for booking in bsObj.allBookings:
    cBooking = booking['booking']  # current (matched) booking from BS
    convertedBSBookingObj.copyFrom(cBooking)

    cBookingCheckInDate = datetime.datetime.strptime(cBooking['start_at'], '%Y-%m-%dT%H:%M:%SZ').date()
    print cBookingCheckInDate