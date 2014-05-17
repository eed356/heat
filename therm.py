#!/usr/bin/env python
import os
import re
import RPi.GPIO as GPIO
import time
import math

def main():

    GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)

# set BCM pin number for the furnace.
    FURNACE = 18
    GPIO.setup(FURNACE, GPIO.OUT)
    GPIO.output(FURNACE, GPIO.HIGH)

# see if the one-wire "w1" interfaces are loaded
    modfile = open("/proc/modules")
    moduletext = modfile.read()
    modfile.close()
    if not (re.search("w1_gpio", moduletext) and re.search("w1_therm", moduletext)):

# if modules not found, install them
        os.system('sudo modprobe w1-gpio')
        os.system('sudo modprobe w1-therm')

# define serial number for the DS18B20 temperature sensor
    sensmaintemp = "/sys/bus/w1/devices/28-000005b5701f/w1_slave" #inside sensor
    sensoutsidetemp = "/sys/bus/w1/devices/28-000005cd4664/w1_slave" #NOT CURRENTLY CONFIGURED

# this reads the temperature and rounds the value to the nearest decimal and also does a crc check
    def currtemp():
        while(1):
            tfile = open(sensmaintemp)
            text = tfile.read()
            tfile.close()
            firstline  = text.split("\n")[0]
            crc_check = text.split("crc=")[1]
            crc_check = crc_check.split(" ")[1]
            if crc_check.find("YES")>=0:
                break
        secondline = text.split("\n")[1]
        temperaturedata = secondline.split(" ")[9]
        temperature = float(temperaturedata[2:])
        temperature = temperature / 1000.0
        temperature = round(temperature, 1)
        return temperature

# set desired temperature using thermostat file from web server. reads reads a text file in /var/bin
    def settemp():
        readtemp = open("thermostat", "r")
        settemp = readtemp.readline(4)
        readtemp.close()
        return float(settemp)

# hold the temperature at the settemp. write status to file in /var/bin
    def holdtemp():
        # the + or - of 0.5 is a heuristic value. modify to desired setting
        while currtemp() >= settemp() - 0.5:
           GPIO.output(FURNACE, GPIO.HIGH)
           status = open("status", "w+")
           status.write("Furnace is off.")
           status.close()
           print "Off loop", currtemp(), settemp()
           time.sleep(30)
        else:
            while currtemp() <= settemp() + 0.5:
               GPIO.output(FURNACE, GPIO.LOW)
               status = open("status", "w+")
               status.write("Furnace is on.")
               status.close()
               print "On loop", currtemp()
               time.sleep(30)

# this constructs an infinite loop
    infloop = 1
    while infloop == 1 :
        holdtemp()

if __name__ == '__main__':
        main()

