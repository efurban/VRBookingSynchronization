__author__ = 'urban'

import BookingSync as BS
import datetime
import ConfirmationEmailRetriver as confirmations
import sys
import re
import vrDB
import send_email_via_gmail as gmail
import email


## twu: find all check in detail emails and sync the sent status in db (webfaction)


## test: find all

#bsObj = BS.BSHelper()
#bsObj.load()
#convertedBSBookingObj = BS.BSBooking()

db = vrDB.VRDB()

# send out check in detail emails
checkinDetailsToBeSentList = vrDB.VRDB().getCheckinEmaiStatuslList() # get list of bookings that need to send check in details
for rec in checkinDetailsToBeSentList:
#    print rec['confirmationCode'] + ' ' + rec['email'] + ' ' + rec['apt_id']
    try:
        aptNum = rec[1]
        bookingID = rec[0]
        subject = "Thank you for your booking (%s): Details" % bookingID
        toAddr = rec[2]
        checkinDate = str(rec[5])
        emailBody = "Thanks for your booking. Here is the check in detail. Please let us know if you have any questions.\n\n Apt ID: %s\n\n%s" % (aptNum, rec[6])
        print "Sending confirmation email: Apt = %s, id = %s, email = %s, checkinDate = %s" % (aptNum, bookingID, toAddr, checkinDate)
        gmail.mail_via_va(toAddr, subject, emailBody, "")
    except Exception, e:
        print e.message
        pass






# update sent status in database, per the sent email box from gmail
# get all check in detail emails from sent mail, and sync it to db booking_status
bookingComCheckinEmails = confirmations.BookingComCheckInSent()
bookingComCheckinEmails.GetAll(100)

sys.stdout.write("Parsing Booking.com check in detail emails")

if bookingComCheckinEmails is not None:
    for eBody in bookingComCheckinEmails.emails:
        try:
            _email = email.message_from_string(eBody)
            #        print _email['subject'].split("(")[1].split(")")
            confirmationCode = '#' + re.findall(r'\d+', _email['subject'])[0]
            isSent = db.confirmationAlreadySent(confirmationCode)
            sys.stdout.write(".") # just so we know it's progressing
            if isSent is not None and not isSent:
                db.insertUpdate_checkInEmail_status(confirmationCode)  # update status in db
                print "newly sent: " + confirmationCode
        except Exception, e:
            print e.message

sys.stdout.write("[DONE]\n")



#
#
#for booking in bsObj.allBookings:
#    cBooking = booking['booking']  # current (matched) booking from BS
#    convertedBSBookingObj.copyFrom(cBooking)
#
#    cBookingCheckInDate = datetime.datetime.strptime(cBooking['start_at'], '%Y-%m-%dT%H:%M:%SZ').date()
#    print cBookingCheckInDate
#
