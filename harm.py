from icecream import ic # Для дебага

from PyQt5 import QtWidgets  # , QtGui, QtCore
#from PyQt5.QtCore import QThread, QObject
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow

import sys
import time

from harmonic import Ui_MainWindow  #модуль дизайна

# Подключение необходимых модулей для вращения мотора
import serial
import serial.tools.list_ports
import minimalmodbus

# Подключение необходимых модулей для осциллографа
import ctypes
import numpy as np
from picosdk.ps5000a import ps5000a as ps
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc

SERVO_MB_ADDRESS = 16

# ---------- General ----------
global rotatingTime
rotatingTime = 0

# ---------- Motor variables ----------
global motorSpeed, motorAcc, motorDec, motorState, motorTurns, servo
motorSpeed = 60 # rpm
motorAcc = 20
motorDec = 20
motorState = 0
motorTurns = 10

# ---------- Picoscope 5442D ----------
global sampleRates, timeBase, interval, channels, intervals, resolution
resolutions = ["14", "15", "16"]
resolution = 14
ranges = ["10 mV", "20 mV", "50 mV", "100 mV", "200 mV", "500 mV", "1 V", "2 V", "5 V", "10 V", "20 V", "50 V"]
channels = [0, 0, 0, 0]
intervals_14bit_15bit = ["104", "200", "504", "1000", "2000"]
intervals_16bit = ["112", "208", "512", "1008", "2000"]
sampleRates_14bit_15bit = ["9.62 МС/c", "5 МС/c", "1.98 МС/c", "1 МС/c", "500 кС/c"]
sampleRates_16bit = ["8.93 МС/c", "4.81 МС/c", "1.95 МС/c", "992 кС/c", "500 кС/c"]

# Создание объектов chandle, status
chandle = ctypes.c_int16()
status = {}

# ---------- Functions ----------
def rotate():
	''' -- Coil continious rotation --'''
	global motorSpeed, motorAcc, motorDec, motorState, motorTurns, servo
	try:
		motorSpeed = int(application.ui.Speed.text())
		motorAcc = int(application.ui.Acceleration.text())
		motorDec = int(application.ui.Deceleration.text())
		motorTurns = int(application.ui.Turns.text())
		data = [0x0002, 0x0000, 0x0000, motorSpeed, motorAcc, motorDec, 0x0000, 0x0010]
		servo.write_registers(0x6200, data)
		print("rotating..")
	except NameError:
		print("servo not found")


def start():
	''' -- Start coil rotation --'''
	global motorSpeed, motorAcc, motorDec, motorState, motorTurns, servo
	print("start")

def stop():
	''' -- Stop coil rotation --'''
	global servo
	try:
		servo.write_register(0x6002, 0x40, functioncode=6)
		print("stop")
	except NameError:
		print("servo not found")

def init_motor():
	''' -- Initialize motor coil --'''
	global servo
	try:
		servo = minimalmodbus.Instrument(application.ui.cbox_SerialPort.currentText(), SERVO_MB_ADDRESS)
		servo.serial.baudrate = 9600
		servo.serial.parity = serial.PARITY_NONE
		servo.serial.stopbits = 2
		servo.write_register(0x0405, 0x83, functioncode=6)
		application.ui.ServoStatus.setText("Подключен")
		print("servo enabled")
	except:
		application.ui.ServoStatus.setText("Не подключен")
		print("servo not found")

def portChanged():
	global port, servo
	if application.ui.cbox_SerialPort.currentIndex() != -1:
		servo.close()

def calcTime():
	global rotatingTime, motorSpeed, motorTurns
	motorSpeed = int(application.ui.Speed.text())
	motorTurns = int(application.ui.Turns.text())
	rotatingTime = motorTurns/motorSpeed*60
	application.ui.Time.setText(str(rotatingTime))
	ic(rotatingTime)

def updateInterval():
	global timeBase, interval, resolution
	resolution = 0
	if application.ui.Resolution.count() != 0:
		resolution = int(application.ui.Resolution.currentText())
		if resolution in [14, 15]:
			application.ui.Interval.clear()
			application.ui.Interval.addItems(intervals_14bit_15bit)
		elif resolution == 16:
			application.ui.Interval.clear()
			application.ui.Interval.addItems(intervals_16bit)
		interval = int(application.ui.Interval.currentText())
		print(resolution, interval)

def resolutionUpdate():
	global timeBase, interval, resolution, channels
	channels[0] = application.ui.Channel1Enable.checkState()
	channels[1] = application.ui.Channel2Enable.checkState()
	channels[2] = application.ui.Channel3Enable.checkState()
	channels[3] = application.ui.Channel4Enable.checkState()
	if channels.count(2) >= 3:
		application.ui.Resolution.clear()
		application.ui.Resolution.addItems(['14'])
	if channels.count(2) == 2:
		application.ui.Resolution.clear()
		application.ui.Resolution.addItems(['14', '15'])
	if channels.count(2) == 1:
		application.ui.Resolution.clear()
		application.ui.Resolution.addItems(['14', '15', '16 '])

def calcTimeBase():
	global timeBase, interval, resolution
	if resolution in [14, 15]:
		application.ui.SampleRate.setText(sampleRates_14bit_15bit[application.ui.Interval.currentIndex()])
	elif resolution == 16:
		application.ui.SampleRate.setText(sampleRates_16bit[application.ui.Interval.currentIndex()])

def start_record_data():
	''' -- Recording oscilloscope data '''
	global chandle, status
	# Подключение к осциллографу
	# Установка разрешения 12 бит
	resolution = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_12BIT"] # resolution == 0
		
	# Получение статуса и chandle для дальнейшего использования
	status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(chandle),None, resolution) # status["openunit"] == 0
	ic(status["openunit"])
	try:
		assert_pico_ok(status["openunit"])
	except: # PicoNotOkError:
		powerStatus = status["openunit"]
		if powerStatus == 286:
			status["changePowerSource"] = ps.ps5000aChangePowerSource(chandle, powerStatus)
		elif powerStatus == 282:
			status["changePowerSource"] = ps.ps5000aChangePowerSource(chandle, powerStatus)
		else:
			raise assert_pico_ok(status["changePowerSource"])
	
	# Настройка канала A
	# handle = chandle
	channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
	# enabled = 1
	coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]
	chARange = ps.PS5000A_RANGE["PS5000A_20V"]
	# analogue offset = 0 V
	status["setChA"] = ps.ps5000aSetChannel(chandle, channel, 1, coupling_type, chARange, 0)
	ic(status["setChA"])
	assert_pico_ok(status["setChA"])
	
	# Настройка канала B
	# handle = chandle
	channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"]
	# enabled = 1
	# coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]
	chBRange = ps.PS5000A_RANGE["PS5000A_2V"]
	# analogue offset = 0 V
	status["setChB"] = ps.ps5000aSetChannel(chandle, channel, 1, coupling_type, chBRange, 0)
	ic(status["setChB"])
	assert_pico_ok(status["setChB"])
	
	# Получение максимального количества сэмплов АЦП
	maxADC = ctypes.c_int16()
	status["maximumValue"] = ps.ps5000aMaximumValue(chandle,
	ctypes.byref(maxADC))
	assert_pico_ok(status["maximumValue"])

	# Установка количества сэмплов до и после срабатывания триггера
	preTriggerSamples = 100
	postTriggerSamples = 100
	maxSamples = preTriggerSamples + postTriggerSamples
	
	# Установка частоты сэмплирования
	timebase = 8
	timeIntervalns = ctypes.c_float()
	returnedMaxSamples = ctypes.c_int32()
	status["getTimebase2"] = ps.ps5000aGetTimebase2(chandle, timebase, maxSamples, ctypes.byref(timeIntervalns), ctypes.byref(returnedMaxSamples), 0)
	assert_pico_ok(status["getTimebase2"])
	
	# Запуск сбора данных
	status["runBlock"] = ps.ps5000aRunBlock(chandle, preTriggerSamples, postTriggerSamples, timebase, None, 0, None, None)
	assert_pico_ok(status["runBlock"])
	
	# Ожидание готовности данных
	ready = ctypes.c_int16(0)
	check = ctypes.c_int16(0)
	while ready.value == check.value:
		status["isReady"] = ps.ps5000aIsReady(chandle, ctypes.byref(ready))
	
	# Создание буферов данных
	bufferAMax = (ctypes.c_int16 * maxSamples)()
	bufferAMin = (ctypes.c_int16 * maxSamples)()
	bufferBMax = (ctypes.c_int16 * maxSamples)()
	bufferBMin = (ctypes.c_int16 * maxSamples)()
	
	# Указание буфера для сбора данных канала А
	source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
	status["setDataBuffersA"] = ps.ps5000aSetDataBuffers(chandle, source, ctypes.byref(bufferAMax), ctypes.byref(bufferAMin), maxSamples, 0, 0)
	assert_pico_ok(status["setDataBuffersA"])
	
	# Указание буфера для сбора данных канала А
	source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"]
	status["setDataBuffersB"] = ps.ps5000aSetDataBuffers(chandle, source, ctypes.byref(bufferBMax), ctypes.byref(bufferBMin), maxSamples, 0, 0)
	assert_pico_ok(status["setDataBuffersB"])
	
	# Выделение памяти для переполнения
	overflow = ctypes.c_int16()
	
	# Приведение типов
	cmaxSamples = ctypes.c_int32(maxSamples)
	
	# Получение данных из осциллографа в созданные буферы
	status["getValues"] = ps.ps5000aGetValues(chandle, 0, ctypes.byref(cmaxSamples), 0, 0, 0, ctypes.byref(overflow))
	assert_pico_ok(status["getValues"])

	# Преобразование отсчетов АЦП в мВ
	ic(bufferAMax, chARange, maxADC)
	adc2mVChAMax = adc2mV(bufferAMax, chARange, maxADC)
	ic(bufferBMax, chBRange, maxADC)
	adc2mVChBMax = adc2mV(bufferBMax, chBRange, maxADC)
	ic(adc2mVChAMax)
	ic(adc2mVChBMax)

	# Create time data
	time = np.linspace(0, (cmaxSamples.value - 1) * timeIntervalns.value, cmaxSamples.value)

	# plot data from channel A and B
	plt.plot(time, adc2mVChAMax[:])
	plt.plot(time, adc2mVChBMax[:])
	plt.xlabel('Time (ns)')
	plt.ylabel('Voltage (mV)')
	plt.show()
	
def stop_record_data():
	''' -- Stop recording oscilloscope data '''
	global chandle, status
	# Остановка осциллографа
	status["stop"] = ps.ps5000aStop(chandle)
	assert_pico_ok(status["stop"])
	
	# Закрытие и отключение осциллографа
	status["close"]=ps.ps5000aCloseUnit(chandle)
	assert_pico_ok(status["close"])
	print("Data recording stopped")


# ---------- Serial ----------
global port
portList = serial.tools.list_ports.comports(include_links=False)
comPorts = []
for item in portList:
	comPorts.append(item.device)
print("Available COM ports: " + str(comPorts))
#port = serial.Serial(str(comPorts[0]))

class window(QtWidgets.QMainWindow):
	def __init__(self):
		super(window, self).__init__()
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)
		self.setFocus(True)

		for i in range(len(comPorts)):
			self.ui.cbox_SerialPort.addItem(str(comPorts[i]))
		
		#self.ui.cbox_SerialPort.currentIndexChanged.connect(portChanged)
		self.ui.btn_ContRotation.clicked.connect(rotate)
		self.ui.btn_StartRotation.clicked.connect(start)
		self.ui.btn_StopRotation.clicked.connect(stop)
		
		self.ui.btn_StartRecord.clicked.connect(start_record_data)
		self.ui.btn_StopRecord.clicked.connect(stop_record_data)


		self.ui.Connect.clicked.connect(init_motor)
		
		# Init Pico parameters
		#for resolution in resolutions:
		self.ui.Resolution.addItems(resolutions)
		#for rng in ranges:
		self.ui.Channel1Range.addItems(ranges)
		#for rng in ranges:
		self.ui.Channel2Range.addItems(ranges)
		#for rng in ranges:
		self.ui.Channel3Range.addItems(ranges)
		#for rng in ranges:
		self.ui.Channel4Range.addItems(ranges)
		self.ui.Interval.addItems(intervals_14bit_15bit)
		self.ui.SampleRate.setText(sampleRates_14bit_15bit[0])
		
		# Calculate rotation time
		self.ui.Speed.editingFinished.connect(calcTime)
		self.ui.Turns.editingFinished.connect(calcTime)

		# Calculate Picoscope
		self.ui.Resolution.currentIndexChanged.connect(updateInterval)
		self.ui.Interval.currentIndexChanged.connect(calcTimeBase)

		# Checkbox changed
		self.ui.Channel1Enable.stateChanged.connect(resolutionUpdate)
		self.ui.Channel2Enable.stateChanged.connect(resolutionUpdate)
		self.ui.Channel3Enable.stateChanged.connect(resolutionUpdate)
		self.ui.Channel4Enable.stateChanged.connect(resolutionUpdate)
		

app = QtWidgets.QApplication([])
application = window()
application.show()

sys.exit(app.exec_())