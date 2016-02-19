#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import sys
import hih613


##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
#                         RASPBERRY PI FOG COLLECTOR v0.1
#  Code by Chad Saltikov
#  Feel free to modify, change, or scrap code for newer code.
#  Code is not perfect and could likely results in serious damage to electrical equipment
#  as the GPIO's are controlling relays and high amperage fans and solenoids.  Please use
#  proper safety precautions to ensure there are no damages to property or persons. 
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##


class Printer():
    """
    Print things to stdout on one line dynamically
    """
 
    def __init__(self,data):
 
        sys.stdout.write("\r"+data.__str__()+"  ")
        sys.stdout.flush()


## Useful pins and their function ##
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

class Fogpi(object):
    def __init__(self, debug=False):
        # Use physical pin numbers
        GPIO.setmode(GPIO.BOARD)
        self.debug = debug
        # pinouts to the relays
        self.pins = dict(bigfan=[7, GPIO.LOW],
                    solenoid1=[12, GPIO.HIGH ],
                    solenoid2=[13, GPIO.HIGH],
                    smallfan=[ 11, GPIO.HIGH ] )
        # pin for water sensor
       # self.h2o = 22
        # pin for door sensors
        self.door1 = 16
        self.door2 = 18

        if debug: print('Initializing GPIOs')
        # Setup the GPIO pinouts for output controllers
        for key, items in self.pins.iteritems():
            GPIO.setup(items[0], GPIO.OUT)
           # GPIO.output(items[0], items[1])
            if debug: print('\t{} on pin {}'.format(key, items))
	GPIO.output(12,GPIO.HIGH)
	GPIO.output(13,GPIO.HIGH)
	GPIO.output(11,GPIO.HIGH)
        # Setup the GPIO pinouts for input sensing of H20
       # GPIO.setup(self.h2o, GPIO.IN)
       # if debug: print('H2O sensor pin: {}'.format(self.h2o))

        # Setup the GPIO pinouts for input sensing of door switches
        GPIO.setup(self.door1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.door2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        if debug: print('Door1: {} Door2: {}'.format(self.door1, self.door2))

    # Make methods to turn relays on/off
    def solenoid1(self):
        """Activates solenoid1"""
        GPIO.output(self.pins['solenoid1'][0], GPIO.LOW)
        if self.debug: print('Solenoids 1 is on')
        time.sleep(2)
        GPIO.output(self.pins['solenoid1'][0], GPIO.HIGH)
        if self.debug: print('Solenoid 1 is off')

    def solenoid2(self):
        """Activates solenoid2"""
        GPIO.output(self.pins['solenoid2'][0], GPIO.LOW)
        if self.debug: print('Solenoid 2 is on')
        time.sleep(2)
        GPIO.output(self.pins['solenoid2'][0], GPIO.HIGH)
        if self.debug: print('Solenoid 2 is off')

    def small_fan_on(self):
        """Turns the small fan on"""
        GPIO.output(self.pins['smallfan'][0], GPIO.LOW)
        if self.debug: print('Small fan is on')

    def small_fan_off(self):
        """Turns the small fan off"""
        GPIO.output(self.pins['smallfan'][0], GPIO.HIGH)
        if self.debug: print('Small fan is off')

    def big_fan_on(self):
        """Turns the big fan on"""
        GPIO.output(self.pins['bigfan'][0], GPIO.HIGH)
        if self.debug: print('Big fan is on')

    def big_fan_off(self):
        """Turns the big fan off"""
	
        GPIO.output(self.pins['bigfan'][0], GPIO.LOW)
        if self.debug: print('Big fan is off')

    def get_H2O(self):
        """Get the state of the water sensor"""
       # water = GPIO.input(self.h2o)
        if self.debug:
            print(water)
        # a one is positive for water
        return 0

    def get_doors(self):
        """Get the state of the two door sensors """
        doors =  [ GPIO.input(self.door1), GPIO.input(self.door2) ]
        if self.debug:
            print('Door1: {} Door2: {}'.format(doors[0], doors[1]))
        return doors

if __name__ == '__main__':
    # humidity cutoff to turn replay on
    cutoff = 55
    # solenoid state will increment to 1 if there is water
    solenoid_state = 0
    
    Fog = Fogpi(debug=False)
  #  Fog.big_fan_off()
    door1_status = False

    door2_status = False
    door2_message = False

    while True:
        try:
            # Get input from the water sensor
            water = Fog.get_H2O()
            door1, door2 = Fog.get_doors()
            
            # Get data from the HIH-6130 sensor
            sta, hum, tempout = hih613.hih6130()

            dict = { 'field1': hum, 'field2': tempout, 'field3': water }

            output = "Hum: %s, Temp: %s, Water: %s, Door1: %s, Door2: %s" % (dict['field1'], dict['field2'], dict['field3'], door1, door2)
            print(output)

            if not door2_status:
                if not door2_message:
                    if door2:
                        print('Door2 open')
                        door2_message = True
                        door2_status = True

            # turn on small fan if humidity threshold is detected
            if (hum >= cutoff):
                Fog.small_fan_on()
                
            # turn on everything if humidity threshold and water is detected
#            if (hum >= cutoff) and (solenoid_state == 0) and water==1:
#                Fog.solenoid1()
#                Fog.solenoid2()
#                Fog.solenoid_state +=1
#                time.sleep(1)
#                Fog.big_fan_on()
#            elif hum < cutoff and solenoid_state != 0:
#                Fog.big_fan_off()
#                Fog.small_fan_off()
#		 print('turning off collector')
#            time.sleep(2)
        except (KeyboardInterrupt):
            print("Quit")
            GPIO.cleanup()
            raise
        except:
            print 'Unexpected error: ', sys.exc_info()[0]
            GPIO.cleanup()
            raise
    print('Finished')
