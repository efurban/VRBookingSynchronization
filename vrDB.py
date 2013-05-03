__author__ = 'Travis Wu'

import pymysql
import datetime
#import Booking as emailBooking



class VRDB:
    def __init__(self):
        self.conn = pymysql.connect(host='nycapt.db.7527697.hostedresource.com', port=3306, user='nycapt', passwd='Ktxd1976@', db='nycapt')
        self.dbcur = self.conn.cursor()

    def __close__(self):
        self.dbcur.close()
        self.conn.commit()
        self.conn.close()

    def exists(self, emailBooking):
        sqlcmd = "SELECT (1) FROM booking WHERE apt_id = {0} AND checkin_date = '{1}' AND checkout_date = '{2}'".format(emailBooking.aptNum, emailBooking.checkInDate, emailBooking.checkOutDate)
        result = self.dbcur.execute(sqlcmd)
        return result

    def getAptIDMappingExceptions(self):
        aptMapping = {}
        try:
            self.dbcucr = self.conn.cursor(pymysql.cursors.DictCursor)
            query = "SELECT apt_name, apt_id FROM property_name_mapping"
            self.dbcucr.execute(query)
            aptMapping = self.dbcucr.fetchall()
        except Exception, e:
            print e
            pass
        return aptMapping

    def insertUpdate(self, emailBooking):
        self.conn = pymysql.connect(host='nycapt.db.7527697.hostedresource.com', port=3306, user='nycapt', passwd='Ktxd1976@', db='nycapt')
#        self.dbcur = self.conn.cursor()

        try:
            # a. map the special mapping for apt name / id
            if not str(emailBooking.aptNum).isdigit():
                aptMaps = self.getAptIDMappingExceptions()
                for map in aptMaps:
                    if str(emailBooking.aptNum).strip() in str(map['apt_name']).strip():
                        emailBooking.aptNum = map['apt_id']

            # update the booking
            self.dbcur = self.conn.cursor()
            sqlcmd =  "call pr_insertUpdate_booking(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            checkInDate = pymysql.escape_string(str(datetime.datetime.strftime(emailBooking.checkInDate, '%Y-%m-%d')))
            checkOutDate = pymysql.escape_string(str(datetime.datetime.strftime(emailBooking.checkOutDate, '%Y-%m-%d')))
            bookingDate = pymysql.escape_string(str(emailBooking.bookingDate))

            bookingSource = None
            if emailBooking.bookingSource == "Airbnb":
                bookingSource = 1
            if emailBooking.bookingSource == "Wimdu":
                bookingSource = 2
            sqlcmd = sqlcmd % (pymysql.escape_string(str(emailBooking.aptNum)), checkInDate, checkOutDate, str(emailBooking.price), '0', str(emailBooking.guestCount),
                           pymysql.escape_string(str(bookingSource)), pymysql.escape_string(str(emailBooking.confirmationCode).replace("Confirmation Code: ", "")),'0', pymysql.escape_string(''),
                            bookingDate)
#            print sqlcmd

            self.dbcur.execute(sqlcmd)
            self.conn.commit()
        except Exception, e:
            print e
            pass
