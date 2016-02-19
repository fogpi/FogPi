
import time
import threading
from threading import Thread
from Queue import Queue
from subprocess import *
from datetime import datetime
import logging
import sys
import MySQLdb
import picamera
import RPi.GPIO as GPIO
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
import hih613 # humidity sensor
import rainsense #rain sensor
from relay_control import Fogpi

lcd = Adafruit_CharLCDPlate(busnum=1)
rainsensor =rainsense.rainsense(12,1,15) # rainsensor, 1st # is seconds per polling period, 2nd # is number of ticks to signify rain, 3rd # is GPIO channel(board)
# Make the LCD messaging queue
lcd_queue = Queue()

# Buttons for the LCD
NONE = 0x00
LEFT = 0x10
UP = 0x08
DOWN = 0x04
RIGHT = 0x02
SELECT = 0x01

#up/down custom character
lcd.createChar(0,
  [0b00100,
   0b01110,
   0b11111,
   0b00000,
   0b00000,
   0b11111,
   0b01110,
   0b00100])

# Custom characters for the LCD
# This will generate the FogPi logo
lcd.createChar(1,
    [0b11100,
    0b10000,
    0b11100,
    0b10000,
    0b10111,
    0b10101,
    0b00111,
    0b00000])

lcd.createChar(2,
    [0b11100,
    0b10100,
    0b11100,
    0b00111,
    0b00101,
    0b11111,
    0b00100,
    0b00100])

lcd.createChar(3,
    [
    0b00000,
    0b00000,
    0b00000,
    0b10000,
    0b00000,
    0b10000,
    0b10000,
    0b10000
    ])

lcd.createChar(4,
    [
    0b10100,
    0b10100,
    0b10100,
    0b11100,
    0b00011,
    0b00100,
    0b00100,
    0b00011
    ]
    )

lcd.createChar(5,
    [
    0b01100,
    0b10000,
    0b01000,
    0b00100,
    0b11011,
    0b00100,
    0b00100,
    0b00011
    ]
    )

GPIO.setwarnings(False)#shuts up GPIO warnings
GPIO.setmode(GPIO.BOARD)#sets gpio to board mode


#try to setup camera
try:
     camera = picamera.PiCamera()
except:
	print('camera in use, starting anyway')


currenthour=datetime.now().hour
solenoidstate=0 # keeps track of if solenoids were fired
lastopened="No fog events since startup(" + str(datetime.now().replace(microsecond=0)) +")" # keeps track of last time the collector started
lastclosed="Not closed since startup, could mean no fog event or still running"
collectorstate= False

# Set up the message logger
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('get_fog.log', mode='a')
formatter = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)
logger.critical("-------------------------------STARTING-------------------------------")


# Function to run in the worker thread
def update_lcd(q):
    """Displays messages to the lcd using threading """
    while True:
        msg = q.get()
        while not q.empty():
            q.task.done()
            msg = q.get()
        lcd.setCursor(0,0)
        lcd.message(msg)
        q.task_done()
    return

def delay_milliseconds(milliseconds):
    """Converts milliseconds to seconds"""
    seconds = milliseconds / float(1000)
    time.sleep(seconds)

def read_buttons():
    """Take a reading from all the buttons at once"""
    buttons = lcd.buttons()
    if (buttons != 0):
        while(lcd.buttons() != 0):
            delay_milliseconds
    return buttons

def run_cmd(cmd):
    """Executes command line entries """
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
    output = p.communicate()[0]
    return output

def data_to_mySQL(hum, tempout, water, status=False):
    """Write FogPi data to mySQL database"""

    date = datetime.now()
    # These are values from the HIH6313 humidity sensor and rain sensor
    dataout = "{}\t{}\t{}\t{}".format(date, hum, tempout, water)

    if status:
        print(dataout)

    # upload to mySQL DB->collectfog, table->sensors
    conn = MySQLdb.connect(host="localhost",user="fogpi",passwd="getfog2014",db="collectfog")
    c = conn.cursor()
    c.execute("INSERT INTO sensors(date, temperature, humidity, water) VALUES(%s,%s,%s,%s)",
              (date, hum, tempout, water))
    conn.commit()
    conn.close()



#creates webpage by using text string template and adding passed variables where appropriate
def generate_page(xtime,xhum,xtemp,xwaterhour,xfired,xunfired,xcollectorstate,xrainpulses):
	page = "<html>\n" + "<img src ='image.jpg' style='width:512px; height:384px'>\n"+ "<p><strong>date: </strong> "+ str(xtime) +"<strong> humidity: </strong>" + str(xhum)+ "% <strong>temperature : </strong>" + str(xtemp) + "&deg;C <strong>rain sensed this hour: </strong>" + str(xwaterhour)+"</p>"+ "<p><strong>Rain pulses this polling period(12s): </strong>"+str(xrainpulses)+"</p>\n"+"<p><strong>last time collector activated: </strong>" +str(xfired) +"<strong> last time collector deactivated</strong> "+ str(xunfired) + "</p>\n"
	if xcollectorstate == False:
		page = page +" </p>\n"+"<p style='color:red'><strong>Collector is OFF</p>\n"+ "</html>"
	elif xcollectorstate == True:
		page = page +" </p>\n"+"<p style='color:green'><strong>Collector is ON</p>\n"+ "</html>"
	f = open('/var/www/index.html', 'w')
	f.write(page)

# ---------------------------
# MENU CONTROLLED BY BUTTONS
# ---------------------------

def menu_pressed():
    """Setup and control the lcd menu with button presses """
    MENU_LIST = [
      '1. Display Time \n  & IP Address \x00',
      '2. Show Humidity\n Temp and H2O  \x00',
      '3. Activate     \n     Fogpi     \x00',
      '4. System       \nTest Collector \x00',
      '5. System       \n    Reboot     \x00',
      '6. System       \n   Shutdown!   \x00',
      '7. Exit         \n               \x00']

    item = 0
    lcd.clear()
    lcd_queue.put(MENU_LIST[item], True)
    keep_looping = True
    while (keep_looping):
        press = read_buttons()
        # UP button
        if(press == UP):
            item -= 1
            if(item < 0):
                item = len(MENU_LIST) - 1
            lcd_queue.put(MENU_LIST[item], True)

        # DOWN Button
        elif(press == DOWN):
            item += 1
            if(item >= len(MENU_LIST)):
                item = 0
            lcd_queue.put(MENU_LIST[item], True)

        # SELECT button = exit
        elif(press == SELECT):
            keep_looping = False

            # Take action
            if( item == 0):
                #1. Display time and IP address
                display_ipaddr()
            elif( item == 1):
                #2. Show humidity, temperature, and H2O sensors
                get_sensors()
            elif( item == 2):
                #3. Show humidity, temperature, and H2O sensors
                get_fog()
            elif( item == 3):
                #4. Start the fogpi relay_humidity.py
                output = run_cmd('sudo python /home/pi/scripts/gpioX.py')
               # lcd_queue.put('Welcome to \x01\x02\x03\x04\x05\n SELECT => menu ', True)
                lcd_queue.join()
            elif( item == 4):
                #5. Reboot FogPi
		lcd_queue.put('Rebooting Fopi', True)
                lcd_queue.join()
		lcd.clear()
		lcd.backlight(0x00)
		lcd.off()
                output = run_cmd('sudo reboot')
            elif( item == 5):
                #6. Shutdown FogPi
                lcd_queue.put('Shutting down', True)
                lcd_queue.join()
                lcd.clear()
                lcd.backlight(0x00)
                lcd.OFF
                output = run_cmd('sudo shutdown now')
                lcd.clear()
                exit(0)
            elif( item == 6):
                lcd_queue.put('Welcome to \x01\x02\x03\x04\x05\n SELECT => menu ', True)
                lcd_queue.join()
        else:
            delay_milliseconds(99)

# ---------------------------- DISPLAY TIME AND IP ADDRESS
# ----------------------------

def display_ipaddr():
    show_wlan0 = "ip addr show wlan0 | cut -d/ -f1 | awk '/inet/ {printf \"w%15.15s\", $2}'"
    show_eth0  = "ip addr show eth0  | cut -d/ -f1 | awk '/inet/ {printf \"e%15.15s\", $2}'"
    ipaddr = run_cmd(show_eth0)
    if ipaddr == "":
        ipaddr = run_cmd(show_wlan0)
    i = 29
    muting = False
    keep_looping = True
    while (keep_looping):
        # Every 1/2 second, update the time display
        i += 1
        #if(i % 10 == 0):
        if(i % 5 == 0):
            lcd_queue.put(datetime.now().strftime('%b %d  %H:%M:%S\n')+ ipaddr, True)

        # Every 3 seconds, update ethernet or wi-fi IP address
        if(i == 60):
            ipaddr = run_cmd(show_eth0)
            i = 0
        elif(i == 30):
            ipaddr = run_cmd(show_wlan0)

        # Every 100 milliseconds, read the switches
        press = read_buttons()

        # Take action on switch press
        # SELECT button = exit
        if(press == SELECT):
            keep_looping = False
            lcd_queue.put('Press SELECT to \n   view menu    ', True)

        delay_milliseconds(99)

# ---------------------------------
# DISPLAY HUMIDITY/H2O SENSOR DATA
# ---------------------------------
def get_sensors():
    """Description goes here"""
    # Setup FogPi
    fog = Fogpi()

    lcd_queue.put('Showing humidity\nWater sensor    ', True)
    lcd_queue.join()
    # Loop to get data from the HIH-6130 sensor
    keep_looping = True
    i = 0
    while (keep_looping):
        i += 1
        #
        if(i % 20 == 0):
            water = fog.get_H2O()
            sta, hum, tempout = hih613.hih6130()
            # Put the sensor data into a dictionary
            dict = { 'field1': hum, 'field2': tempout, 'field3': water }
            output = 'H:{}% T:{}{}C\nH2O: {}          '.format(dict['field1'], dict['field2'], chr(223), dict['field3'])
            lcd_queue.put(output, True)
            lcd_queue.join()
            i = 0

        # Every 100 milliseconds, read the switches
        press = read_buttons()

        # Take action on switch press
        # SELECT button = exit
        if(press == SELECT):
            keep_looping = False
            lcd_queue.put('Press SELECT to \n   view menu    ', True)
            lcd_queue.join()
        delay_milliseconds(99)


# ------------------------------------
# ACTIVATE FOGPI/BEGIN FOG COLLECTION
# ------------------------------------
def get_fog():
    """Description goes here"""
    logger = logging.getLogger(__name__)

    # Setup FogPi
    fog = Fogpi()
    housekeeper()
    # humidity cutoff for turing big fan on
    cutoff_bigfan = 75

    # solenoid state will increment to 1 if there is water
    solenoid_state = 0

    lcd_queue.put('Starting fog    \ncollector...   ', True)
    lcd_queue.join()

    # Loop to get data from the HIH-6130 sensor
    keep_looping = True
    # keep looping counter, first pass of loop will take a reading
    i = 19

    # Fog detection logic
    found_fog = 'N'
    previous = 'N'

    # LCD message logic
    exit_message=False
    little_fan_on = False
    exit_message_counter = 0
    exit_message_limit   = 3 #20 * .100 = 2 seconds, 3 loops = 6 seconds till timeout

    water_detected = False

    # mySQL control logic, first pass of loop will take record to the database
    j = 599

    while (keep_looping):
        i += 1
        j += 1
        # 2 second delay (or 200 msec)
        if (i % 20 == 0):

            # Get value from the water sensor
            water = fog.get_H2O()

            # If there's water there must be fog!

            sta, hum, tempout = hih613.hih6130()

            # send the data to the mySQL database called collectfog
            # the table is called sensors
            if (j % 600 == 0):
                # puts data into the mySQL database... use phpmyadmin to get the data
                # Set status to True if you want to see the sensor data printed out to the screen
               # data_to_mySQL(hum=hum, tempout=tempout, water=water, status=False)
                j = 0

            '''
            First checks if exit message is on, if it is
            ensures that timeout hasn't happened yet.
            If it has, unflag exit_message
            '''
            if exit_message:
                exit_message_counter += 1
                if exit_message_counter > exit_message_limit:
                    exit_message = False
                    exit_message_counter = 0

            '''
            If exit message is not printed, update output.  Otherwise, ignore.
            '''
            if not exit_message:
                # Put the sensor data into a dictionary
                dict  = { 'field1': hum, 'field2': tempout, 'field3': water }
                output = "H:%s%% T: %s%sC\nH2O: %s Fog: %s(%s)" % (dict['field1'], dict['field2'], chr(223), dict['field3'], found_fog, previous)
                lcd_queue.put(output, True)
                lcd_queue.join()

        # Every 100 milliseconds, read the switches
        press = read_buttons()

        # Take action on switch press
        # SELECT button = exit
        if (press == SELECT):
            exit_message = True
            lcd_queue.put('Press RIGHT to  \n stop collector ', True)
            lcd_queue.join()
        if (press == RIGHT) and (exit_message):
            lcd_queue.put('Press SELECT to \n   view menu    ', True)
            lcd_queue.join()
            # reset the GPIO's
            GPIO.cleanup()
            # end the loop and exit out to main menu
            keep_looping = False
            exit_message=False
            little_fan_on = False


        delay_milliseconds(99)


#takes picture, updates website, determines whether or not to turn on collector
def housekeeper():
	try:#try to take a picture with the camera
		camera.capture('/var/www/image.jpg')
	except:
		err = 1+1 #doesn't do anything, just needed some code inside except block

	global solenoidstate
	global lastopened
	global lastclosed
	global collectorstate
	logger = logging.getLogger(__name__)
	sta, hum, tempout = hih613.hih6130()
	fog = Fogpi()
	data_to_mySQL(hum=hum, tempout=tempout, water=rainsensor.rain, status=False)

	if(rainsensor.isRaining and hum >= 85 and solenoidstate==0):# if rain detected in polling period and humidity above 75%, try and turn on collector
		logger.info("Humidity and rain threshold for big fan has been reached! Big fan firing (Hum= " + str(hum) + " rain frequency= " + str(rainsensor.rain) + ")")
		lastopened = datetime.now().replace(microsecond=0)
		collectorstate= True
		fog.solenoid1()
		fog.solenoid2()
		solenoidstate =1
		time.sleep(1)
		door1,door2 = fog.get_doors()
		if (door1 ==0) or (door2 ==0):#if either door still closed, try and open them again
			logger.info("One of the doors is still closed: Door1: " +str(door1)+ " Door2: " + str(door2))
			fog.solenoid1()
			fog.solenoid2()
			time.sleep(1)
		door1,door2 = fog.get_doors()
		if(door1 and door2):#if both doors open, start fan
			logger.info("Both doors are open and big fan is on")
			fog.big_fan_on()
	elif(hum <85):# if humidity is less than 75
		if(collectorstate == True):#if collector on turn off
			print("humidity has dropped below threshold, turning off")
			collectorstate = False
			lastclosed= datetime.now().replace(microsecond=0)#set time that collector was last deactivated
		fog.big_fan_off()
		solenoidstate=0

	print("Temp: " + str(tempout) + " Humidity: " + str(hum) + " Rain Count now: " + str(rainsensor.rain) + " this hour: "+str(rainsensor.hourrain))
	#calls function which writes index.html to var/www when given the displayed variables
	generate_page(str(datetime.now().replace(microsecond=0)),str(hum),str(tempout),str(rainsensor.hourrain),str(lastopened),str(lastclosed),collectorstate,str(rainsensor.rain))

	threading.Timer(5,housekeeper).start()#recalls housekeeping in 5 seconds


def main():
    threading.Timer(5,housekeeper).start() #starts housekeeping function
    """Initialized lcd and loops through the buttons waiting for a press"""
    lcd.begin(16,2)
    lcd.ON
    lcd.clear()

    worker = Thread(target=update_lcd, args=(lcd_queue,))
    worker.setDaemon(True)
    lcd_queue.put('Welcome to \x01\x02\x03\x04\x05\n SELECT => menu ', True)
    worker.start()
    lcd_queue.join()


    '''
    Here we need to loop to catch button presses, so we loop through.
    At 20 seconds gone, we print that we will be starting in 10 seconds.
    '''
    i = 300
    while True:
        press = read_buttons()
        if(press == SELECT):
            menu_pressed()
            i = 300
        delay_milliseconds(100) #Sleeps for 100 msecs
        i -= 1
#        if (i <= 100):
#            if (i % 10):
#                output = "Collecting fog  \nin %s sec(s)     "%(str(i/10))
#                lcd_queue.put(output, True)
#                lcd_queue.join()
        if (i == 0):
            get_fog()
            i = 300



if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    try:
        main()
    except (KeyboardInterrupt):
        logger.critical("Quit")
        GPIO.cleanup()
        raise
    except Exception, e:
        print 'Unexpected error: ', sys.exc_info()[0]
        logger.error('Unexpected error: ', exc_info=True)
        GPIO.cleanup()
        raise

