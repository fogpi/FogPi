import RPi.GPIO as GPIO
import time

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

h2o = 22
GPIO.setup(h2o, GPIO.IN)

while True:
    input = GPIO.input(h2o)
    if input:
        print('High: %s' % input)
    else:
        print('Low: %s' % input)
    time.sleep(1)
    
GPIO.cleanup()
