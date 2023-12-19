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
        publisher(websocket)
        #subscriber(websocket)
        
        
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
    
def subscriber(websocket):
    while True:
        message = websocket.recv()
        print(message)
    
def signal_handler(sig, frame, websocket):
    print('Stopping...')
    websocket.close()
    exit()

if __name__ == "__main__":
    print("Starting...")
    while True:
        main()