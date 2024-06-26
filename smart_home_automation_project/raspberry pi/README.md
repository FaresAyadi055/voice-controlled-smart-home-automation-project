this program controls a mini smart home with a raspberry pi. It can be done remotely 
with an internet connection via a server communication. In this project we are using a mobile app as the 
user interface to establish this remote control.

house with the following layout=>5 rooms: living room, kitchen, bedroom, bathroom, garage
=>each room has a light , the garage has an automatic door , the living and bedroom have fans,
the living room has a tv,there is also a temperature and humidity sensor
 
| Device                   | GPIO Pin (BCM) | Description                          |
|--------------------------|----------------|--------------------------------------|
| Living Room Light        | 23             | White LED                            |
| Living Room Fan          | 27             | 5V DC Motor                          |
| Living Room TV           | 16             | Arduino Uno with LCD Screen Shield   |
| Kitchen Light            | 4              | White LED                            |
| Kitchen Oven             | 17             | Red LED                              |
| Bedroom Light            | 26             | White LED                            |
| Bedroom Fan              | 24             | 5V DC Motor                          |
| Bathroom Light           | 6              | White LED                            |
| Garage Light             | 22             | White LED                            |
| Garage Door Servo        | 13             | MG995 Servo Motor                    |
| Temp/Humidity Sensor     | 25             | DHT11                                |

!(the dc motors and arduino power supply are being controlled through a 4 relays board and powered by a phone charger)

!(the program send a get request to the server every second and compare it to the previous one if new_command!=old_command it gets executed)
# How to use it
-this program has 5 types of commands:

1- device control commands:

to control a device in the house you need to specify three key information.
In your command which are the device location, device name, and the action you want to do (the order doesn't matter).
the program will search for key words in the user input and fill the command list, any missing information is replaced with "Null"
for error handing. 
the system will output a list in the format ["location","device","action"] it will be used as an activation command line.

example: "light up the bathroom" ===> ["bathroom",light","on"].

here are the programs keywords:
```python
    locations = ("kitchen","living_room", "bedroom", "bathroom", "garage")
    devices = ("light", "tv", "fan", "door","lights","television","fans","oven")
    on = ("up","on","open","cool_down")
    off = ("down","off","close","lower")
    actions = {"on": on, "off": off}
```
2-list of active devices:

by typing or saying "history" or making an http get request the program will display a list containing the devices you just activated
(the program will automatically remove the devices that you turned off from the list)

3-turn_off_everything:

by typing or saying "turn off everything" or "turn off all devices" the program will 
generate commands that will turn of the devices in the active devices list then clear it in both the program and server.

4-closing the program:

by typing or saying "terminate" the program will first turn off all devices before stopping the program
the server will then replace "terminate" with "null" so the program won't shutdown when restarted

5-automated cooling:

the dht device upload the current temperature and humidity to the server every 10 seconds in a separate thread.
the automated cooling happens on the server side where it waits for a http post request containing a threshold
temperature value and compares it to the current temperature. based on the comparison it will either turn on or 
off the living room fan, by updating the current command stored in the server waiting to be retrieved by the pi.

# materials:

| Component              | Description                             | Notes                                |
|------------------------|-----------------------------------------|--------------------------------------|
| White LED              | Light source for various rooms          | Used for lighting control            |
| 5V DC Motor            | Fan for living room and bedroom         | Controlled via relay board           |
| mini screen            | will represent a tv in a living room    |you may want to include an i2c script if you don't want to use an uno shield|
| Red LED                | Indicator light for kitchen oven        |                                      |
| MG995 Servo Motor      | the script is specific to this model    |I used a bearing and 3d printed an axel to rotate the door |
| DHT11                  | Temperature and humidity sensor         | Measures environmental data          |
| 4-Relay Board          | Controls multiple devices               | Used to control DC motors and screen power supply |
| Phone Charger          | Powers the 4-Relay Board                | Supplies power to the relay board    |
|breadbord/jumper cables | for wiring                              |                                      |
|building materials      | we used corrugated plastic sheets       |you can use anything you want         |
|4-Relay Board           | a switch for the power consuming devices| the logic of this board is inverted  |

# important! the program will first ask you input your server's url
if you want to hardcode the url then in line 15
```python
import RPi.GPIO as GPIO
import time
import requests
import json
import adafruit_dht
import board
import threading
#this code was tested on a raspberry pi 4
stop=threading.Event()
dht_device = adafruit_dht.DHT11(board.D25)
GPIO.setmode(GPIO.BCM)
GPIO.setup(13, GPIO.OUT)
p = GPIO.PWM(13, 50)  # PWM frequency is 50Hz
p.start(10)  # Initialization at this angle the garage door is closed
initial_url="input your server url here"                                            #<====hardcode your url here
initial_url=input("input your server's url here :")                                 #<====comment this line
```

