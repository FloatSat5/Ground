import sys
import qdarkstyle
import os
# 1. Import QApplication and all the required widgets
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QAction, QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLineEdit
from attitude import AttitudeIndicator
from websockets.server import serve
import asyncio
from PyQt5 import QtCore, QtWebSockets, QtNetwork
from PyQt5.QtGui import QDoubleValidator
import json

def condFunc(func, cond):
    if cond:
        func()

class Main():
    def main(self):
        os.environ['QT_API'] = 'pyqt5'
        # 2. Create an instance of QApplication
        app = QApplication(sys.argv + ['-platform', 'windows:darkmode=1'])
        
        serverObject = QtWebSockets.QWebSocketServer('My Socket', QtWebSockets.QWebSocketServer.NonSecureMode)
        server = MyServer(serverObject)
        self.server = server
        serverObject.closed.connect(app.quit)
        server.addSubFunction(self.subFunction)


        # 3. Create your application's GUI
        window = QWidget()
        app.setStyleSheet(qdarkstyle.load_stylesheet())
        window.setWindowTitle("PyQt App")
        #window.setGeometry(100, 100, 800, 450)
        scale = 1.5
        window.setGeometry(100, 100, 800 * scale, 450 * scale)
        #window.setGeometry(100, 100, 1600, 900)
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
        tabPID = QWidget()
        #tabs.resize(800,450)
        tabs.move(0,0)
        # Set text size of tabs
        tabs.setStyleSheet("QTabBar::tab { height: 23px; width: 150px; font-size: 12pt; }")
        
        # Add tabs
        tabs.addTab(tabOverview, "Overview")
        tabs.addTab(tabMission, "Mission modes")
        tabs.addTab(tabSensors, "Sensors")
        tabs.addTab(tabCustom, "Custom")
        tabs.addTab(tabPID, "PID")
        
        # Create first tab
        tabOverview.layout = QVBoxLayout()
        pushButton1 = QPushButton("PyQt5 button")
        tabOverview.layout.addWidget(pushButton1)
        
        attitude = AttitudeIndicator()
        self.attitude = attitude
        tabOverview.layout.addWidget(attitude)
        
        tabOverview.setLayout(tabOverview.layout)
        
        # Add tabs to widget
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tabs, 0)
        
        # Add elements to mission tab
        tabPID.layout = QHBoxLayout()
        self.createPIDSection(tabPID.layout)
        tabPID.setLayout(tabPID.layout)

        # 4. Show your application's GUI
        window.show()
        tabs.setCurrentIndex(4)

        #asyncio.run(wsServe())
        # 5. Run your application's event loop
        sys.exit(app.exec())
        
    def createPIDSection(self, parent):
        # section for pid values
        pidLayout = QVBoxLayout()
        # PID label
        pidLabel = QLabel("PID")
        pidLabel.setStyleSheet("font-size: 14pt; font-weight: bold;")
        pidLabel.setAlignment(QtCore.Qt.AlignTop)
        pidLabel.setAlignment(QtCore.Qt.AlignHCenter)
        pidLayout.addWidget(pidLabel)
        self.createParameter(pidLayout, "pid.K_p", label="K_p")
        self.createParameter(pidLayout, "pid.K_i", label="K_i")
        self.createParameter(pidLayout, "pid.K_d", label="K_d")
        parent.addLayout(pidLayout)
        
    def createParameter(self, parent, name, min = 0, max = 2, value = 1, decimalPlaces = 3, label=None):
        if label is None:
            label = name
        scale = 10**decimalPlaces
        verLayout = QVBoxLayout()
        verLayout.setAlignment(QtCore.Qt.AlignTop)
        firstLine = QHBoxLayout()
        secondLine = QHBoxLayout()

        # set label
        label = QLabel(label)
        label.setAlignment(QtCore.Qt.AlignLeft)
        label.setStyleSheet("font-size: 12pt;")
        label.setMinimumWidth(50)
        #label.setMaximumWidth(50)
        firstLine.addWidget(label)
        
        # Min value input
        minLabel = QLabel("Min")
        minLabel.setAlignment(QtCore.Qt.AlignRight)
        minLabel.setAlignment(QtCore.Qt.AlignVCenter)
        minLabel.setStyleSheet("font-size: 12pt;")
        firstLine.addWidget(minLabel)
        
        minInput = QLineEdit()
        minInput.setAlignment(QtCore.Qt.AlignCenter)
        minInput.setStyleSheet("font-size: 12pt;")
        minInput.setMinimumWidth(70)
        #minInput.setMaximumWidth(50)
        minInput.setText(str(min))
        # Set validator
        validator = QDoubleValidator()
        validator.setBottom(0)
        validator.setDecimals(3)
        # make empty string invalid
        validator.setNotation(QDoubleValidator.StandardNotation)
        minInput.setValidator(validator)
        
        # safe textChanged
        
        firstLine.addWidget(minInput)
        
        # Value display
        display = QLabel(("{:." + str(decimalPlaces) + "f}").format(value))
        display.setAlignment(QtCore.Qt.AlignCenter)
        display.setStyleSheet("font-size: 12pt;")
        display.setMinimumWidth(70)
        #display.setMaximumWidth(50)
        firstLine.addWidget(display)
        
        # Max value input
        maxLabel = QLabel("Max")
        maxLabel.setAlignment(QtCore.Qt.AlignRight)
        maxLabel.setStyleSheet("font-size: 12pt;")
        firstLine.addWidget(maxLabel)
        
        maxInput = QLineEdit()
        maxInput.setAlignment(QtCore.Qt.AlignCenter)
        maxInput.setStyleSheet("font-size: 12pt;")
        maxInput.setMinimumWidth(70)
        #maxInput.setMaximumWidth(50)
        maxInput.setText(str(max))
        maxInput.setValidator(validator)
        
        firstLine.addWidget(maxInput)
        
        slider = QSlider(QtCore.Qt.Horizontal)
        slider.setMinimum(min*scale)
        slider.setMaximum(max*scale)
        slider.setValue(value*scale)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(scale/10)
        slider.valueChanged.connect(lambda v: self.valueChanged(v/scale, display, name))
        secondLine.addWidget(slider)
        
        minInput.textChanged.connect(lambda v: condFunc(lambda: slider.setMinimum(float(v)*scale), v != ""))
        maxInput.textChanged.connect(lambda v: condFunc(lambda: slider.setMaximum(float(v)*scale), v != ""))
        
        verLayout.addLayout(firstLine)
        verLayout.addLayout(secondLine)
        parent.addLayout(verLayout)
    
    def valueChanged(self, value, display, name):
        display.setText(str(value))
        self.server.sendText(json.dumps({name: value}))
    
    def subFunction(self, message):
        print(message)
        if message.startswith('{'):
            msg = json.loads(message)
            if "pitch" in msg:
                self.attitude.setPitch(msg["pitch"])
            if "roll" in msg:
                self.attitude.setRoll(msg["roll"])
    
class MyServer(QtCore.QObject):
    def __init__(self, parent):
        super(QtCore.QObject, self).__init__(parent)
        self.clients = []
        self.server = QtWebSockets.QWebSocketServer(parent.serverName(), parent.secureMode(), parent)
        if self.server.listen(QtNetwork.QHostAddress.LocalHost, 1302):
            print('Connected: '+self.server.serverName()+' : '+self.server.serverAddress().toString()+':'+str(self.server.serverPort()))
        else:
            print('error')
        self.server.newConnection.connect(self.onNewConnection)

        #print(self.server.isListening())
        #self.attitude = attitude
        self.subFunctions = []
        self.clientConnection = None

    def onNewConnection(self):
        self.clientConnection = self.server.nextPendingConnection()
        self.clientConnection.textMessageReceived.connect(self.processTextMessage)

        self.clientConnection.binaryMessageReceived.connect(self.processBinaryMessage)
        self.clientConnection.disconnected.connect(self.socketDisconnected)

        self.clients.append(self.clientConnection)

    def processTextMessage(self,  message):
        if (self.clientConnection):
            for function in self.subFunctions:
                function(message)
            else:
                self.clientConnection.sendTextMessage(message)

    def processBinaryMessage(self,  message):
        if (self.clientConnection):
            self.clientConnection.sendBinaryMessage(message)

    def socketDisconnected(self):
        if (self.clientConnection):
            self.clients.remove(self.clientConnection)
            self.clientConnection.deleteLater()
    
    def addSubFunction(self, function):
        self.subFunctions.append(function)
        
    def sendText(self, message):
        if self.clientConnection:
            self.clientConnection.sendTextMessage(message)

if __name__ == "__main__":
    main = Main()
    main.main()