import datetime
import ConfirmationEmailRetriver as confirmations
import send_email_via_gmail as gmail
import Booking as emailBooking
import BookingSync as BS
import vrDB
import sys


import sys
reload(sys)
sys.setdefaultencoding("utf8")


numOfDaysLookback_Airbnb = 10
numOfDaysLookback_Wimdu = 2
Dry = False
FillDBOnly = False

try:
    emailMessage = ""
    aptIDExceptions = vrDB.VRDB().getAptIDMappingExceptions()

    airbnbEmails = confirmations.AirbnbConfirmation()
    airbnbEmails.GetAll(numOfDaysLookback_Airbnb)

    wimduEmails  = confirmations.WimduConfirmation()
    wimduEmails.GetAll(numOfDaysLookback_Wimdu)

    allBookingsFromEmails = []
    db = vrDB.VRDB()

    sys.stdout.write("Parsing Wimdu emails")
    for eBody in wimduEmails.emails:
        wBooking = emailBooking.Booking()  # can be any booking (Airbnb, wimdu...etc)
        try:
            wBooking.parseBookingFromWimduEmail(eBody)  # confirmed booking from Airbnb, could be new or existing
            allBookingsFromEmails.append(wBooking)
            sys.stdout.write(".")
        except Exception, e:
            print 'something is wrong', e
            continue
    sys.stdout.write("[DONE]\n")

    sys.stdout.write("Parsing Airbnb emails")
    for emailBody in airbnbEmails.emails:
        abBooking = emailBooking.Booking()  # can be any booking (Airbnb, wimdu...etc)
        try:
            abBooking.parseBookingFromAirbnbEmail(emailBody)  # confirmed booking from Airbnb, could be new or existing
            allBookingsFromEmails.append(abBooking)
            sys.stdout.write(".")
        except Exception, e:
            print 'something is wrong', e
            continue

    # special apt ID mapping case
    for em in allBookingsFromEmails:
        if not str.isdigit(str(em.aptNum)):
            for map in aptIDExceptions:
                if str(em.aptName).strip() in str(map['apt_name']).strip():
                    em.aptNum = map['apt_id']
                    continue



    sys.stdout.write("[DONE]\n")

    sys.stdout.write("Adding booking records to DB\n")
    # adding all bookings for our own db
    for currEmailBooking in allBookingsFromEmails:
        print currEmailBooking.bookingSource, currEmailBooking.confirmationCode
        print currEmailBooking.aptNum, currEmailBooking.checkInDate, str(currEmailBooking.checkOutDate)
        db.insertUpdate(currEmailBooking)

    sys.stdout.write("\n[DONE]\n\n")

#
#        """, ("snake", "turtle"))
    if FillDBOnly:
        sys.exit(0)

    for currEmailBooking in allBookingsFromEmails:
        if not str.isdigit(str( currEmailBooking.aptNum)):
            continue

        currBSBooking = BS.BSBooking()  # BookingSync booking item

        # if this confirmation is for existing booking, populate currBSBooking
        print currEmailBooking.bookingSource, currEmailBooking.guestName, currEmailBooking.confirmationCode
        print currEmailBooking.aptNum, currEmailBooking.checkInDate, currEmailBooking.checkOutDate

        guest = BS.BSGuest()

        currentGuestExists =  False
        if (currEmailBooking.email is not None):

            guestObj = guest.exists(currEmailBooking.email)
            if guestObj['exists']:
                guest.id = guestObj['id']
                currentGuestExists = True
                print 'old guests , id = ' + str(guest.id)
            else:
                guest.fullname = currEmailBooking.guestName
                guest.email = currEmailBooking.email
                guest.post()
                print 'new guests, id = ' + str(guest.id)

        # need to put this back
        today = datetime.date.today()
        if currEmailBooking.checkOutDate.date() < today:
            continue

        currBSBookingObj = currBSBooking.exists(currEmailBooking)
        if currBSBookingObj['exists']:
            somethingModified = False
            # update the final price and guest count
            currBSBooking.copyFrom(currBSBookingObj['booking'])
            if currBSBooking.final_price is None:
                print 'missing final price, updating...'
                emailMessage = emailMessage + '\nmissing final price, updating...'
                currBSBooking.final_price = currEmailBooking.price
                somethingModified = True
            if currBSBooking.adults is None:
                print 'missing guest count, updating...'
                emailMessage = emailMessage + '\nmissing guest count, updating...'
                currBSBooking.adults = currEmailBooking.guestCount
                somethingModified = True
            if currBSBooking.client_id is None and guest.id is not None:
                currBSBooking.client_id = guest.id
                somethingModified = True
                print 'missing guest info, updating'
                emailMessage = emailMessage + '\nmissing guest info, updating'

            # conver the date to the format that BS understands
            if somethingModified:
                if not Dry:
                    currBSBooking.update()
                else:
                    print 'Dry run: update booking'
        else:
            print 'creating BS booking...'
            currBSBooking.popuateFromBooking(currEmailBooking)
            emailMessage = emailMessage + "\nBooked from: %s\nApt # = %s\nStartDate = %s\nEndDate = %s\nName = %s\nPrice = %s\n" % (currEmailBooking.bookingSource, currEmailBooking.aptNum, str(currEmailBooking.checkInDate), str(currEmailBooking.checkOutDate), currEmailBooking.guestName, str(currEmailBooking.price))
            if guest.id is not None:
                currBSBooking.client_id = guest.id
            try:
                if not Dry:
                    currBSBooking.post()

                else:
                    print 'Dry run: post/create booking'
            except Exception, e:
                print e.content
                emailMessage = emailMessage + e.content
                pass

    if emailMessage.__len__() > 0:
        gmail.mail(", ".join(["traviswu@gmail.com","cwjacklin@gmail.com"]),
            "new bookings",
            emailMessage,
            "")
#    else:
#        gmail.mail(", ".join(["traviswu@gmail.com","cwjacklin@gmail.com"]),
#            "No new bookings",
#            emailMessage,
#            "")

except Exception, e:
    print e




