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
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc, splitMSODataFast

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
# chandle = ctypes.c_int16()
# status = {}

# ---------- Functions ----------
def rotate():
	''' -- Coil continious rotation --'''
	global motorSpeed, motorAcc, motorDec, motorState, motorTurns, servo
	try:
		motorSpeed = int(harm.ui.Speed.text())
		motorAcc = int(harm.ui.Acceleration.text())
		motorDec = int(harm.ui.Deceleration.text())
		motorTurns = int(harm.ui.Turns.text())
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
		servo = minimalmodbus.Instrument(harm.ui.cbox_SerialPort.currentText(), SERVO_MB_ADDRESS)
		servo.serial.baudrate = 9600
		servo.serial.parity = serial.PARITY_NONE
		servo.serial.stopbits = 2
		servo.write_register(0x0405, 0x83, functioncode=6)
		harm.ui.ServoStatus.setText("Подключен")
		print("servo enabled")
	except:
		harm.ui.ServoStatus.setText("Не подключен")
		print("servo not found")

def portChanged():
	global port, servo
	if harm.ui.cbox_SerialPort.currentIndex() != -1:
		servo.close()

def calcTime():
	global rotatingTime, motorSpeed, motorTurns
	motorSpeed = int(harm.ui.Speed.text())
	motorTurns = int(harm.ui.Turns.text())
	rotatingTime = motorTurns/motorSpeed*60
	harm.ui.Time.setText(str(rotatingTime))

def updateInterval():
	global timeBase, interval, resolution
	resolution = 0
	if harm.ui.Resolution.count() != 0:
		resolution = int(harm.ui.Resolution.currentText())
		if resolution in [14, 15]:
			harm.ui.Interval.clear()
			harm.ui.Interval.addItems(intervals_14bit_15bit)
		elif resolution == 16:
			harm.ui.Interval.clear()
			harm.ui.Interval.addItems(intervals_16bit)
		interval = int(harm.ui.Interval.currentText())
		print(resolution, interval)

def resolutionUpdate():
	global timeBase, interval, resolution, channels
	channels[0] = harm.ui.Channel1Enable.checkState()
	channels[1] = harm.ui.Channel2Enable.checkState()
	channels[2] = harm.ui.Channel3Enable.checkState()
	channels[3] = harm.ui.Channel4Enable.checkState()
	if channels.count(2) >= 3:
		harm.ui.Resolution.clear()
		harm.ui.Resolution.addItems(['14'])
	if channels.count(2) == 2:
		harm.ui.Resolution.clear()
		harm.ui.Resolution.addItems(['14', '15'])
	if channels.count(2) == 1:
		harm.ui.Resolution.clear()
		harm.ui.Resolution.addItems(['14', '15', '16 '])

def calcTimeBase():
	global timeBase, interval, resolution
	if resolution in [14, 15]:
		harm.ui.SampleRate.setText(sampleRates_14bit_15bit[harm.ui.Interval.currentIndex()])
	elif resolution == 16:
		harm.ui.SampleRate.setText(sampleRates_16bit[harm.ui.Interval.currentIndex()])

def setup_analogue_channels():
	''' -- Настройка аналоговых каналов --'''
	harm.chRange = {}
	
	if harm.ui.Channel1Enable.isChecked():
		# Настройка канала A
		# handle = harm.chandle
		channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
		# enabled = 1
		coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]
		chRange["A"] = ps.PS5000A_RANGE["PS5000A_20V"]
		# analogue offset = 0 V
		harm.status["setChA"] = ps.ps5000aSetChannel(harm.chandle, channel, 1, coupling_type, chRange["A"], 0)
		assert_pico_ok(harm.status["setChA"])
	
	if harm.ui.Channel2Enable.isChecked():
		# Настройка канала B
		# handle = harm.chandle
		channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"]
		# enabled = 1
		# coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]
		chRange["B"] = ps.PS5000A_RANGE["PS5000A_2V"]
		# analogue offset = 0 V
		harm.status["setChB"] = ps.ps5000aSetChannel(harm.chandle, channel, 1, coupling_type, chRange["B"], 0)
		assert_pico_ok(harm.status["setChB"])

	if harm.ui.Channel3Enable.isChecked():
		# Настройка канала C
		# handle = harm.chandle
		channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_C"]
		# enabled = 1
		# coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]
		chRange["C"] = ps.PS5000A_RANGE["PS5000A_2V"]
		# analogue offset = 0 V
		harm.status["setChC"] = ps.ps5000aSetChannel(harm.chandle, channel, 1, coupling_type, chRange["C"], 0)
		assert_pico_ok(harm.status["setChC"])

	if harm.ui.Channel4Enable.isChecked():
		# Настройка канала D
		# handle = harm.chandle
		channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_D"]
		# enabled = 1
		# coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]
		chRange["D"] = ps.PS5000A_RANGE["PS5000A_2V"]
		# analogue offset = 0 V
		harm.status["setChD"] = ps.ps5000aSetChannel(harm.chandle, channel, 1, coupling_type, chRange["D"], 0)
		assert_pico_ok(harm.status["setChD"])

	return chRange

def setup_digital_channels():
	''' -- Настройка цифровых каналов --'''
	digital_port0 = ps.PS5000A_CHANNEL["PS5000A_DIGITAL_PORT0"]
	ic(digital_port0)
	# Set up digital port
	# handle = harm.chandle
	# channel = ps5000a_DIGITAL_PORT0 = 0x80
	# enabled = 1
	# logicLevel = 10000
	harm.status["SetDigitalPort"] = ps.ps5000aSetDigitalPort(harm.chandle, digital_port0, 1, 10000)
	assert_pico_ok(harm.status["SetDigitalPort"])

def start_record_data():
	''' -- Recording oscilloscope data --'''

	# global chandle, status
	# Подключение к осциллографу
	# Установка разрешения 12 бит
	resolution = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_12BIT"] # resolution == 0
		
	# Получение статуса и chandle для дальнейшего использования
	harm.status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(harm.chandle), None, resolution) # 
	try:
		assert_pico_ok(harm.status["openunit"])
	except: # PicoNotOkError:
		powerStatus = harm.status["openunit"]
		if powerStatus == 286:
			harm.status["changePowerSource"] = ps.ps5000aChangePowerSource(harm.chandle, powerStatus)
		elif powerStatus == 282:
			harm.status["changePowerSource"] = ps.ps5000aChangePowerSource(harm.chandle, powerStatus)
		else:
			raise assert_pico_ok(harm.status["changePowerSource"])

	setup_analogue_channels()
	setup_digital_channels()

	# Получение максимального количества сэмплов АЦП
	maxADC = ctypes.c_int16()
	harm.status["maximumValue"] = ps.ps5000aMaximumValue(harm.chandle, ctypes.byref(maxADC))
	assert_pico_ok(harm.status["maximumValue"])

	# Установка количества сэмплов до и после срабатывания триггера
	preTriggerSamples = 2500
	postTriggerSamples = 2500
	maxSamples = preTriggerSamples + postTriggerSamples
	
	# Установка частоты сэмплирования
	timebase = 80000
	timeIntervalns = ctypes.c_float()
	returnedMaxSamples = ctypes.c_int32()
	harm.status["getTimebase2"] = ps.ps5000aGetTimebase2(harm.chandle, timebase, maxSamples, ctypes.byref(timeIntervalns), ctypes.byref(returnedMaxSamples), 0)
	assert_pico_ok(harm.status["getTimebase2"])
	
	# Запуск сбора данных
	harm.status["runBlock"] = ps.ps5000aRunBlock(harm.chandle, preTriggerSamples, postTriggerSamples, timebase, None, 0, None, None)
	assert_pico_ok(harm.status["runBlock"])
	
	# Ожидание готовности данных
	ready = ctypes.c_int16(0)
	check = ctypes.c_int16(0)
	while ready.value == check.value:
		harm.status["isReady"] = ps.ps5000aIsReady(harm.chandle, ctypes.byref(ready))
	
	# Создание буферов данных
	bufferAMax = (ctypes.c_int16 * maxSamples)()
	bufferAMin = (ctypes.c_int16 * maxSamples)()
	bufferBMax = (ctypes.c_int16 * maxSamples)()
	bufferBMin = (ctypes.c_int16 * maxSamples)()
	bufferCMax = (ctypes.c_int16 * maxSamples)()
	bufferCMin = (ctypes.c_int16 * maxSamples)()
	bufferDMax = (ctypes.c_int16 * maxSamples)()
	bufferDMin = (ctypes.c_int16 * maxSamples)()

	# Create buffers ready for assigning pointers for data collection
	bufferDPort0Max = (ctypes.c_int16 * maxSamples)()
	bufferDPort0Min = (ctypes.c_int16 * maxSamples)()
	
	if harm.ui.Channel1Enable.isChecked():
		# Указание буфера для сбора данных канала А
		source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
		harm.status["setDataBuffersA"] = ps.ps5000aSetDataBuffers(harm.chandle, source, ctypes.byref(bufferAMax), ctypes.byref(bufferAMin), maxSamples, 0, 0)
		assert_pico_ok(harm.status["setDataBuffersA"])
	
	if harm.ui.Channel2Enable.isChecked():
		# Указание буфера для сбора данных канала B
		source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"]
		harm.status["setDataBuffersB"] = ps.ps5000aSetDataBuffers(harm.chandle, source, ctypes.byref(bufferBMax), ctypes.byref(bufferBMin), maxSamples, 0, 0)
		assert_pico_ok(harm.status["setDataBuffersB"])

	if harm.ui.Channel3Enable.isChecked():
		# Указание буфера для сбора данных канала C
		source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_C"]
		harm.status["setDataBuffersC"] = ps.ps5000aSetDataBuffers(harm.chandle, source, ctypes.byref(bufferCMax), ctypes.byref(bufferCMin), maxSamples, 0, 0)
		assert_pico_ok(harm.status["setDataBuffersC"])

	if harm.ui.Channel4Enable.isChecked():
		# Указание буфера для сбора данных канала D
		source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_D"]
		harm.status["setDataBuffersD"] = ps.ps5000aSetDataBuffers(harm.chandle, source, ctypes.byref(bufferDMax), ctypes.byref(bufferDMin), maxSamples, 0, 0)
		assert_pico_ok(harm.status["setDataBuffersD"])

	# Указание буфера для сбора данных цифрового канала ps5000a_DIGITAL_PORT0
	# handle = harm.chandle
	# source = ps.ps5000a_DIGITAL_PORT0    # == 0x80
	digital_port0 = ps.PS5000A_CHANNEL["PS5000A_DIGITAL_PORT0"]
	ic(digital_port0)
	# Buffer max = ctypes.byref(bufferDPort0Max)
	# Buffer min = ctypes.byref(bufferDPort0Min)
	# Buffer length = totalSamples
	# Segment index = 0
	# Ratio mode = ps5000a_RATIO_MODE_NONE = 0
	harm.status["SetDataBuffersDigital"] = ps.ps5000aSetDataBuffers(harm.chandle, digital_port0, ctypes.byref(bufferDPort0Max), ctypes.byref(bufferDPort0Min), maxSamples, 0, 0)
	assert_pico_ok(harm.status["SetDataBuffersDigital"])

	print("Starting data collection...")

	# Выделение памяти для переполнения
	overflow = ctypes.c_int16()
	
	# Приведение типов
	cmaxSamples = ctypes.c_int32(maxSamples)
	
	# Получение данных из осциллографа в созданные буферы
	harm.status["getValues"] = ps.ps5000aGetValues(harm.chandle, 0, ctypes.byref(cmaxSamples), 0, 0, 0, ctypes.byref(overflow))
	assert_pico_ok(harm.status["getValues"])

	print("Data collection complete.")

	# Преобразование отсчетов АЦП в мВ
	if harm.ui.Channel1Enable.isChecked():
		adc2mVChAMax = adc2mV(bufferAMax, chRange["A"], maxADC)
	if harm.ui.Channel2Enable.isChecked():
		adc2mVChBMax = adc2mV(bufferBMax, chRange["B"], maxADC)
	if harm.ui.Channel3Enable.isChecked():
		adc2mVChCMax = adc2mV(bufferCMax, chRange["C"], maxADC)
	if harm.ui.Channel4Enable.isChecked():
		adc2mVChDMax = adc2mV(bufferDMax, chRange["D"], maxADC)

	# Obtain binary for Digital Port 0
	# The tuple returned contains the channels in order (D7, D6, D5, ... D0).
	bufferDPort0 = splitMSODataFast(cmaxSamples, bufferDPort0Max)

	# Create time data
	time = np.linspace(0, (cmaxSamples.value - 1) * timeIntervalns.value, cmaxSamples.value)

	# plot data from channel A and B
	# plt.subplot(1, 2, 1)
	plt.figure(num='PicoScope 5000a Series (A API) analogue ports')
	plt.title('Plot of Analogue Ports vs. time')
	if harm.ui.Channel1Enable.isChecked():
		plt.plot(time, adc2mVChAMax[:])
	if harm.ui.Channel2Enable.isChecked():
		plt.plot(time, adc2mVChBMax[:])
	if harm.ui.Channel3Enable.isChecked():
		plt.plot(time, adc2mVChCMax[:])
	if harm.ui.Channel4Enable.isChecked():
		plt.plot(time, adc2mVChDMax[:])
	plt.xlabel('Time (ns)')
	plt.ylabel('Voltage (mV)')
	
	# plt.subplot(1, 2, 2)
	plt.figure(num='PicoScope 5000a Series (A API) digital ports')
	plt.title('Plot of Digital Port 0 digital channels vs. time')
	# plt.plot(time, bufferDPort0[0], label='D7')  # D7 is the first array in the tuple.
	# plt.plot(time, bufferDPort0[1], label='D6')
	# plt.plot(time, bufferDPort0[2], label='D5')
	plt.plot(time, bufferDPort0[3], label='D4')
	# plt.plot(time, bufferDPort0[4], label='D3')
	# plt.plot(time, bufferDPort0[5], label='D2')
	# plt.plot(time, bufferDPort0[6], label='D1')
	plt.plot(time, bufferDPort0[7], label='D0')  # D0 is the last array in the tuple.
	plt.xlabel('Time (ns)')
	plt.ylabel('Logic Level')
	plt.legend(loc="upper right")
	
	plt.show()
	
def stop_record_data():
	''' -- Stop recording oscilloscope data '''
	# global chandle, status
	# Остановка осциллографа
	status["stop"] = ps.ps5000aStop(harm.chandle)
	assert_pico_ok(status["stop"])
	
	# Закрытие и отключение осциллографа
	status["close"]=ps.ps5000aCloseUnit(harm.chandle)
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

		# Создание объектов chandle, status
		self.chandle = ctypes.c_int16()
		self.status = {}

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
		
if __name__ == "__main__":
	app = QtWidgets.QApplication([])
	harm = window()
	harm.show()

	sys.exit(app.exec_())