from websockets.sync.client import connect
import json
from time import sleep
import signal
import sys


def main():
    try:
        run()
    except ConnectionRefusedError as e:
        sleep(1)
    except Exception as e:
        print(e)
        sleep(1)
        
def run():
    with connect("ws://localhost:1302") as websocket:
        signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, websocket))
        #publisher(websocket)
        #subscriber(websocket)
        publisherAngPos(websocket)
        
        
def publisher(websocket):
    sleepTime = 0.05
    sleepTime = 1
    while True:
        for i in range(-90, 91, 1):
            sendPitch(websocket, i/10)
            sleep(sleepTime)
        for i in range(90, -91, -1):
            sendPitch(websocket, i/10)
            sleep(sleepTime)

def sendPitch(websocket, pitch):
    msg = {}
    msg["pitch"] = pitch
    msg["roll"] = 20
    message = json.dumps(msg)
    websocket.send(message)
    #message = websocket.recv()
    
def publisherAngPos(websocket):
    sleepTime = 1
    count = 0
    step = 10
    while True:
        roll = (count*step - 120) % 360
        if roll > 180:
            roll -= 360
        pitch = (count*step) % 360
        if pitch > 180:
            pitch -= 360
        yaw = (count*step + 120) % 360
        if yaw > 180:
            yaw -= 360
        sendAngData(websocket, roll, pitch, yaw, count)
        sendAngData(websocket, yaw, roll, pitch, count, command="angve")
        websocket.send(f"{count}, armpo, {count%2}")
        websocket.send(f"{count}, batvo, {count%10}")
        websocket.send(f"{count}, elcur, {count%10}")
        websocket.send(f"{count}, magst, {count%2}")
        count += 1
        sleep(sleepTime)
    
def sendAngData(websocket, roll, pitch, yaw, msgNum, command="angpo"):
    msg = f"{msgNum}, {command}, {roll}, {pitch}, {yaw}"
    websocket.send(msg)
    
def subscriber(websocket):
    while True:
        message = websocket.recv()
        print(message)
    
def signal_handler(sig, frame, websocket):
    print('Stopping...')
    #websocket.close()
    exit()

if __name__ == "__main__":
    print("Starting...")
    while True:
        main()