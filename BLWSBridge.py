import websockets
import asyncio
from aioserial import AioSerial
import sys
from websockets.exceptions import ConnectionClosed

# BluetoothSerialPort-Websocket bidirectional bridge
class BluetoothWebsocketBridge:
    lastTelemetry = ""
    count = 0
    blConnected = False
    def main(self):
        print("Starting...")
        self.websocket = None
        aioSerial = AioSerial(port='COM8', baudrate=115200) #, timeout=10)
        self.aioSerial = aioSerial
        asyncio.run(self.async_loop(aioSerial))
        
    async def async_loop(self, aioSerial: AioSerial):
        #asyncio.create_task(self.write(aioSerial))
        #asyncio.create_task(self.ws_server())
        asyncio.create_task(self.websocket_client())
        print("Started bridge")
        while True:
            await self.bluetooth_client(aioSerial)

    async def bluetooth_client(self, aioSerial):
        message = (await aioSerial.read_until_async()).decode(errors='ignore')
        blConnected = True
        message = message.replace('\x00','')
        if message.endswith('\n'):
            message = message.rstrip('\n')
        msgSplit = message.split(',')
        if not msgSplit[0].startswith("Invalid") and msgSplit[0] != self.lastTelemetry:
            self.lastTelemetry = msgSplit[0]
        if self.websocket and self.websocket.open and self.count % 1 == 0:
            print(f"Received bl message: {message}")
            msgs = message.split(';')
            for msg in msgs:
                await self.websocket.send(msg)
        self.count += 1

    async def websocket_client(self):
        while True:
            try:
                await self.ws_client_connection()
            except ConnectionRefusedError as e:
                pass
            except asyncio.CancelledError:
                pass
            except asyncio.TimeoutError:
                pass
            await asyncio.sleep(1)

    async def ws_client_connection(self):
        async with websockets.connect("ws://localhost:1302", ping_timeout=None) as websocket:
            self.websocket = websocket
            print(f"Connected to {websocket.remote_address}")
            await self.ws_loop(websocket)

    async def ws_loop(self, websocket, path=''):
        #await asyncio.sleep(2)
        #await websocket.send('batvo,11.9')
        await websocket.send('{ "blConnected": true}')
        while True:
            try:
                await self.ws_handle(websocket)
            except ConnectionClosed as e:
                print(f"Connection closed: {path} from {websocket.remote_address}: {e}")
                self.websocket = None
                break

    async def ws_handle(self, websocket):
        message = await websocket.recv()
        print(f'Received ws message: {message}')
        if not message.endswith('\n'):
            message += '\n'
        await self.aioSerial.write_async(message.encode())


    # ------------ Unused functions: ------------
    async def write(self, aioSerial: AioSerial):
        while True:
            await aioSerial.write_async(b'Hello GrabSat!')
            await asyncio.sleep(1)

    async def ws_server(self):
        async with websockets.serve(self.ws_request, "", 1302, ping_interval=None):
            await asyncio.Future()  # run forever

    async def ws_request(self, websocket, path):
        self.websocket = websocket
        print(f"Connection from {websocket.remote_address}")
        await self.ws_loop(websocket, path)

if __name__ == '__main__':
    try:
        BluetoothWebsocketBridge().main()
    except RuntimeError:
        pass
    except KeyboardInterrupt:
        sys.exit(0)