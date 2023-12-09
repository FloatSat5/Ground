from websockets.sync.client import connect
import json

def hello():
    with connect("ws://localhost:1302") as websocket:
        msg = {}
        msg["pitch"] = 10
        message = json.dumps(msg)
        websocket.send(message)
        message = websocket.recv()
        print(f"Received: {message}")

hello()