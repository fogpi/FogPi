#!/usr/env/python

import smbus
import time

i2c = smbus.SMBus(1)

# ==============================================
# =   HIH-6130 Humidity/Temperrature Sensors   =
# =   for Measurement Data Fetch Mode          =
# ==============================================
def hih6130():
    # get 4 bytes
    buf = i2c.read_i2c_block_data(0x27, 0, 4)

    # get status
    sta = buf[0] >> 6 & 0x03

    # command mode or diagnostic mode are zero
    if sta >= 2:
            return [sta, 0.0, 0.0]

    # get digital output
    hum = (buf[0] & 0x3F) * 256 + buf[1]
    tem = buf[2] * 64 + (buf[3] >> 2)

    # convert digital output
    hum = round(hum / 16383.0 * 100, 1)
    tem = round(tem / 16383.0 * 165 - 40, 1)
    return [sta, hum, tem]


if __name__ == "__main__":
    # print out Humidity and Temperrature
    while True:
        data = hih6130()
        print("Humidity= %s  Temp=%s" % (data[1], data[2]))
        time.sleep(1)
