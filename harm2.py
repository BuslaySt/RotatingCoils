from icecream import ic # Для дебага
from time import time

from PyQt5 import QtWidgets
from harmonic import Ui_MainWindow  #модуль дизайна

import sys
# import time
import pandas as pd
import numpy as np

# Подключение необходимых модулей для вращения мотора
import serial
import serial.tools.list_ports
import minimalmodbus

# Подключение необходимых модулей для осциллографа
import ctypes
import matplotlib.pyplot as plt
from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc, splitMSODataFast

# ---------- Functions ----------
def rotate() -> None:
	''' -- Coil continious rotation --'''
	try:
		harm.motorSpeed = int(harm.ui.Speed.text())
		harm.motorAcc = int(harm.ui.Acceleration.text())
		harm.motorDec = int(harm.ui.Deceleration.text())
		harm.motorTurns = int(harm.ui.Turns.text())
		data = [0x0002, 0x0000, 0x0000, harm.motorSpeed, harm.motorAcc, harm.motorDec, 0x0000, 0x0010]
		harm.servo.write_registers(0x6200, data)
		print("rotating..")
	except NameError:
		print("servo not found")

def start() -> None:
	''' -- Start coil rotation --'''
	print("start")

def stop() -> None:
	''' -- Stop coil rotation --'''
	try:
		harm.servo.write_register(0x6002, 0x40, functioncode=6)
		print("stop")
	except NameError:
		print("servo not found")

def init_motor() -> None:
	''' -- Initialize motor coil --'''
	try:
		harm.servo = minimalmodbus.Instrument(harm.ui.cbox_SerialPort.currentText(), harm.SERVO_MB_ADDRESS)
		harm.servo.serial.baudrate = 9600
		harm.servo.serial.parity = serial.PARITY_NONE
		harm.servo.serial.stopbits = 2
		harm.servo.write_register(0x0405, 0x83, functioncode=6)
		harm.ui.ServoStatus.setText("Подключен")
		print("servo enabled")
	except:
		harm.ui.ServoStatus.setText("Не подключен")
		print("servo not found")

def portChanged() -> None:
	if harm.ui.cbox_SerialPort.currentIndex() != -1:
		harm.servo.close()

def calcTime() -> None:
	harm.motorSpeed = int(harm.ui.Speed.text())
	harm.motorTurns = int(harm.ui.Turns.text())
	harm.rotatingTime = harm.motorTurns/harm.motorSpeed*60
	harm.ui.Time.setText(str(harm.rotatingTime))

def updateInterval() -> None:
	harm.resolution = 0
	if harm.ui.Resolution.count() != 0:
		harm.resolution = int(harm.ui.Resolution.currentText())
		if harm.resolution in [14, 15]:
			harm.ui.Interval.clear()
			harm.ui.Interval.addItems(harm.intervals_14bit_15bit)
			harm.ui.Interval.setCurrentText('504')
		elif harm.resolution == 16:
			harm.ui.Interval.clear()
			harm.ui.Interval.addItems(harm.intervals_16bit)
			harm.ui.Interval.setCurrentText('512')
		harm.interval = harm.ui.Interval.currentText()

def resolutionUpdate() -> None:
	''' Выбор битности разрешения в зависимости от количества используемых каналов '''
	harm.channels[0] = harm.ui.Channel1Enable.checkState()
	harm.channels[1] = harm.ui.Channel2Enable.checkState()
	harm.channels[2] = harm.ui.Channel3Enable.checkState()
	harm.channels[3] = harm.ui.Channel4Enable.checkState()
	if harm.channels.count(2) >= 3:
		harm.ui.Resolution.clear()
		harm.ui.Resolution.addItems(['14'])
	if harm.channels.count(2) == 2:
		harm.ui.Resolution.clear()
		harm.ui.Resolution.addItems(['14', '15'])
		harm.ui.Resolution.setCurrentText('15')
	if harm.channels.count(2) == 1:
		harm.ui.Resolution.clear()
		harm.ui.Resolution.addItems(['14', '15', '16'])
	harm.ui.Resolution.setCurrentText('16')

def calcTimeBase() -> None:
	if harm.resolution in [14, 15]:
		harm.ui.SampleRate.setText(harm.sampleRates_14bit_15bit[harm.ui.Interval.currentIndex()])
	elif harm.resolution == 16:
		harm.ui.SampleRate.setText(harm.sampleRates_16bit[harm.ui.Interval.currentIndex()])
	harm.interval = harm.ui.Interval.currentText()

def open_scope_unit():
	match harm.resolution:
		case 14:	resolution_code = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_14BIT"]
		case 15:	resolution_code = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_15BIT"]
		case 16:	resolution_code = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_16BIT"]
		
	# Получение статуса и chandle для дальнейшего использования
	harm.status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(harm.chandle), None, resolution_code) # 
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

def setup_analogue_channels() -> None:
	''' -- Настройка аналоговых каналов --'''
	harm.chRange = {}
	coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]	

	# Настройка канала A
	# handle = harm.chandle
	channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
	# enabled = 1
	enabledA = 1 if harm.ui.Channel1Enable.isChecked() else 0
	# coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]
	match harm.ui.Channel1Range.currentText():
		case "10 mV": 	harm.chRange["A"] = ps.PS5000A_RANGE["PS5000A_10MV"]
		case "20 mV": 	harm.chRange["A"] = ps.PS5000A_RANGE["PS5000A_20MV"]
		case "50 mV": 	harm.chRange["A"] = ps.PS5000A_RANGE["PS5000A_50MV"]
		case "100 mV": 	harm.chRange["A"] = ps.PS5000A_RANGE["PS5000A_100MV"]
		case "200 mV": 	harm.chRange["A"] = ps.PS5000A_RANGE["PS5000A_200MV"]
		case "500 mV": 	harm.chRange["A"] = ps.PS5000A_RANGE["PS5000A_500MV"]
		case "1 V": 	harm.chRange["A"] = ps.PS5000A_RANGE["PS5000A_1V"]
		case "2 V": 	harm.chRange["A"] = ps.PS5000A_RANGE["PS5000A_2V"]
		case "5 V": 	harm.chRange["A"] = ps.PS5000A_RANGE["PS5000A_5V"]
		case "10 V": 	harm.chRange["A"] = ps.PS5000A_RANGE["PS5000A_10V"]
		case "20 V": 	harm.chRange["A"] = ps.PS5000A_RANGE["PS5000A_20V"]
		case "50 V": 	harm.chRange["A"] = ps.PS5000A_RANGE["PS5000A_50V"]
	# analogue offset = 0 V
	harm.status["setChA"] = ps.ps5000aSetChannel(harm.chandle, channel, enabledA, coupling_type, harm.chRange["A"], 0)
	assert_pico_ok(harm.status["setChA"])
	
	# Настройка канала B
	# handle = harm.chandle
	channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"]
	# enabled = 1
	enabledB = 1 if harm.ui.Channel2Enable.isChecked() else 0
	# coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]
	match harm.ui.Channel2Range.currentText():
		case "10 mV": 	harm.chRange["B"] = ps.PS5000A_RANGE["PS5000A_10MV"]
		case "20 mV": 	harm.chRange["B"] = ps.PS5000A_RANGE["PS5000A_20MV"]
		case "50 mV": 	harm.chRange["B"] = ps.PS5000A_RANGE["PS5000A_50MV"]
		case "100 mV": 	harm.chRange["B"] = ps.PS5000A_RANGE["PS5000A_100MV"]
		case "200 mV": 	harm.chRange["B"] = ps.PS5000A_RANGE["PS5000A_200MV"]
		case "500 mV": 	harm.chRange["B"] = ps.PS5000A_RANGE["PS5000A_500MV"]
		case "1 V": 	harm.chRange["B"] = ps.PS5000A_RANGE["PS5000A_1V"]
		case "2 V": 	harm.chRange["B"] = ps.PS5000A_RANGE["PS5000A_2V"]
		case "5 V": 	harm.chRange["B"] = ps.PS5000A_RANGE["PS5000A_5V"]
		case "10 V": 	harm.chRange["B"] = ps.PS5000A_RANGE["PS5000A_10V"]
		case "20 V": 	harm.chRange["B"] = ps.PS5000A_RANGE["PS5000A_20V"]
		case "50 V": 	harm.chRange["B"] = ps.PS5000A_RANGE["PS5000A_50V"]
	# analogue offset = 0 V
	harm.status["setChB"] = ps.ps5000aSetChannel(harm.chandle, channel, enabledB, coupling_type, harm.chRange["B"], 0)
	assert_pico_ok(harm.status["setChB"])

	
	# Настройка канала C
	# handle = harm.chandle
	channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_C"]
	# enabled = 1
	enabledC = 1 if harm.ui.Channel3Enable.isChecked() else 0
	# coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]
	match harm.ui.Channel3Range.currentText():
		case "10 mV": 	harm.chRange["C"] = ps.PS5000A_RANGE["PS5000A_10MV"]
		case "20 mV": 	harm.chRange["C"] = ps.PS5000A_RANGE["PS5000A_20MV"]
		case "50 mV": 	harm.chRange["C"] = ps.PS5000A_RANGE["PS5000A_50MV"]
		case "100 mV": 	harm.chRange["C"] = ps.PS5000A_RANGE["PS5000A_100MV"]
		case "200 mV": 	harm.chRange["C"] = ps.PS5000A_RANGE["PS5000A_200MV"]
		case "500 mV": 	harm.chRange["C"] = ps.PS5000A_RANGE["PS5000A_500MV"]
		case "1 V": 	harm.chRange["C"] = ps.PS5000A_RANGE["PS5000A_1V"]
		case "2 V": 	harm.chRange["C"] = ps.PS5000A_RANGE["PS5000A_2V"]
		case "5 V": 	harm.chRange["C"] = ps.PS5000A_RANGE["PS5000A_5V"]
		case "10 V": 	harm.chRange["C"] = ps.PS5000A_RANGE["PS5000A_10V"]
		case "20 V": 	harm.chRange["C"] = ps.PS5000A_RANGE["PS5000A_20V"]
		case "50 V": 	harm.chRange["C"] = ps.PS5000A_RANGE["PS5000A_50V"]
	# analogue offset = 0 V
	harm.status["setChC"] = ps.ps5000aSetChannel(harm.chandle, channel, enabledC, coupling_type, harm.chRange["C"], 0)
	assert_pico_ok(harm.status["setChC"])

	# Настройка канала D
	# handle = harm.chandle
	channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_D"]
	# enabled = 1
	enabledD = 1 if harm.ui.Channel4Enable.isChecked() else 0
	# coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]
	match harm.ui.Channel4Range.currentText():
		case "10 mV": 	harm.chRange["D"] = ps.PS5000A_RANGE["PS5000A_10MV"]
		case "20 mV": 	harm.chRange["D"] = ps.PS5000A_RANGE["PS5000A_20MV"]
		case "50 mV": 	harm.chRange["D"] = ps.PS5000A_RANGE["PS5000A_50MV"]
		case "100 mV": 	harm.chRange["D"] = ps.PS5000A_RANGE["PS5000A_100MV"]
		case "200 mV": 	harm.chRange["D"] = ps.PS5000A_RANGE["PS5000A_200MV"]
		case "500 mV": 	harm.chRange["D"] = ps.PS5000A_RANGE["PS5000A_500MV"]
		case "1 V": 	harm.chRange["D"] = ps.PS5000A_RANGE["PS5000A_1V"]
		case "2 V": 	harm.chRange["D"] = ps.PS5000A_RANGE["PS5000A_2V"]
		case "5 V": 	harm.chRange["D"] = ps.PS5000A_RANGE["PS5000A_5V"]
		case "10 V": 	harm.chRange["D"] = ps.PS5000A_RANGE["PS5000A_10V"]
		case "20 V": 	harm.chRange["D"] = ps.PS5000A_RANGE["PS5000A_20V"]
		case "50 V": 	harm.chRange["D"] = ps.PS5000A_RANGE["PS5000A_50V"]
	# analogue offset = 0 V
	harm.status["setChD"] = ps.ps5000aSetChannel(harm.chandle, channel, enabledD, coupling_type, harm.chRange["D"], 0)
	assert_pico_ok(harm.status["setChD"])

def setup_digital_channels() -> None:
	''' -- Настройка цифровых каналов --'''
	digital_port0 = ps.PS5000A_CHANNEL["PS5000A_DIGITAL_PORT0"]
	# Set up digital port
	# handle = harm.chandle
	# channel = ps5000a_DIGITAL_PORT0 = 0x80
	# enabled = 1
	# logicLevel = 10000
	harm.status["SetDigitalPort"] = ps.ps5000aSetDigitalPort(harm.chandle, digital_port0, 1, 10000)
	assert_pico_ok(harm.status["SetDigitalPort"])

def get_max_ADC_samples() -> None:
	''' Получение максимального количества сэмплов АЦП '''
	harm.maxADC = ctypes.c_int16()
	harm.status["maximumValue"] = ps.ps5000aMaximumValue(harm.chandle, ctypes.byref(harm.maxADC))
	assert_pico_ok(harm.status["maximumValue"])

def set_max_samples() -> None:
	''' Установка количества сэмплов до и после срабатывания триггера '''
	harm.preTriggerSamples = 0
	harm.postTriggerSamples = 10000000
	harm.maxSamples = harm.preTriggerSamples + harm.postTriggerSamples

def set_timebase() -> None:
	# Установка частоты сэмплирования
	if harm.resolution in [14, 15]:
		harm.timebase = harm.intervals_14bit_15bit[harm.interval] # 65 == 504 нс
	elif harm.resolution == 16:
		harm.timebase = harm.intervals_16bit[harm.interval] # 25 == 512 нс
	harm.timeIntervalns = ctypes.c_float()
	returnedMaxSamples = ctypes.c_int32()
	harm.status["getTimebase2"] = ps.ps5000aGetTimebase2(harm.chandle, harm.timebase, harm.maxSamples, ctypes.byref(harm.timeIntervalns), ctypes.byref(returnedMaxSamples), 0)
	assert_pico_ok(harm.status["getTimebase2"])

def set_digital_trigger():
	# set the digital trigger for a high bit on digital channel 4
	conditions = ps.PS5000A_CONDITION(ps.PS5000A_CHANNEL["PS5000A_DIGITAL_PORT0"], ps.PS5000A_TRIGGER_STATE["PS5000A_CONDITION_TRUE"])
	nConditions = 1
	clear = 1
	add = 2
	info = clear + add
	harm.status["setTriggerChannelConditionsV2"] = ps.ps5000aSetTriggerChannelConditionsV2(harm.chandle,
																					ctypes.byref(conditions),
																					nConditions,
																					info)
	assert_pico_ok(harm.status["setTriggerChannelConditionsV2"])

	directions = ps.PS5000A_DIGITAL_CHANNEL_DIRECTIONS(ps.PS5000A_DIGITAL_CHANNEL["PS5000A_DIGITAL_CHANNEL_4"], ps.PS5000A_DIGITAL_DIRECTION["PS5000A_DIGITAL_DIRECTION_HIGH"])
	nDirections = 1
	harm.status["setTriggerDigitalPortProperties"] = ps.ps5000aSetTriggerDigitalPortProperties(harm.chandle,
																						ctypes.byref(directions),
																						nDirections)
	assert_pico_ok(harm.status["setTriggerDigitalPortProperties"])

	# set autotrigger timeout value
	harm.status["autoTriggerus"] = ps.ps5000aSetAutoTriggerMicroSeconds(harm.chandle, 10000)
	assert_pico_ok(harm.status["autoTriggerus"])

def start_record_data() -> None:

	''' -- Recording oscilloscope data --'''
	# Подключение к осциллографу
	# Установка разрешения
	time1 = time()	
	open_scope_unit()
		
	setup_analogue_channels()
	setup_digital_channels()

	get_max_ADC_samples()
	set_max_samples()
	set_timebase()

	# Запуск сбора данных
	harm.status["runBlock"] = ps.ps5000aRunBlock(harm.chandle, harm.preTriggerSamples, harm.postTriggerSamples, harm.timebase, None, 0, None, None)
	assert_pico_ok(harm.status["runBlock"])
	
	# Ожидание готовности данных
	ready = ctypes.c_int16(0)
	check = ctypes.c_int16(0)
	while ready.value == check.value:
		harm.status["isReady"] = ps.ps5000aIsReady(harm.chandle, ctypes.byref(ready))
	
	# Создание буферов данных
	bufferAMax = (ctypes.c_int16 * harm.maxSamples)()
	bufferAMin = (ctypes.c_int16 * harm.maxSamples)()
	bufferBMax = (ctypes.c_int16 * harm.maxSamples)()
	bufferBMin = (ctypes.c_int16 * harm.maxSamples)()
	bufferCMax = (ctypes.c_int16 * harm.maxSamples)()
	bufferCMin = (ctypes.c_int16 * harm.maxSamples)()
	bufferDMax = (ctypes.c_int16 * harm.maxSamples)()
	bufferDMin = (ctypes.c_int16 * harm.maxSamples)()

	# Create buffers ready for assigning pointers for data collection
	bufferDPort0Max = (ctypes.c_int16 * harm.maxSamples)()
	bufferDPort0Min = (ctypes.c_int16 * harm.maxSamples)()
	
	if harm.ui.Channel1Enable.isChecked():
		# Указание буфера для сбора данных канала А
		source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
		harm.status["setDataBuffersA"] = ps.ps5000aSetDataBuffers(harm.chandle, source, ctypes.byref(bufferAMax), ctypes.byref(bufferAMin), harm.maxSamples, 0, 0)
		assert_pico_ok(harm.status["setDataBuffersA"])
	
	if harm.ui.Channel2Enable.isChecked():
		# Указание буфера для сбора данных канала B
		source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"]
		harm.status["setDataBuffersB"] = ps.ps5000aSetDataBuffers(harm.chandle, source, ctypes.byref(bufferBMax), ctypes.byref(bufferBMin), harm.maxSamples, 0, 0)
		assert_pico_ok(harm.status["setDataBuffersB"])

	if harm.ui.Channel3Enable.isChecked():
		# Указание буфера для сбора данных канала C
		source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_C"]
		harm.status["setDataBuffersC"] = ps.ps5000aSetDataBuffers(harm.chandle, source, ctypes.byref(bufferCMax), ctypes.byref(bufferCMin), harm.maxSamples, 0, 0)
		assert_pico_ok(harm.status["setDataBuffersC"])

	if harm.ui.Channel4Enable.isChecked():
		# Указание буфера для сбора данных канала D
		source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_D"]
		harm.status["setDataBuffersD"] = ps.ps5000aSetDataBuffers(harm.chandle, source, ctypes.byref(bufferDMax), ctypes.byref(bufferDMin), harm.maxSamples, 0, 0)
		assert_pico_ok(harm.status["setDataBuffersD"])

	# Указание буфера для сбора данных цифрового канала ps5000a_DIGITAL_PORT0
	# handle = harm.chandle
	# source = ps.ps5000a_DIGITAL_PORT0    # == 0x80
	digital_port0 = ps.PS5000A_CHANNEL["PS5000A_DIGITAL_PORT0"]
	# Buffer max = ctypes.byref(bufferDPort0Max)
	# Buffer min = ctypes.byref(bufferDPort0Min)
	# Buffer length = totalSamples
	# Segment index = 0
	# Ratio mode = ps5000a_RATIO_MODE_NONE = 0
	harm.status["SetDataBuffersDigital"] = ps.ps5000aSetDataBuffers(harm.chandle, digital_port0, ctypes.byref(bufferDPort0Max), ctypes.byref(bufferDPort0Min), harm.maxSamples, 0, 0)
	assert_pico_ok(harm.status["SetDataBuffersDigital"])

	set_digital_trigger()

	print("Starting data collection...")

	# Выделение памяти для переполнения
	overflow = ctypes.c_int16()
	
	# Приведение типов
	cmaxSamples = ctypes.c_int32(harm.maxSamples)
	
	# Получение данных из осциллографа в созданные буферы
	harm.status["getValues"] = ps.ps5000aGetValues(harm.chandle, 0, ctypes.byref(cmaxSamples), 0, 0, 0, ctypes.byref(overflow))
	assert_pico_ok(harm.status["getValues"])

	print("Data collection complete.")
	stop_record_data()

	# Create time data
	time_axis = np.linspace(0, (cmaxSamples.value - 1) * harm.timeIntervalns.value, cmaxSamples.value)
	harm.df['timestamp'] = time_axis

	# Преобразование отсчетов АЦП в мВ
	if harm.ui.Channel1Enable.isChecked():
		adc2mVChAMax = adc2mV(bufferAMax, harm.chRange["A"], harm.maxADC)
		harm.df['ch_a'] = adc2mVChAMax
	if harm.ui.Channel2Enable.isChecked():
		adc2mVChBMax = adc2mV(bufferBMax, harm.chRange["B"], harm.maxADC)
		harm.df['ch_b'] = adc2mVChBMax
	if harm.ui.Channel3Enable.isChecked():
		adc2mVChCMax = adc2mV(bufferCMax, harm.chRange["C"], harm.maxADC)
		harm.df['ch_c'] = adc2mVChCMax
	if harm.ui.Channel4Enable.isChecked():
		adc2mVChDMax = adc2mV(bufferDMax, harm.chRange["D"], harm.maxADC)
		harm.df['ch_d'] = adc2mVChDMax

	# Obtain binary for Digital Port 0
	# The tuple returned contains the channels in order (D7, D6, D5, ... D0).
	bufferDPort0 = splitMSODataFast(cmaxSamples, bufferDPort0Max)
	harm.df['D0'] = bufferDPort0[7]
	harm.df['D4'] = bufferDPort0[3]

	time2 = time()
	ic(time2-time1)

	ic(harm.df.info())
	ic(harm.df.head())
	ic(harm.df.describe())
	
	# harm.df['D0'] = harm.df['D0'].apply(int)
	# harm.df['D4'] = harm.df['D4'].apply(int)

	plot_data()


def plot_data() -> None:
	# plot data from analogue and digital channels 
	plt.figure(num='PicoScope 5000a ports')

	plt.subplot(3,1,1)
	plt.title("Plot of ports' data vs. time")
	if harm.ui.Channel1Enable.isChecked():
		plt.plot(harm.df['timestamp'], harm.df['ch_a'], label='ch A')
	if harm.ui.Channel2Enable.isChecked():
		plt.plot(harm.df['timestamp'], harm.df['ch_b'][:], label='ch B')
	plt.xlabel('Time (ns)')
	plt.ylabel('Voltage (mV)')
	plt.legend(loc="upper right")

	plt.subplot(3,1,2)
	if harm.ui.Channel3Enable.isChecked():
		plt.plot(harm.df['timestamp'], harm.df['ch_c'][:], label='ch C')
	if harm.ui.Channel4Enable.isChecked():
		plt.plot(harm.df['timestamp'], harm.df['ch_d'][:], label='ch D')
	plt.xlabel('Time (ns)')
	plt.ylabel('Voltage (mV)')
	plt.legend(loc="upper right")

	# plt.figure(num='PicoScope 5000a digital ports')
	
	# plt.title('Plot of Digital Port 0 digital channels vs. time')
	# plt.plot(harm.df['timestamp'], harm.df['D7'], label='D7')  # D7 is the first array in the tuple.
	# plt.plot(harm.df['timestamp'], harm.df['D6'], label='D6')
	# plt.plot(harm.df['timestamp'], harm.df['D5'], label='D5')
	plt.subplot(3,1,3)
	plt.plot(harm.df['timestamp'], harm.df['D4'], label='D4')
	# plt.plot(harm.df['timestamp'], harm.df['D3'], label='D3')
	# plt.plot(harm.df['timestamp'], harm.df['D2'], label='D2')
	# plt.plot(harm.df['timestamp'], harm.df['D1'], label='D1')
	# plt.plot(harm.df['timestamp'], harm.df['D0'], label='D0')  # D0 is the last array in the tuple.
	plt.xlabel('Time (ns)')
	plt.ylabel('Logic Level')
	plt.legend(loc="upper right")
	
	plt.show()
	
def stop_record_data():
	''' -- Stop recording oscilloscope data '''
	# Остановка осциллографа
	harm.status["stop"] = ps.ps5000aStop(harm.chandle)
	assert_pico_ok(harm.status["stop"])
	
	# Закрытие и отключение осциллографа
	harm.status["close"]=ps.ps5000aCloseUnit(harm.chandle)
	assert_pico_ok(harm.status["close"])
	print("Data recording stopped")

# ---------- Serial ----------
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

		self.df = pd.DataFrame()
		self.data = dict()

		self.rotatingTime = 0
		self.SERVO_MB_ADDRESS = 16

		# ---------- Picoscope 5442D ----------
		# global sampleRates, timeBase, interval, channels, intervals, resolution
		self.resolutions = ["14", "15", "16"]
		self.resolution = 14
		self.ranges = ["10 mV", "20 mV", "50 mV", "100 mV", "200 mV", "500 mV", "1 V", "2 V", "5 V", "10 V", "20 V"]  #, "50 V"] 50V не работает
		self.channels = [0, 0, 0, 0]
		self.intervals_14bit_15bit = {"104": 15, "200": 27, "504": 65, "1000": 127, "2000": 252}
		self.intervals_16bit = {"112": 10, "208": 16, "512": 35, "1008": 66, "2000": 128}
		self.sampleRates_14bit_15bit = ["9.62 МС/c", "5 МС/c", "1.98 МС/c", "1 МС/c", "500 кС/c"]
		self.sampleRates_16bit = ["8.93 МС/c", "4.81 МС/c", "1.95 МС/c", "992 кС/c", "500 кС/c"]

		# ---------- Motor variables ----------
		self.motorSpeed = 120 # rpm
		self.motorAcc = 20
		self.motorDec = 20
		self.motorState = 0
		self.motorTurns = 10

		# Создание объектов chandle, status
		self.chandle = ctypes.c_int16()
		self.status = {}

		for port in comPorts:
			self.ui.cbox_SerialPort.addItem(port)
		
		#self.ui.cbox_SerialPort.currentIndexChanged.connect(portChanged)
		self.ui.btn_ContRotation.clicked.connect(rotate)
		self.ui.btn_StartRotation.clicked.connect(start)
		self.ui.btn_StopRotation.clicked.connect(stop)
		
		self.ui.btn_StartRecord.clicked.connect(start_record_data)
		self.ui.btn_StopRecord.clicked.connect(stop_record_data)

		self.ui.btn_Connect.clicked.connect(init_motor)
				
		# Init Pico parameters
		self.ui.Resolution.addItems(self.resolutions)
		self.ui.Channel1Range.addItems(self.ranges)
		self.ui.Channel1Range.setCurrentText('200 mV')
		self.ui.Channel1Range.addItems(self.ranges)
		self.ui.Channel2Range.addItems(self.ranges)
		self.ui.Channel3Range.addItems(self.ranges)
		self.ui.Channel3Range.setCurrentText('1 V')
		self.ui.Channel4Range.addItems(self.ranges)
		# self.ui.Interval.addItems(self.intervals_14bit_15bit)
		self.ui.SampleRate.setText(self.sampleRates_14bit_15bit[0])
		
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
	resolutionUpdate()

	harm.show()
	
	sys.exit(app.exec_())