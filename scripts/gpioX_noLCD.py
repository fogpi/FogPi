import RPi.GPIO as GPIO
import time
import sys
import hih613
from threading import Thread
from Queue import Queue

# Use physical pin numbers
GPIO.setmode(GPIO.BOARD)

# pin 1  = 3.3V     pin 2  = 5 V
# pin 3  = I2C SDA  pin 3  =
# pin 5  = I2C SCL  pin 6  = Ground
# pin 7  = GPIO4    pin 8  =
# pin 11 = GPIO17   pin 12 = GPIO18
# pin 13 = GPIO21   pin 14 =
# pin 15 = GPIO22   pin 16 = GPIO23
# pin 17            pin 18 = GPIO24
# pin 19            pin 22 = GPIO25

# Set up header pins as an input with off state
# bigfan is the beefcake relay from Sparkfun, GPIO.LOW turns it off.
# The other pins run on the 8-channel relay, GPIO.HIGH turns them off
pins = dict(bigfan=[7, GPIO.LOW],
            solenoid1=[12, GPIO.HIGH ],
            solenoid2=[13, GPIO.HIGH ],
            smallfan=[ 11, GPIO.HIGH ] )

# Make methods to turn relays on/off
def solenoid1():
    GPIO.output(pins['solenoid1'][0], GPIO.LOW)
    print('Solenoid1 on')
    time.sleep(3)
    GPIO.output(pins['solenoid1'][0], GPIO.HIGH)
    print('Solenoid1 off')

def solenoid2():
    GPIO.output(pins['solenoid2'][0], GPIO.LOW)
    print('Solenoid2 on')
    time.sleep(3)
    GPIO.output(pins['solenoid2'][0], GPIO.HIGH)
    print('Solenoid2 off')

def small_fan_on():
    GPIO.output(pins['smallfan'][0], GPIO.LOW)
    print('Small fan is on')

def small_fan_off():
    GPIO.output(pins['smallfan'][0], GPIO.HIGH)
    print('Small fan is off')

def big_fan_on():
    GPIO.output(pins['bigfan'][0], GPIO.HIGH)
    print('Big fan is on')

def big_fan_off():
    GPIO.output(pins['bigfan'][0], GPIO.LOW)
    print('Big fan is off')

# ----------------------------  
# WORKER THREAD  
# ----------------------------  
  
# Define a function to run in the worker thread  

if __name__ == '__main__':
    
    print('Initializing GPIOs')
    for key, items in pins.iteritems():
        GPIO.setup(items[0], GPIO.OUT)
        GPIO.output(items[0], items[1])
        print('\t{} on pin {}'.format(key, items))
    time.sleep(1)
    while True:
        try:
            small_fan_on()
            solenoid1()
            solenoid2()
            big_fan_on()
            time.sleep(7)
            big_fan_off()
            small_fan_off()
        except (KeyboardInterrupt):
            print("Quit")
            GPIO.cleanup()
        except:
            print 'Unexpected error: ', sys.exc_info()[0]
            GPIO.cleanup()
            raise
