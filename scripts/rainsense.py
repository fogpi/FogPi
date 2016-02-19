#!/usr/env/python

import time
from datetime import datetime
import threading
import RPi.GPIO as GPIO
#================================
#=	RainGaugeSensorClass   =#
#= detects pulses, turn on/off =#
#================================


class rainsense:
#init function, takes time period to poll over, number of ticks from rain sensor to turn on in polling period, and GPIO channel that rain sensor is setup
	timerfrequency = 0
	threshold=0
	GPIOchannel=0
	rain=0
	hourrain=0
	isRaining=False

 
	def rain_detected(self,channel): # this function gets called every time pulse detected on requested channel
		self.rain = self.rain +1
		self.hourrain = self. hourrain +1

	def checkrain(self):
		print('pulses this period' + str(self.rain) + "this hour: " +str(self.hourrain))
		if self.currenthour != datetime.now().hour:
			self.hourrain=0
			self.currenthour = datetime.now().hour

		if self.rain > self.threshold-1 :
			self.isRaining = True
			print('threshold of rain surpassed :is raining')
		else:
			self.isRaining = False
			print('threshold of rain not surpassed:no rain')

		self.rain = 0
		threading.Timer(self.timerfrequency,self.checkrain).start()

	def __init__(self,time,ticks,channel):
                self.timerfrequency = time
                self.threshold = ticks
                self.GPIOchannel =channel

                self.rain = 0
                self.hourrain = 0
                self.isRaining=False

                self.currenthour = datetime.now().hour
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
                GPIO.add_event_detect(self.GPIOchannel, GPIO.FALLING, callback=self.rain_detected, bouncetime=10)#polls pin for rainsensor

                threading.Timer(self.timerfrequency,self.checkrain).start() # starts timer to count pulses per polling period

if __name__ == "__main__":
		rainsensor = rainsense(12,10,15)
		while True:
			time.sleep(1)
		
