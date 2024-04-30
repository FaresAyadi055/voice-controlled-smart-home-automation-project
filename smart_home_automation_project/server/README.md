Flask Server for Raspberry Pi Smart Home

this flask server was hosted on PythonAnyWhere for this project you can chose another service or self hosting. 

it was made to establish communication between a mobile app made with Thunkable and the program
on the raspberry pi.

the mobile app sends commands either typed or voiced (using the google speech recognition api feature in Thunkable)
where they are stored in the server until they are fetched by the pi or overwritten by another command.
the mobile app also sends a threshold temperature to the server.
the mobile app receives data from the server like the current temperature and humidity and the list of active devices.
the raspberry pi receives the commands from the server and executes them.
It also sends the current temperature and humidity to the server every 10 seconds.
The program keep track of active devices and upload the list to the server every command execution.

here is a simplified table of the communication between the different components:

| Communication Direction| Origin         | Destination   | Data/Action                              | Frequency         |
|------------------------|----------------|---------------|------------------------------------------|-------------------|
| Command upload         | Mobile App     | Flask Server  | User commands (typed/voiced)             | user dependant    |
| Command retrieve       | Flask Server   | Raspberry Pi  | Retrieve stored commands in the server   | Every second      |
| Temp/Humidity upload   | Raspberry Pi   | Flask Server  | Temperature and humidity uploading       | Every 10 seconds  |
| Temp/Humidity Retrieve | Flask Server   | Mobile App    | Temperature and humidity readings        | user dependant    |
| Active_Device upload   | Raspberry Pi   | Flask Server  | upload List of active devices            | user dependant    |
| Active_Device retrieve | Flask Server   | Mobile App    | display List of active devices           | After each command|
| Threshold Temperature  | Mobile App     | Flask Server  | User-specified temperature threshold     | user dependant    |


automated cooling is done on the server side where it waits for a http post request containing a threshold temperature value and compares it to the current temperature.
if the current is higher or equal to the threshold the server updates the command to "turn on the living room fan".
if the current temperature is lower than the threshold the server updates the command to "turn off the living room fan".
the command is then fetched by the pi.


the api endpoints are already defined in the flask server like get_data for fetching the dht11 data and set_command sor updating the commands.
make sure to add them at the end of the url you chose.