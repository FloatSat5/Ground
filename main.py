import sys
import qdarkstyle
import os
# 1. Import QApplication and all the required widgets
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QAction, QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLineEdit, QComboBox
from attitude import AttitudeIndicator
from websockets.server import serve
import asyncio
from PyQt5 import QtCore, QtWebSockets, QtNetwork
from PyQt5.QtGui import QDoubleValidator
import json
from pyqtgraph import PlotWidget, plot
import time
from compass import CompassWidget
from PyQt5.QtCore import QTimer

def condFunc(func, cond):
    if cond:
        func()

def isFloat(string):
    try:
        float(string)
        return True
    except ValueError:
        return False
    
def clampAngle(angle):
    while angle > 180:
        angle -= 360
    while angle < -180:
        angle += 360
    return angle

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
        window.setGeometry(100, 100, int(800 * scale), int(450 * scale))
        #window.setGeometry(100, 100, 1600, 900)
        #helloMsg = QLabel("<h1>Hello, World!</h1>", parent=window)
        #helloMsg.move(60, 15)
        
        layout = QVBoxLayout()
        window.setLayout(layout)
            
        # Initialize tab screen
        tabs = QTabWidget()
        self.tabs = tabs
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
        tabOverview.layout = QHBoxLayout()
        
        attitude = AttitudeIndicator()
        self.attitude = attitude
        tabOverview.layout.addWidget(attitude)
        
        compass = CompassWidget()
        self.compass = compass
        tabOverview.layout.addWidget(compass)
        
        tabOverview.setLayout(tabOverview.layout)
        
        # Add tabs to widget
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tabs, 0)
        
        # Add mission tab
        tabMission.layout = QVBoxLayout()
        self.createMissionTab(tabMission.layout)
        tabMission.setLayout(tabMission.layout)
        
        # Add sensor tab
        tabSensors.layout = QVBoxLayout()
        self.createSensorTab(tabSensors.layout)
        tabSensors.setLayout(tabSensors.layout)

        # Add custom tab
        tabCustom.layout = QVBoxLayout()
        self.createCustomTab(tabCustom.layout)
        tabCustom.setLayout(tabCustom.layout)
        self.tabCustom = tabCustom
        
        # Add elements to mission tab
        tabPID.layout = QVBoxLayout()
        self.createPIDTab(tabPID.layout)
        tabPID.setLayout(tabPID.layout)

        self.connectionLED = QLabel('C', tabs)
        self.connectionLED.move(850, 2)
        self.connectionLED.resize(26, 26)
        # setting up border and radius
        self.connectionLED.setStyleSheet(self.ledStylesheet("darkGreen"))
        self.connectionLED.setAlignment(QtCore.Qt.AlignCenter)

        self.batVoltLED = QLabel('P', tabs)
        self.batVoltLED.move(890, 2)
        self.batVoltLED.resize(26, 26)
        self.batVoltLED.setStyleSheet(self.ledStylesheet("darkRed"))
        self.batVoltLED.setAlignment(QtCore.Qt.AlignCenter)

        self.startBlinkingPowerLED()

        # 4. Show your application's GUI
        window.show()
        tabs.setCurrentIndex(1)

        #asyncio.run(wsServe())
        # 5. Run your application's event loop
        sys.exit(app.exec())
        
    def createMissionTab(self, parent):
        self.createParameter(parent, "mosav", label="Motor angular velocity [deg/min]", max=180, buttonLabel="Set", plotIndex=0)
        self.createParameter(parent, "sangp", label="Satellite angular position [deg]", min=-180, max=180, buttonLabel="Set", plotIndex=1)
        self.createParameter(parent, "sangv", label="Satellite angular velocity [deg/min]", max=180, buttonLabel="Set", plotIndex=2)
        
        # Create button to turn off satellite
        offButton = QPushButton("Turn off satellite")
        offButton.setStyleSheet("font-size: 14pt; font-weight: bold;")
        offButton.clicked.connect(lambda: self.server.sendText("swoff,1"))
        parent.addWidget(offButton)
        
        # Create button to start finding the debris
        findDebrisButton = QPushButton("Find debris")
        findDebrisButton.setStyleSheet("font-size: 14pt; font-weight: bold;")
        findDebrisButton.clicked.connect(lambda: self.server.sendText("fideb,1"))
        parent.addWidget(findDebrisButton)
        
        # Create button to extend arm
        self.createParameter(parent, "exarm", label="Extend arm [mm]", value=110, max=200, buttonLabel="Set")
        
        # Create button to retract arm
        self.createParameter(parent, "rearm", label="Retract arm [mm]", value=200, max=200, buttonLabel="Set")

        self.armPos = self.createParameter(parent, "", label="Estimated Arm position[mm]", value=0, max=150, interactable=False)
        
        # Create toggle for electromagnet
        magnetToggle = QPushButton("Toggle electromagnet")
        magnetToggle.setStyleSheet("font-size: 14pt; font-weight: bold;background-color : darkred")
        magnetToggle.setCheckable(True)
        magnetToggle.clicked.connect(lambda: self.server.sendText(f"semag,{1 if magnetToggle.isChecked() else 0}"))
        magnetToggle.clicked.connect(lambda: self.changeColor(magnetToggle))
        parent.addWidget(magnetToggle)
        
    def changeColor(self, button):
        if button.isChecked():
            button.setStyleSheet("font-size: 14pt; font-weight: bold;background-color : green")
        else:
            button.setStyleSheet("font-size: 14pt; font-weight: bold;background-color : darkred")
        
        
    def createSensorTab(self, parent):
        # Create motor angular velocity plot
        motAngVelPlot = self.createMotAngVelPlot()
        self.motAngVelPlots.append(motAngVelPlot)
        parent.addWidget(motAngVelPlot)

        # Create angular position plot
        angPosPlot = self.createAngPlot('Angular position', 'deg')
        self.angPosPlots.append(angPosPlot)
        parent.addWidget(angPosPlot)
        
        # Create angular velocity plot
        angVelPlot = self.createAngPlot('Angular velocity', 'deg/s')
        self.angVelPlots.append(angVelPlot)
        parent.addWidget(angVelPlot)
        
        # Create arm position display
        self.armPosDisplay = QLabel("Arm position: Unknown")
        parent.addWidget(self.armPosDisplay)
        
        # Create electromagnet status display
        self.magnetStatusDisplay = QLabel("Electromagnet status: Unknown")
        parent.addWidget(self.magnetStatusDisplay)
        
        # Create battery voltage plot
        batVoltPlot = self.createBatVoltPlot()
        self.batVoltPlots.append(batVoltPlot)
        parent.addWidget(batVoltPlot)
        
        # Create current plot
        #eleCurrentPlot = self.createEleCurrentPlot()
        #self.eleCurrentPlots.append(eleCurrentPlot)
        #parent.addWidget(eleCurrentPlot)

    def createMotAngVelPlot(self):
        motAngVelPlot = PlotWidget()
        motAngVelPlot.setLabel('left', 'Motor Angular velocity', units='deg/s')
        motAngVelPlot.setLabel('bottom', 'Time', units='s')
        motAngVelPlot.showGrid(x=True, y=True)
        motAngVelPlot.setYRange(-90, 90)
        motAngVelPlot.setXRange(0, 10)
        motAngVelPlot.addLegend()
        motAngVelPlot.plot(self.motAngVel[0], self.motAngVel[1], name="Motor Angular velocity", pen='r')
        self.plotLines["mosav"].append(motAngVelPlot.addLine(x=None, y=0))
        return motAngVelPlot

    def createAngPlot(self, name="Angular position", units="deg"):
        plot = PlotWidget()
        plot.setLabel('left', name, units=units)
        plot.setLabel('bottom', 'Time', units='s')
        plot.showGrid(x=True, y=True)
        plot.setYRange(-180, 180)
        plot.setXRange(0, 10)
        plot.addLegend()
        plot.plot(self.angVel[0], self.angVel[3], name="Roll", pen='r')
        plot.plot(self.angVel[0], self.angVel[2], name="Pitch", pen='g')
        plot.plot(self.angVel[0], self.angVel[1], name="Yaw", pen='b')
        if name == "Angular position":
            self.plotLines["sangp"].append(plot.addLine(x=None, y=0))
        elif name == "Angular velocity":
            self.plotLines["sangv"].append(plot.addLine(x=None, y=0))
        return plot

    def createEleCurrentPlot(self):
        eleCurrentPlot = PlotWidget()
        eleCurrentPlot.setLabel('left', 'Current', units='mA')
        eleCurrentPlot.setLabel('bottom', 'Time', units='s')
        eleCurrentPlot.showGrid(x=True, y=True)
        eleCurrentPlot.setYRange(0, 10)
        eleCurrentPlot.setXRange(0, 10)
        eleCurrentPlot.addLegend()
        eleCurrentPlot.plot(self.eleCurrent_mA[0], self.eleCurrent_mA[1], name="Current", pen='r')
        return eleCurrentPlot
    
    def createBatVoltPlot(self):
        batVoltPlot = PlotWidget()
        batVoltPlot.setLabel('left', 'Battery voltage', units='V')
        batVoltPlot.setLabel('bottom', 'Time', units='s')
        batVoltPlot.showGrid(x=True, y=True)
        batVoltPlot.setYRange(13, 14)
        batVoltPlot.setXRange(0, 10)
        batVoltPlot.addLegend()
        batVoltPlot.plot(self.batVolt[0], self.batVolt[1], name="Voltage", pen='r')
        return batVoltPlot
    
    def createCustomTab(self, parent):
        plotDict = {}
        self.plotDict = plotDict

        motAngVelPlot = self.createMotAngVelPlot()
        self.motAngVelPlots.append(motAngVelPlot)
        plotDict["Motor angular velocity"] = motAngVelPlot

        angPosPlot = self.createAngPlot('Angular position', 'deg')
        self.angPosPlots.append(angPosPlot)
        plotDict["Angular position"] = angPosPlot

        angVelPlot = self.createAngPlot('Angular velocity', 'deg/s')
        self.angVelPlots.append(angVelPlot)
        plotDict["Angular velocity"] = angVelPlot

        batVoltPlot = self.createBatVoltPlot()
        self.batVoltPlots.append(batVoltPlot)
        plotDict["Battery voltage"] = batVoltPlot

        eleCurrentPlot = self.createEleCurrentPlot()
        self.eleCurrentPlots.append(eleCurrentPlot)
        plotDict["Current"] = eleCurrentPlot

        # Create dropdown for selecting plot
        plotDropdown = QComboBox()
        plotDropdown.addItems(list(plotDict.keys()))
        plotDropdown.currentIndexChanged.connect(lambda i: self.changePlot(i, self.plotDict, parent))
        self.plotDropdown = plotDropdown
        parent.addWidget(plotDropdown)
        parent.addWidget(list(plotDict.values())[0])

        # Create toggle to hide roll and pitch
        hideRollPitchToggle = QPushButton("Hide roll and pitch")
        hideRollPitchToggle.setStyleSheet("font-size: 14pt; font-weight: bold;background-color : darkred")
        hideRollPitchToggle.setCheckable(True)
        hideRollPitchToggle.clicked.connect(lambda: self.setHideRollPitch(hideRollPitchToggle))
        parent.addWidget(hideRollPitchToggle)

    def setHideRollPitch(self, hideRollPitchToggle):
        self.hideRollPitch = hideRollPitchToggle.isChecked()
        self.changeColor(hideRollPitchToggle)

    def changePlot(self, index, plotDict, parent=None):
        if parent is None:
            parent = self.tabCustom.layout
        lastPlot = parent.itemAt(1).widget()
        lastPlot.setParent(None)
        parent.insertWidget(1, list(plotDict.values())[index])
        self.plotDropdown.setCurrentIndex(index)
        #self.plotDropdown.setCurrentText(self.plotDropdown.itemText(index))

        
    def createPIDTab(self, parent):
        # section for pid values
        piMotAngVelLayout = QVBoxLayout()
        # PID label
        piMotAngVelLabel = QLabel("PI motor angular velocity")
        piMotAngVelLabel.setStyleSheet("font-size: 14pt; font-weight: bold;")
        piMotAngVelLabel.setAlignment(QtCore.Qt.AlignTop)
        piMotAngVelLabel.setAlignment(QtCore.Qt.AlignHCenter)
        piMotAngVelLayout.addWidget(piMotAngVelLabel)
        self.createParameter(piMotAngVelLayout, "gkpmw", label="K_p", buttonLabel="Set")
        self.createParameter(piMotAngVelLayout, "gkimw", label="K_i", buttonLabel="Set")
        #self.createParameter(pidLayout, "gkpsa", label="K_d")
        parent.addLayout(piMotAngVelLayout)
        
        piSatAngleLayout = QVBoxLayout()
        piSatAngle = QLabel("PI sat angle")
        piSatAngle.setStyleSheet("font-size: 14pt; font-weight: bold;")
        piSatAngle.setAlignment(QtCore.Qt.AlignTop)
        piSatAngle.setAlignment(QtCore.Qt.AlignHCenter)
        piSatAngleLayout.addWidget(piSatAngle)
        self.createParameter(piSatAngleLayout, "gkpsa", label="K_p", buttonLabel="Set")
        self.createParameter(piSatAngleLayout, "gkisa", label="K_i", buttonLabel="Set")
        parent.addLayout(piSatAngleLayout)
        
        # section for sat angular velocity
        satAngVelLayout = QVBoxLayout()
        satAngVelLabel = QLabel("PI sat angular velocity")
        satAngVelLabel.setStyleSheet("font-size: 14pt; font-weight: bold;")
        satAngVelLabel.setAlignment(QtCore.Qt.AlignTop)
        satAngVelLabel.setAlignment(QtCore.Qt.AlignHCenter)
        satAngVelLayout.addWidget(satAngVelLabel)
        self.createParameter(satAngVelLayout, "gkpsw", label="K_p", buttonLabel="Set")
        self.createParameter(satAngVelLayout, "gkisw", label="K_i", buttonLabel="Set")
        parent.addLayout(satAngVelLayout)
        
        
    def createParameter(self, parent, name, min = 0, max = 2, value = 1, decimalPlaces = 3, label=None, buttonLabel=None, interactable=True, plotIndex=None):
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
        
        # Value display and input
        display = QLineEdit(("{:." + str(decimalPlaces) + "f}").format(value))
        display.setAlignment(QtCore.Qt.AlignCenter)
        display.setStyleSheet("font-size: 12pt;")
        display.setMinimumWidth(70)
        #display.setMaximumWidth(50)
        firstLine.addWidget(display)

        if buttonLabel is not None:
            button = QPushButton(buttonLabel)
            button.setStyleSheet("font-size: 12pt;")
            button.setMinimumWidth(70)
            #button.setMaximumWidth(50)
            #button.clicked.connect(lambda: self.server.sendText(f"{name},{display.text()}"))
            button.clicked.connect(lambda: self.valueChanged(float(display.text()), display, name))
            button.clicked.connect(lambda: self.tabs.setCurrentIndex(3))
            if plotIndex is not None:
                button.clicked.connect(lambda: self.changePlot(plotIndex, self.plotDict))
            firstLine.addWidget(button)
        
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
        #validator.setBottom(0)
        validator.setDecimals(3)
        # make empty string invalid
        validator.setNotation(QDoubleValidator.StandardNotation)
        minInput.setValidator(validator)
        
        # safe textChanged
        
        firstLine.addWidget(minInput)
        
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
        slider.setMinimum(int(min*scale))
        slider.setMaximum(int(max*scale))
        slider.setValue(int(value*scale))
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(int(scale/10))
        if buttonLabel is None and interactable:
            slider.valueChanged.connect(lambda v: self.valueChanged(v/scale, display, name))
        else:
            slider.valueChanged.connect(lambda v: display.setText(str(v/scale)))
        secondLine.addWidget(slider)
        
        # connect textChanged to slider
        display.textChanged.connect(lambda v: condFunc(lambda: slider.setValue(int(float(v)*scale)), isFloat(v)))
        
        minInput.textChanged.connect(lambda v: condFunc(lambda: slider.setMinimum(int(float(v)*scale)), isFloat(v)))
        maxInput.textChanged.connect(lambda v: condFunc(lambda: slider.setMaximum(int(float(v)*scale)), isFloat(v)))

        if not interactable:
            display.setReadOnly(True)
            minInput.setReadOnly(True)
            maxInput.setReadOnly(True)
            slider.setDisabled(True)

        verLayout.addLayout(firstLine)
        verLayout.addLayout(secondLine)
        parent.addLayout(verLayout)
        return display
    
    def valueChanged(self, value, display, name):
        display.setText(str(value))
        #self.server.sendText(json.dumps({name: value}))
        
        if name in self.plotLines:
            for line in self.plotLines[name]:
                line.setValue(value)
                self.controlValues[name] = value
        if name == "exarm" or name == "rearm":
            armPosition = float(self.armPos.text())
            mmValue = value if name == "exarm" else -value
            armPosition += mmValue
            self.armPos.setText(f"{armPosition:.3f}")
            self.server.sendText(f"{name},{(value/self.arm_mmPerMiliSec):.3f}")
        else:
            self.server.sendText(f"{name},{value}")
    
    def subFunction(self, message):
        #print(message)
        if message.startswith('{'):
            msg = json.loads(message)
            if "pitch" in msg:
                self.attitude.setPitch(msg["pitch"])
            if "roll" in msg:
                self.attitude.setRoll(msg["roll"])
            if "blConnected" in msg and msg["blConnected"] == True:
                self.connectionLED.setStyleSheet(self.ledStylesheet("#00CC00"))
        else:
            if ',' not in message:
                return
            msgSplit = message.split(',')
            if not isFloat(msgSplit[0]):
                message = f"{time.time()},{message}"
            teleType = message.split(',')[1].strip()
            if teleType.startswith('motav'):
                self.handleDataPlot(message, self.motAngVel, self.motAngVelPlots, "Motor Angular velocity", lineValue=self.controlValues["mosav"])
            elif teleType.startswith('angve'):
                self.handleAngVel(message)
            elif teleType.startswith('angpo'):
                self.handleAngPos(message)
            elif teleType.startswith('armpo'):
                armState = "Extended" if message.split(',')[2].strip() == "1" else "Retracted"
                self.armPosDisplay.setText(f"Arm position: {armState}")
            elif teleType.startswith('batvo'):
                self.handleDataPlot(message, self.batVolt, self.batVoltPlots, "Voltage")
                if self.batVolt[1][-1] < 12:
                    self.batVoltLED.setStyleSheet(self.ledStylesheet("#FF0000"))
                    self.startBlinkingPowerLED()
            elif teleType.startswith('elcur'):
                self.handleDataPlot(message, self.eleCurrent_mA, self.eleCurrentPlots, "Current")
            elif teleType.startswith('magst'):
                eleState = "On" if message.split(',')[2].strip() == "1" else "Off"
                self.magnetStatusDisplay.setText(f"Electromagnet status: {eleState}")
    
    def handleAngVel(self, message):
        self.handleAngDataPlot(message, self.angVel, self.angVelPlots, self.controlValues["sangv"])
            
    def handleAngPos(self, message):
        msg = message.split(',')
        if len(msg) != 5:
            return
        yaw = clampAngle(float(msg[2])) 
        pitch = clampAngle(float(msg[3]))
        roll = clampAngle(float(msg[4]))
        self.attitude.setRoll(roll)
        self.attitude.setPitch(pitch)
        self.compass.setAngle(yaw)
        clampedMessage = f"{msg[0]},{msg[1]},{roll},{pitch},{yaw}"
        self.handleAngDataPlot(clampedMessage, self.angPos, self.angPosPlots, self.controlValues["sangp"])

    def handleAngDataPlot(self, message, data, plot, lineValue=None):
        msg = message.split(',')
        if len(msg) != 5:
            return
        #self.angPos[0].append(time.time())
        data[0].append(float(msg[0]))
        data[1].append(float(msg[2]))
        data[2].append(float(msg[3]))
        data[3].append(float(msg[4]))
        #data[0] = data[0][-100:]
        #data[1] = data[1][-100:]
        #data[2] = data[2][-100:]
        #data[3] = data[3][-100:]
        # Test if plot is array
        if type(plot) == list:
            for p in plot:
                self.plotAngData(data, p, lineValue)
        else:
            self.plotAngData(data, plot, lineValue)

    def plotAngData(self, data, plot, lineValue=None):
        plot.clear()
        # Plot new data
        if not self.hideRollPitch:
            plot.plot(data[0], data[1], name="Roll", pen='r')
            plot.plot(data[0], data[2], name="Pitch", pen='g')
        plot.plot(data[0], data[3], name="Yaw", pen='b')
        plot.setXRange(data[0][-1] - 10, data[0][-1])
        if lineValue is not None:
            plot.addLine(x=None, y=lineValue)
        
    def handleDataPlot(self, message, data, plot, label, lineValue=None):
        msg = message.split(',')
        if len(msg) != 3:
            return
        #self.angPos[0].append(time.time())
        data[0].append(float(msg[0]))
        data[1].append(float(msg[2]))
        
        if type(plot) == list:
            for p in plot:
                self.plotData(data, p, label, lineValue)
        else:
            self.plotData(data, plot, label, lineValue)

    def plotData(self, data, plot, label, lineValue=None):
        plot.clear()
        # Plot new data
        plot.plot(data[0], data[1], name=label, pen='r')
        plot.setXRange(data[0][-1] - 10, data[0][-1])
        if lineValue is not None:
            plot.addLine(x=None, y=lineValue)
    
    def ledStylesheet(self, color):
        return f"border-radius: 13px; background-color : {color};font-size: 12pt;"
    
    def startBlinkingPowerLED(self):
        timer = QTimer()
        timer.timeout.connect(self.blinkPowerLED)  # execute `display_time`
        timer.setInterval(1000)  # 1000ms = 1s
        timer.start()
        self.blinkPowerLED()

    def blinkPowerLED(self):
        if self.batVoltLED.styleSheet() == self.ledStylesheet("darkRed"):
            self.batVoltLED.setStyleSheet(self.ledStylesheet("#FF0000"))
        else:
            self.batVoltLED.setStyleSheet(self.ledStylesheet("darkRed"))
    
    def __init__(self):
        self.motAngVel = [[], []] # time, angular velocity
        self.angVel = [[], [], [], []] # time, yaw, pitch, roll
        self.angPos = [[], [], [], []] # time, yaw, pitch, roll
        self.batVolt = [[], []] # time, voltage
        self.eleCurrent_mA = [[], []] # time, current

        self.motAngVelPlots = []
        self.angVelPlots = []
        self.angPosPlots = []
        self.batVoltPlots = []
        self.eleCurrentPlots = []

        self.plotLines = {}
        self.controlValues = {}
        for x in ["mosav", "sangp", "sangv"]:
            self.plotLines[x] = []
            self.controlValues[x] = 0

        self.arm_mmPerMiliSec = 30*10**-3
        self.hideRollPitch = False
    
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
            #else:
            #    self.clientConnection.sendTextMessage(message)

    def processBinaryMessage(self,  message):
        pass
        #if (self.clientConnection):
        #    self.clientConnection.sendBinaryMessage(message)

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