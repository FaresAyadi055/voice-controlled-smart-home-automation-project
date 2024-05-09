from flask import Flask, request, jsonify
import json

df={"dht11":["0.0","0.0"],"command":["null"],"active_devices":"null","threshold":"null"}
#this dictionary is used to store the data being transferred between the mobile app and the raspberry pi program
def threshold():
    #this compares the current temperature to the threshold temperature set by the user
    if float(df["dht11"][0])>=float(df["threshold"]):
        df["command"]=["turn on the living room fan /dht11/"]
    else:
        df["command"]=["turn off the living room fan /dht11/"]
app = Flask(__name__)
@app.route('/set_data', methods=['POST'])
def set_data():
    json_data = request.get_json()
    dict_data= json.loads(json_data)
    temperature =dict_data['temperature']
    humidity =dict_data['humidity']
    data = [temperature,humidity]
    df["dht11"]=data
    if df["threshold"].isnumeric():
        threshold()
    return jsonify(data)

@app.route('/set_command', methods=['POST'])
def set_command():
    command =request.data.decode('utf-8')
    command=[command]
    df["command"]=command
    return jsonify(command)
@app.route('/set_threshold', methods=['POST'])
def set_threshold():
    limit =request.data.decode('utf-8')
    if limit.isnumeric():
        df["threshold"]=limit
    else:
        df["threshold"]="null"
    return jsonify(limit)
@app.route('/get_threshold', methods=['GET'])
def get_threshold():
    limit=df["threshold"]
    return limit
@app.route('/get_data', methods=['GET'])
def get_data():
    data =df["dht11"]
    data=f"temperature: {data[0]}°C  humidity: {data[1]}%"
    return data

@app.route('/get_command', methods=['GET'])
def get_command():
    command=df["command"]
    if command[0].lower()=="terminate":
        df["command"]=["null"]
    # this prevent the program from shutting down if we restart it without resetting the command
    return command[0]
@app.route('/get_devices', methods=['GET'])
def get_devices():
    devices=df["active_devices"]
    return devices

@app.route('/set_devices', methods=['POST'])
def set_devices():
    json_data = request.get_json()
    dict_data= json.loads(json_data)
    devices=dict_data['devices']
    df["active_devices"]=devices
    return jsonify(devices)

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5002)
