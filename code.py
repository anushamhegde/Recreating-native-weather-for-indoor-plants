## final working code

import RPi.GPIO as GPIO
import time
import spidev
import os
import time
import json
import requests
import asyncio
from kasa import SmartStrip
import board
import adafruit_dht
import digitalio


MOISTURE_LIMIT = 440     

# Setting the SPI interface
spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=1000000

# The function readMoisture takes the channel reference and returns the data using SPI 
# Reads analog value where value 1023 is complety dry and value 200 is wet soil
def readMoisture(channel):
  
  val = spi.xfer2([1,(8+channel)<<4,0])
  data = ((val[1]&3) << 8) + val[2]
  return data


# The function turnPumpOn takes input from GPIO pin 23, pump turn on and off with sleep time 0.05 seconds. 
# when invoked drops 1-2 drop of water
def turnPumpOn():
  try:
    pump = digitalio.DigitalInOut(board.D23)
    pump.direction = digitalio.Direction.OUTPUT
    pump.value = True
    time.sleep(0.10)
    pump.value = False
    time.sleep(0.10)
    pump.value = True
  except KeyboardInterrupt:
    print("exception found")
    sys.exit()


# the function getlocationHumidity makes API call to get weather based on specific city
def getlocationHumidity():
  response = requests.get("https://api.openweathermap.org/data/2.5/weather?id=1256047&appid=1c95316466c6a0d5887c404d04a1458c&units=imperial")
  json_result = response.json()
  weather_data = json_result.get('main')  
  humidity= weather_data.get('humidity')
  return humidity

# the function gets current humidity in the room 
def getCurrentHumidity():
  try:
    dhtDevice = adafruit_dht.DHT22(board.D4, use_pulseio=False)
    curr_humidity = dhtDevice.humidity
    return curr_humidity
  except RuntimeError as error:
    # the errors occures frequently, DHT's are hard to read
    print(error.args[0])  
    
  except Exception as error:
    dhtDevice.exit()
    raise error
  except KeyboardInterrupt:
    dhtDevice.exit()
    print('exiting script')

# connecting to smart plug using IP
plug = SmartStrip("192.168.1.117")
asyncio.run(plug.update())

# Function to turn on humididier using smart plug
def turnOnHumidifier():
  try:
    asyncio.run(plug.children[1].turn_on()) 
  except Exception as error:
    print("Error from plug turn on");

# Function to turn off humididier using smart plug
def turnOffHumidifier():
  try:
    asyncio.run(plug.children[1].turn_off()) 
  except Exception as error:
    print("Error from plug turn off")

# Function to turn on full wavelength light using smart plug
def turnOnLight():
  plug = SmartStrip("192.168.1.117")
  asyncio.run(plug.update())
  asyncio.run(plug.children[0].turn_on()) 

# Function to turn off full wavelength light using smart plug
def turnOffLight():
  plug = SmartStrip("192.168.1.117")
  asyncio.run(plug.update())
  asyncio.run(plug.children[0].turn_off()) 

# Function to set the light timer using location sunrise and sunset time
#by making webAPI call to sirsi,karnataka India

def isLocationDayLight():
  response = requests.get("https://api.openweathermap.org/data/2.5/weather?id=1256047&appid=1c95316466c6a0d5887c404d04a1458c&units=imperial")
  json_result = response.json()
  current_time = json_result.get('dt')
  sys_info = json_result.get('sys')
  sunrise_time= sys_info.get('sunrise')
  sunset_time= sys_info.get('sunset')
  city_name= json_result.get('name')
  country_name = sys_info.get('country')
  print("current time ",city_name,country_name,current_time )
  print("sunrise in" ,city_name,country_name,sunrise_time )
  print("sunset in" ,city_name,country_name,sunset_time )

  if ((current_time > sunrise_time) and (current_time < sunset_time )):
    print("It is day time")
    return True
  return False
 
if __name__ == "__main__":
  try:
    while True:
      mositureLevel = readMoisture(0)
      print("moisture level is",mositureLevel)
      if (mositureLevel > MOISTURE_LIMIT): # comparing current moisture level of the soil with min soil moisture level
        print("Moisture above limit \n Turning on the pump")
        turnPumpOn() # if current moisture less turn the pump on 
      else:
        print("Moisture below limit\n")


      time.sleep(5) #sleep for 5 seconds 

      humidity_loc= getlocationHumidity()
      curr_humidity= getCurrentHumidity()
      #print("cur humidity:",curr_humidity)
      #print("loc humidity:",humidity_loc)
      if curr_humidity is not None:
        if(curr_humidity<humidity_loc): # if humdity in the house is less than location humidity 
          print(" Humidifier is turned on")
          turnOnHumidifier()
        else:
          print("Humidifier is turned off")
          turnOffHumidifier()

        day = isLocationDayLight()
        if(day):
          turnOnLight()
          print("light is turned on")
        else:
          turnOffLight()
          print("light is turned off")
      time.sleep(300) #sleep for 5 seconds 

      
  except KeyboardInterrupt:
    print( "Cancel.")


