import RPi.GPIO as GPIO
import time
import requests
import json
import adafruit_dht
import board
import threading
stop=threading.Event()
dht_device = adafruit_dht.DHT11(board.D25)
GPIO.setmode(GPIO.BCM)
GPIO.setup(13, GPIO.OUT)
p = GPIO.PWM(13, 50)  # PWM frequency is 50Hz
p.start(10)  # Initialization at this angle the garage door is closed
#this setup is specific to the MG995 servo_motor being used as a garage door
initial_url="input your server's url here"
initial_url=input("input your server's url here: ")

def get_command():
#this api endpoint retrieves commands from a server
        url=initial_url+"/get_command"
        headers={'Content-Type':'application/json'}
        try:
            response = requests.get(url,headers=headers).text
        except Exception as err:
            print(err)
            response="null"
        return response
device_list="light kitchen "
def upload_device_list(device_list):
    #updating the sever with the list of active devices
    devices={"devices":device_list}
    url=initial_url+"/set_devices"
    json_data = json.dumps(devices)
    headers={'Content-Type':'application/json'}
    response = requests.post(url, json=json_data,headers=headers)
def dht11():
#this program collect temperature in c° and humidity in % from the dht11 device
  data={"temperature":0.0,"humidity":0.0}
  temperature_c = dht_device.temperature
  #temperature_f = temperature_c * (9 / 5) + 32
  humidity = dht_device.humidity
  if None not in [humidity,temperature_c]:
    data["temperature"]=temperature_c
    data["humidity"]=humidity
  return data
def upload_dht11():
#this function is running on a separate thread and update the temperature and humidity values every 10 seconds
    while True:
        if stop.is_set():
            break
        url=initial_url+"/set_data"
        try:
          sensor_data = dht11()
        except Exception:
           continue
        print(sensor_data)
        json_data = json.dumps(sensor_data)
        headers={'Content-Type':'application/json'}
        try:
            response = requests.post(url, json=json_data,headers=headers)
            time.sleep(10)
        except Exception as err:
            continue
def processing(text):
    text =text.replace("living room","living_room")
    text =text.replace("cool down","cool_down fan")
    #this insure that some  keywords are not split
    text =text.replace("phone","fan")
    #the voice recognition sometimes mishear the word fan and writes phone instead
    words = text.split()
    locations = ("kitchen","living_room", "bedroom", "bathroom", "garage")
    devices = ("light", "tv", "fan", "door","lights","television","fans","oven")
    on = ("up","on","open","cool_down")
    off = ("down","off","close","lower")
    actions = {"on": on, "off": off}
    loc = "NULL"
    dev = "NULL"
    act = "NULL"
    for word in words:
        if word in locations:
            loc = word      
        elif word in devices:
            dev = word
        if dev[-1]=="s":
            dev=dev[:-1]
        for category, category_list in actions.items():
            if word in category_list:
                act = category
    #this program process the natural language input and extract three key information which are location device and action
    command_list=[loc,dev,act]
    command_list = error_handling(command_list)
    #this function take care of any special cases during the processing
    return command_list

def error_handling(command_list):
    if command_list[1]=="television":
        command_list[1]="tv"
    if command_list[1] =="tv":
        command_list[0]="living_room"
    #there is only one tv in the house found in the living room
    if command_list[1]=="oven":
        command_list[0]="kitchen"
    #there is only 1 oven in the house found in the kitchen
    if command_list[1]=="fan" and command_list[0] not in ("living_room","bedroom"):
        command_list[0]="NULL"
    #only 2 fans one in the living room the other in the bedroom
    return command_list


def history(active_devices,command_list):
    #keeping track of active devices and send the device status to the server
    active_devices=active_device_check(command_list,active_devices)
    device_list="| "
    if not active_devices:
        device_list="null"
    else:
        for device in active_devices:
            dev=" ".join(device)
            device_list=device_list+dev+" | "
    upload_device_list(device_list)
    
    return active_devices

def active_device_check(command_list,active_devices):
    #keeping track of active devices by updating the active devices list
    device=command_list[:2]
    status=command_list[2]
    if status!="off" and (device in active_devices)==False:
        active_devices.append(device)
    elif status=="off" and (device in active_devices)==True:
        active_devices.remove(device)
    return active_devices

def turn_off_everything(active_devices):
    #generate off command for all the currently active devices
    commands=[]
    for device in active_devices:
        commands.append(device+["off"])
    active_devices.clear()
    upload_device_list("null")
    return commands,active_devices

def voice_controlled_home_automation():
    #this function allows the user to remotely control the program through a server
    active_devices = []
    last_command="null"
    #this loop send a get request to the server every second and compare it to the previous one if new_command!=old_command it gets executed
    while True:
        time.sleep(1) 
        command=get_command()
        if command!=last_command:
            last_command=command
            user_input=command.lower()
        else:
            continue
        print(f"input:{user_input}")         
        device_list=[]
        if user_input == "history":
            for devices in active_devices:
                device=" ".join(devices)
                device_list.append(device)
            print(f"output:{device_list}")
            device_list.clear()
            continue 
        #this display the list of active devices on the console
        if "turn off everything" in user_input or "turn off all devices" in user_input:
            commands, active_devices = turn_off_everything(active_devices)
            
            for off_command in commands:
                print(f"output:{off_command}")
                command_dispatcher(off_command)
                #will send the command to specific function based on the matching location
            continue
        if user_input == "terminate":
            commands, active_devices = turn_off_everything(active_devices)
            for off_command in commands:
                print(f"output:{off_command}")
                command_dispatcher(off_command)  
            print("output: terminating...")
            time.sleep(3)
            stop.set()
            #the "terminate" special command shutdown all active devices before closing the program
            #to leave the garage door enough time to close before terminating the program
            GPIO.cleanup()
            break
        command = processing(user_input)
        #the processing function takes the command in form of actual language then simplifies it using word matching to make it a uniform executable command
        if "NULL" in command:
            #if NULL in the command then there is one or more missing information
            print(f"output: I don't understand")
            print(f"output:{command}")
        else:
            active_devices = history(active_devices, command)
            print(f"output:{command}")
            command_dispatcher(command)

def command_dispatcher(command):
    location=command[0]
    device=command[1]
    action=command[2]
    if location=="living_room":
        living_room(device,action)
    elif location=="bedroom":
        bedroom(device,action)
    elif location=="kitchen":
        kitchen(device,action)
    elif location=="bathroom":
        bathroom(device,action)
    elif location=="garage":
        garage(device,action)
  
def kitchen(device,action):
    light_pin=4
    oven_power_pin=17
    if device=="light":
        power_supply_control(light_pin,action)
    if device=="oven":
        power_supply_control(oven_power_pin,action)
            
def bedroom(device,action):
    light_pin=26
    fan_pin=24
    if device=="light":
        power_supply_control(light_pin,action)
    if device=="fan":
        relay_power_supply_control(fan_pin,action)
        
def bathroom(device,action):
    light_pin=6
    if device=="light":
        power_supply_control(light_pin,action)
        
def garage(device,action):
    light_pin=22
    last_action =None
  
    if device=="light":
        power_supply_control(light_pin,action)
    elif device=="door":
        if last_action!=action:
            last_action=action
            servo_control(action)

                
def living_room(device,action):
    light_pin=23
    fan_pin=27
    tv_power_pin=16
    if device=="light":
        power_supply_control(light_pin,action)
    elif device=="fan":
        relay_power_supply_control(fan_pin,action)
    elif device=="tv":
#the tv in my scenario is an arduino uno with an lcd screen shield the usb power supply is connected to a relay
        relay_power_supply_control(tv_power_pin,action)
        
        
def power_supply_control(low_voltage_pin,action):
    GPIO.setup(low_voltage_pin, GPIO.OUT) 
    if action in ("on"):
        GPIO.output(low_voltage_pin,GPIO.HIGH)
    elif action=="off":
        GPIO.output(low_voltage_pin,GPIO.LOW)
        
def relay_power_supply_control(low_voltage_pin,action):
    #the relay board I used had an inverted logic
    GPIO.setup(low_voltage_pin, GPIO.OUT) 
    if action in ("on"):
        GPIO.output(low_voltage_pin,GPIO.LOW)
    elif action=="off":
        GPIO.output(low_voltage_pin,GPIO.HIGH)

def servo_control(action):
   #this function is made for the MG995 servo motor
   #5=>90° rotation clockwise 10=>90° rotation counter clockwise
   act=0
   if action=="on":
      act=5
   elif action=="off":
      act=10
   try:
      p.ChangeDutyCycle(act)  
      time.sleep(1)
   except Exception:
      p.stop()
      GPIO.cleanup()       

 
 # Run the voice-controlled home automation system

thread1=threading.Thread(target=voice_controlled_home_automation)
thread2=threading.Thread(target=upload_dht11)
thread1.start()
thread2.start()
thread1.join()
thread2.join()
GPIO.cleanup()
  

#Here is a reference table to help with the wiring for a raspberry pi 4.

# Device Name & Location        Pin Number BCM
# ---------------------------  ---------------
DEVICE_LIVING_ROOM_LIGHT        = 23
DEVICE_LIVING_ROOM_FAN          = 27
DEVICE_LIVING_ROOM_TV           = 16
DEVICE_KITCHEN_LIGHT            = 4
DEVICE_KITCHEN_OVEN             = 17
DEVICE_BEDROOM_LIGHT            = 26
DEVICE_BEDROOM_FAN              = 24
DEVICE_BATHROOM_LIGHT           = 6
DEVICE_GARAGE_LIGHT             = 22
DEVICE_GARAGE_DOOR_SERVO        = 13
DEVICE_TEMP_HUMIDITY_SENSOR     = 25

# The data above corresponds to device names, locations, and their respective GPIO pin assignments in BCM numbering.
