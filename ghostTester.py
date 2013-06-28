__author__ = 'urban'
from selenium import webdriver
from BeautifulSoup import BeautifulSoup


driver = webdriver.PhantomJS('/Users/urban/Downloads/phantomjs-1.9.1-macosx/bin/phantomjs')
driver.set_window_size(1024, 768) # optional

# has cc
#https://admin.booking.com/hotel/hoteladmin/bookings/booking.html?hotel_id=536676;bn=290921603;ses=1fc072ac73fdeb471d6a725e5dbbffc3

# no cc
#https://admin.booking.com/hotel/hoteladmin/bookings/booking.html?hotel_id=536676;bn=413462216;ses=917d05f85ac757728857a8aa252b6acb

driver.get('https://admin.booking.com/hotel/hoteladmin/bookings/booking.html?hotel_id=536676;bn=290921603;ses=1fc072ac73fdeb471d6a725e5dbbffc3')
err = driver.find_element_by_class_name('error')
if err.text == u'Please login again, your session has expired':
    driver.find_element_by_name('loginname').send_keys('536676')
    driver.find_element_by_name('password').send_keys('nycapt523')
    driver.find_element_by_name("login").click()

# from here, we have a. has user name , password and login b. nothing
try:
    driver.find_element_by_name('loginname').send_keys('536676')
    driver.find_element_by_name('password').send_keys('nycapt523')
    driver.find_element_by_name("login").click()
except Exception, e:
    pass

confirmationPage = driver.page_source

# soup it
soup = BeautifulSoup(repr(confirmationPage))
allItems = soup.findAll('td', {'colspan'} )
allTDs = filter(lambda x: x.attrs == {}, allItems)

driver.save_screenshot('screen.png') # save a screenshot to disk




