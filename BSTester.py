__author__ = 'urban'
import BookingSync as BS
import datetime

bsObj = BS.BSHelper()
bsObj.load()

for booking in bsObj.allBookings:
    print booking['rental']['id']
    cBooking = booking['booking']  # current (matched) booking from BS
    cBookingCheckInDate = datetime.datetime.strptime(cBooking['start_at'], '%Y-%m-%dT%H:%M:%SZ').date()
    print cBookingCheckInDate