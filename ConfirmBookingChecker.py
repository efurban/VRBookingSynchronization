import datetime
import ConfirmationEmailRetriver as confirmations
import send_email_via_gmail as gmail
import Booking as emailBooking
import BookingSync as BS
import vrDB
import sys
import mechanize


reload(sys)
sys.setdefaultencoding("utf8")

numOfDaysLookback_Airbnb = 0
numOfDaysLookback_Wimdu = 0
numOfDaysLookback_bookingCom = 4

SEND_EMAIL = False

Dry = False
FillDBOnly = False

try:
    emailMessage = ""
    aptIDExceptions = vrDB.VRDB().getAptIDMappingExceptions()
    wimduEmails = None
    airbnbEmails = None
    bookingComEmails = None

    if numOfDaysLookback_Airbnb > 0:
        airbnbEmails = confirmations.AirbnbConfirmation()
        airbnbEmails.GetAll(numOfDaysLookback_Airbnb)

    if numOfDaysLookback_Wimdu > 0:
        wimduEmails  = confirmations.WimduConfirmation()
        wimduEmails.GetAll(numOfDaysLookback_Wimdu)

    if numOfDaysLookback_bookingCom > 0:
        bookingComEmails  = confirmations.BookingComConfirmation()
        bookingComEmails.GetAll(numOfDaysLookback_bookingCom)

    allBookingsFromEmails = []
    db = vrDB.VRDB()


    # log into the auth page at booking.com so we don't need to login later when retrieving the booking info
    browser = mechanize.Browser()
    browser.set_handle_robots(False)
    #        browser.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    browser.addheaders = [('User-agent', 'Firefox')]
#        browser.open('https://admin.booking.com/hotel/hoteladmin/?lang=en')
    browser.open('https://admin.booking.com/hotel/hoteladmin/login.html')
    browser.select_form(name="myform")
    browser.form["loginname"] = "536676"
    browser.form["password"] = "nycapt523"
    browser.submit()

    sys.stdout.write("Parsing Booking.com emails")
    if bookingComEmails is not None:
        for eBody in bookingComEmails.emails:
            bcBooking = emailBooking.Booking()  # can be any booking (Airbnb, wimdu...etc)
            try:
                bcBooking.parseBookingFromBookingComEmail(eBody)  # confirmed booking from Airbnb, could be new or existing
    #            if bcBooking.price == 0:
    #                continue  # when price = 0 from booking.com, that 's a cancellation
                allBookingsFromEmails.append(bcBooking)
                sys.stdout.write(".")
            except Exception, e:
                print 'something is wrong', e
                continue
    sys.stdout.write("[DONE]\n")


    sys.stdout.write("Parsing Wimdu emails")
    if wimduEmails is not None:
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
    if airbnbEmails is not None:
        for emailBody in airbnbEmails.emails:
            abBooking = emailBooking.Booking()  # can be any booking (Airbnb, wimdu...etc)
            try:
                abBooking.parseBookingFromAirbnbEmail(emailBody)  # confirmed booking from Airbnb, could be new or existing
                allBookingsFromEmails.append(abBooking)
                sys.stdout.write(".")
            except Exception, e:
                print 'something is wrong', e
                continue
    sys.stdout.write("[DONE]\n")



    # special apt ID mapping case
    for em in allBookingsFromEmails:
        if not str.isdigit(str(em.aptNum)):
            for map in aptIDExceptions:
                if str(em.aptName).strip() in str(map['apt_name']).strip():
                    em.aptNum = map['apt_id']
                    continue



    sys.stdout.write("[DONE]\n")

    sys.stdout.write("Adding booking records to DB\n")
    # adding all bookings for our own db;
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

        if currEmailBooking.price == 0:  # should go delete the booking here.
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
        if currEmailBooking.checkOutDate.date() <= today:
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
            emailMessage = emailMessage + "\nBooked from: %s\nApt # = %s\nStartDate = %s\nEndDate = %s\nName = %s\nPrice = %s\n\nEmail = %s\nBooking # = %s\n\n" \
                           % (currEmailBooking.bookingSource,
                              currEmailBooking.aptNum,
                              str(currEmailBooking.checkInDate),
                              str(currEmailBooking.checkOutDate),
                              currEmailBooking.guestName,  # if has utf code this breaks. need to fix
                              str(currEmailBooking.price),
                              currEmailBooking.email,
                              str(currEmailBooking.confirmationCode)
                )
            emailMessage = emailMessage.encode('utf-8')
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

    if emailMessage.__len__() > 0 and SEND_EMAIL:
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




