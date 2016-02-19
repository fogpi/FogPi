#!/usr/bin/python

import ThingSpeak, time, hih613
import socket, httplib, sys
from datetime import datetime
import RPi.GPIO as GPIO
import time

# Use physical pin numbers
GPIO.setmode(GPIO.BOARD)

# Set up header pin 11 (GPIO17) as an input
i = 7

# humidity cutoff to turn replay on
cutoff = 60

GPIO.setup(i, GPIO.OUT)

# ThingSpeak key:
tskey = 'T3NIRXOPAIZPUD3Z'

# ===========================================================================
# Code
# ===========================================================================

class Printer():
    """
    Print things to stdout on one line dynamically
    """
 
    def __init__(self,data):
 
        sys.stdout.write("\r"+data.__str__())
        sys.stdout.flush()

def print_data(my_dict):
    for key, value in sorted(my_dict.items()):
        if key != 'key':
            print key, value
    print "\n"

print ("Starting script...%s") % (datetime.now())

while True:
	try:
		# from the HIH-6130 sensor
		sta, hum, tempout = hih613.hih6130()

		# Make dictionary of the items to send to ThingSpeak.com

		dict = { 'field1': hum, 'field2': tempout, 'key': tskey }
		ThingSpeak.doit(dict)

		output = "Hum: %s, Temp: %s" % (dict['field1'], dict['field2'])
		Printer(output)

		if hum >= cutoff:
			GPIO.output(i, GPIO.HIGH)
		else:
			GPIO.output(i, GPIO.LOW)
		time.sleep(14)

	except socket.gaierror, e:
		print ("Address related error occurred: %s") % (e)
        	time.sleep(15)
	except socket.error, e:
		print ("Error sending data: %s") % (e)
        	time.sleep(15)
        except httplib.BadStatusLine, e:
        	print ("httplib error: %s") % (e)
        	time.sleep(15)
	except (KeyboardInterrupt):
		print("Quit")
		GPIO.cleanup()
