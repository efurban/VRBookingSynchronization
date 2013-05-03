__author__ = 'urban'


import datetime

import ConfirmationEmailRetriver as confirmations
import send_email_via_gmail as gmail
import Booking as emailBooking
import BookingSync as BS
import vrDB
import sys

reload(sys);
sys.setdefaultencoding("utf8")

numOfDaysLookback_Airbnb = 10
numOfDaysLookback_Wimdu = 10
Dry = False
FillDBOnly = False

try:

    allBookingsFromEmails = []

    emailMessage = ""

    airbnbEmails = confirmations.AirbnbConfirmation()
    airbnbEmails.GetAll(numOfDaysLookback_Airbnb)
    sys.stdout.write("Parsing Airbnb emails")
    counter = 0
    for emailBody in airbnbEmails.emails:
        abBooking = emailBooking.Booking()  # can be any booking (Airbnb, wimdu...etc)
        try:
            abBooking.parseBookingFromAirbnbEmail(emailBody)  # confirmed booking from Airbnb, could be new or existing
            allBookingsFromEmails.append(abBooking)
            counter += 1
            sys.stdout.write(".")
            if counter % 20 == 0:
                sys.stdout.write(str(counter))
            if counter % 100 == 0:
                sys.stdout.write('\n')

        except Exception, e:
            print 'something is wrong:', e
            continue
    sys.stdout.write("[DONE]\n")




    wimduEmails  = confirmations.WimduConfirmation()
    wimduEmails.GetAll(numOfDaysLookback_Wimdu)

    db = vrDB.VRDB()

    sys.stdout.write("Parsing Wimdu emails")
    for eBody in wimduEmails.emails:
        wBooking = emailBooking.Booking()  # can be any booking (Airbnb, wimdu...etc)
        try:
            wBooking.parseBookingFromWimduEmail(eBody)  # confirmed booking from Airbnb, could be new or existing
#            if str(wBooking.aptNum).isdigit():
            allBookingsFromEmails.append(wBooking)
            sys.stdout.write(".")
        except Exception, e:
            print 'something is wrong', e
            continue
    sys.stdout.write("[DONE]\n")





    sys.stdout.write("Adding booking records to DB\n")
    # adding all bookings for our own db
    for currEmailBooking in allBookingsFromEmails:

        # special cases: a. name changes, b. special bookings
        if currEmailBooking.aptNum == 'A LOVELY BEDROOM IN VIEUX-LYON':  # jack's vacation booking
            continue
        if currEmailBooking.aptNum =='Cozy modern Apt in midtown chez moi':
            currEmailBooking.aptNum = 'james'
        if currEmailBooking.aptNum == 'Cozy studio, can see Time Square':
            currEmailBooking.aptNum = '9'
        if currEmailBooking.aptNum == 'Huge studio with Big windows':
            currEmailBooking.aptNum = '8'
        if currEmailBooking.aptNum == 'Large quiet studio Theatre district':
            currEmailBooking.aptNum = '5'
        if currEmailBooking.aptNum == 'Quiet huge paradise studio' or currEmailBooking.aptNum == 'Shared huge quiet paradise studio 6':
            currEmailBooking.aptNum = '6'

        print currEmailBooking.bookingSource, currEmailBooking.confirmationCode
        print currEmailBooking.aptNum, currEmailBooking.checkInDate, str(currEmailBooking.checkOutDate)
        db.insertUpdate(currEmailBooking)

    sys.stdout.write("\n[DONE]\n\n")
except Exception, e:
    print e


