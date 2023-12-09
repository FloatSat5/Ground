import sys
import qdarkstyle
import os
# 1. Import QApplication and all the required widgets
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QAction, QTabWidget,QVBoxLayout, QPushButton
from attitude import AttitudeIndicator
from websockets.server import serve
import asyncio
from PyQt5 import QtCore, QtWebSockets, QtNetwork
import json

def main():
    os.environ['QT_API'] = 'pyqt5'
    # 2. Create an instance of QApplication
    app = QApplication(sys.argv + ['-platform', 'windows:darkmode=1'])


    # 3. Create your application's GUI
    window = QWidget()
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    window.setWindowTitle("PyQt App")
    window.setGeometry(100, 100, 280, 80)
    #helloMsg = QLabel("<h1>Hello, World!</h1>", parent=window)
    #helloMsg.move(60, 15)
    
    layout = QVBoxLayout()
    window.setLayout(layout)
        
    # Initialize tab screen
    tabs = QTabWidget()
    tabOverview = QWidget()
    tabMission = QWidget()
    tabSensors = QWidget()
    tabCustom = QWidget()
    tabs.resize(800,450)
    tabs.move(0,0)
    # Set text size of tabs
    tabs.setStyleSheet("QTabBar::tab { height: 23px; width: 150px; font-size: 12pt; }")
    
    # Add tabs
    tabs.addTab(tabOverview, "Overview")
    tabs.addTab(tabMission, "Mission modes")
    tabs.addTab(tabSensors, "Sensors")
    tabs.addTab(tabCustom, "Custom")
    
    # Create first tab
    tabOverview.layout = QVBoxLayout()
    pushButton1 = QPushButton("PyQt5 button")
    tabOverview.layout.addWidget(pushButton1)
    
    attitude = AttitudeIndicator()
    tabOverview.layout.addWidget(attitude)
    
    tabOverview.setLayout(tabOverview.layout)
    
    # Add tabs to widget
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(tabs, 0)

    # 4. Show your application's GUI
    window.show()

    #asyncio.run(wsServe())
    # 5. Run your application's event loop
    serverObject = QtWebSockets.QWebSocketServer('My Socket', QtWebSockets.QWebSocketServer.NonSecureMode)
    server = MyServer(serverObject, attitude)
    serverObject.closed.connect(app.quit)
    sys.exit(app.exec())
    
class MyServer(QtCore.QObject):
    def __init__(self, parent, attitude):
        super(QtCore.QObject, self).__init__(parent)
        self.clients = []
        self.server = QtWebSockets.QWebSocketServer(parent.serverName(), parent.secureMode(), parent)
        if self.server.listen(QtNetwork.QHostAddress.LocalHost, 1302):
            print('Connected: '+self.server.serverName()+' : '+self.server.serverAddress().toString()+':'+str(self.server.serverPort()))
        else:
            print('error')
        self.server.newConnection.connect(self.onNewConnection)

        print(self.server.isListening())
        self.attitude = attitude

    def onNewConnection(self):
        self.clientConnection = self.server.nextPendingConnection()
        self.clientConnection.textMessageReceived.connect(self.processTextMessage)

        self.clientConnection.binaryMessageReceived.connect(self.processBinaryMessage)
        self.clientConnection.disconnected.connect(self.socketDisconnected)

        self.clients.append(self.clientConnection)

    def processTextMessage(self,  message):
        if (self.clientConnection):
            if message.startswith('{'):
                msg = json.loads(message)
                if "pitch" in msg:
                    self.attitude.setPitch(msg["pitch"])
            self.clientConnection.sendTextMessage(message)

    def processBinaryMessage(self,  message):
        if (self.clientConnection):
            self.clientConnection.sendBinaryMessage(message)

    def socketDisconnected(self):
        if (self.clientConnection):
            self.clients.remove(self.clientConnection)
            self.clientConnection.deleteLater()

if __name__ == "__main__":
    main()