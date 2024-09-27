from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
from PyQt5.QtCore import Qt, QAbstractTableModel
from PyQt5.QtGui import QIcon
from PyQt5.uic import loadUi
import sys, time, datetime, os
import pandas as pd
import numpy as np

import threading

# модуль расчёта интегральных характеристик
import calc

# Подключение необходимых модулей для вращения мотора
import serial
import serial.tools.list_ports
import minimalmodbus

# Модули для осциллографа
import ctypes
from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc, splitMSODataFast

class PandasTableModel(QAbstractTableModel):
    '''- Наследование от абстрактного представления модели таблицы результатов -'''
    def __init__(self, data, hheaders, vheaders):
        super().__init__()
        self.data = data
        self.hheaders = hheaders
        self.vheaders = vheaders

    def rowCount(self, parent=None):
        return len(self.data)

    def columnCount(self, parent=None):
        return len(self.data.columns)

    def data(self, index, role=Qt.DisplayRole):
        '''Представление данных в таблице'''
        if role == Qt.DisplayRole:
            value = self.data.iloc[index.row(), index.column()]
            if pd.isnull(value):
                return '-'
            if isinstance(value, float):
                return f'{value:.3g}'
            return f'{value}'
        return None            

    def headerData(self, section, orientation, role):
        '''Представление заголовков в таблице'''
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.hheaders[section]

            if orientation == Qt.Vertical:
                return self.vheaders[section]

class MainUI( QMainWindow):
    '''--- Основной класс приложения ---'''
    def __init__(self):
        '''--- Инициализация класса, переменных и элементов управления GUI ---'''
        super(MainUI, self).__init__()
        loadUi("harm_ui_v4.ui", self)
        self.setWindowIcon(QIcon("logo.png"))

        # Массив данных
        self.data = dict()
        self.df_result = 0

        '''- переменные для Picoscope 5442D -'''
        self.resolutions = ["14", "15", "16"] # битность
        self.resolution = 14
        self.ranges = ["10 mV", "20 mV", "50 mV", "100 mV", "200 mV", "500 mV", "1 V", "2 V", "5 V", "10 V", "20 V"]  # порог чувствительности , "50 V"] 50V не работает
        self.channels = [0, 0, 0, 0, 0]
        # Интервалы сэмплирования
        self.intervals_14bit_15bit = {"104": 15, "200": 27, "504": 65, "1000": 127, "2000": 252}
        self.intervals_16bit = {"112": 10, "208": 16, "512": 35, "1008": 66, "2000": 128}
        # Скорости сэмплирования
        self.sampleRates_14bit_15bit = ["9.62 МС/c", "5 МС/c", "1.98 МС/c", "1 МС/c", "500 кС/c"]
        self.sampleRates_16bit = ["8.93 МС/c", "4.81 МС/c", "1.95 МС/c", "992 кС/c", "500 кС/c"]

        '''- переменные для мотора -'''
        self.rotatingTime = 0
        # Modbus-адрес драйвера по умолчанию - 16
        self.SERVO_MB_ADDRESS = 16
        # self.motorSpeed = 120     # rpm не влияет
        # self.motorAcc = 1000      # ms  не влияет
        # self.motorDec = 1000      # ms  не влияет
        # self.motorState = 0       #     не влияет
        # self.motorTurns = 10      #     не влияет

        # Создание объектов chandle, status
        self.chandle = ctypes.c_int16()
        self.status = {}
        self.servo = 0
        
        # ---------- Serial ports ----------
        portList = serial.tools.list_ports.comports(include_links=False)
        comPorts = []
        for item in portList:
            comPorts.append(item.device)
        message = "Доступные COM-порты: " + str(comPorts)
        print(message)
        self.statusbar.showMessage(message)

        for port in comPorts:
            self.cBox_SerialPort_1.addItem(port)

        # Кнопка Продолжить окна Инициализации
        self.pBtn_Contunue.clicked.connect(self.init_continue)

        # Кнопка инициализация шагового мотора
        self.pBtn_Connect_1.clicked.connect(self.init_motor)
        # self.pBtn_Connect_2.clicked.connect(self.init_motor)

        # Кнопки управления мотором
        self.pBtn_Rotation.clicked.connect(self.rotate_motor_continious)
        self.pBtn_Stop.clicked.connect(self.stop_rotation)

        # Инициализация параметров осциллографа Pico
        self.cBox_Resolution.addItems(self.resolutions)
        self.cBox_Ch1Range.addItems(self.ranges)
        self.cBox_Ch1Range.setCurrentText('10 V')
        self.cBox_Ch2Range.addItems(self.ranges)
        self.cBox_Ch3Range.addItems(self.ranges)
        self.cBox_Ch3Range.setCurrentText('5 V')
        self.cBox_Ch4Range.addItems(self.ranges)
        self.lbl_SampleRate.setText(self.sampleRates_14bit_15bit[0])

        # DEPRECATED Расчёт времени вращения мотора
        # self.lEd_Speed.editingFinished.connect(calcTime)
        # self.lEd_Turns.editingFinished.connect(calcTime)

        # Расчёт значений осциллографа Picoscope
        self.cBox_Resolution.currentIndexChanged.connect(self.updateInterval)
        self.cBox_Interval.currentIndexChanged.connect(self.calcTimeBase)

        # Проверка битности при включении каналов
        self.chkBox_Ch1Enable.stateChanged.connect(self.resolutionUpdate)
        self.chkBox_Ch2Enable.stateChanged.connect(self.resolutionUpdate)
        self.chkBox_Ch3Enable.stateChanged.connect(self.resolutionUpdate)
        self.chkBox_Ch4Enable.stateChanged.connect(self.resolutionUpdate)
        
        # Порог отсечки logiclevel для цифровых каналов
        logiclevel = 1.5
        self.lEd_ChDigRange.setText(str(logiclevel))
        self.hSld_ChDigRange.setValue(int(logiclevel*10))
        self.lEd_ChDigRange.editingFinished.connect(self.chDigRange_validate)
        self.hSld_ChDigRange.valueChanged.connect(lambda: self.lEd_ChDigRange.setText(str(self.hSld_ChDigRange.value()/10)))

        # Запуск измерений кнопками "Старт измерений"
        # self.pBtn_Start_1.clicked.connect(self.operate1)
        self.pBtn_Start_1.clicked.connect(self.operating_mode1)
        # self.pBtn_Start_2.clicked.connect(self.operate2)
        self.pBtn_Start_2.clicked.connect(self.operating_mode2)
        # self.pBtn_Start_3.clicked.connect(self.operate3_start)
        self.pBtn_Start_3.clicked.connect(self.operating_mode3_start)
        self.pBtn_Next_3.clicked.connect(self.operating_mode3_cont)
        self.pBtn_Finish_3.clicked.connect(self.operating_mode3_fin)
        # self.pBtn_Start_4.clicked.connect(self.operate4)
        self.pBtn_Start_4.clicked.connect(self.operating_mode4)

        self.pBtn_Save2File_1.setEnabled(False)
        self.pBtn_Save2File_2.setEnabled(False)
        self.pBtn_Save2File_3.setEnabled(False)
        self.pBtn_Save2File_4.setEnabled(False)
        self.pBtn_Next_3.setEnabled(False)
        self.pBtn_Finish_3.setEnabled(False)

        self.pBtn_Save2File_1.clicked.connect(self.operating_mode1_savedata)
        self.pBtn_Save2File_2.clicked.connect(self.operating_mode2_savedata)
        self.pBtn_Save2File_3.clicked.connect(self.operating_mode3_savedata)
        self.pBtn_Save2File_4.clicked.connect(self.operating_mode4_savedata)
        
        # Инициализация начальных значений осциллографа Picoscope
        self.resolutionUpdate()
        self.updateInterval()
        self.calcTimeBase()

        '''- Параметры вкладки инициализация -'''
        self.dateEdit.setDate(datetime.datetime.now())
        self.dateEdit.setCalendarPopup(True)

        magnetTypes = ['Квадруполь-32', 'Секступоль', 'Октуполь']
        self.cBox_MagnetType.addItems(magnetTypes)

        operatingModes = ['1. Измерения при фиксированном поле', '2. Оценка временной стабильности', '3. Измерения при изменении тока в обмотках', '4. Остаточные гармоники']
        self.cBox_OperatingModes.addItems(operatingModes)

    '''--- Кнопки управления и проверок ---'''

    def init_continue(self) -> None:
        '''- Действия при нажатии кнопки "Продолжить" -'''
        if self.check_init():
            self.select_tab()
        else:
            message = "Заполните поля инициализации и выберите режим"
            print(message)
            self.statusbar.showMessage(message)

    def check_init(self) -> bool:
        '''- Проверка заполнения полей инициализации -'''
        return True   #TODO Заглушка, убрать
        if self.lEd_Name.text() and self.lEd_MagnetSerial.text() and self.cBox_MagnetType.currentText() and self.cBox_OperatingModes.currentText():
            return True
        else:
            return False

    def select_tab(self) -> None:
        ''' Выбор вкладки рабочего режима съёмки ''' 
        match self.cBox_OperatingModes.currentIndex():
            case 0:
                # self.tab_mode_1.setDisabled(False)
                self.tabWidget.setTabEnabled(1, True)
                self.tabWidget.setTabEnabled(2, False)
                self.tabWidget.setTabEnabled(3, False)
                self.tabWidget.setTabEnabled(4, False)
                self.tabWidget.setCurrentIndex(1)
            case 1:
                self.tabWidget.setTabEnabled(1, False)
                self.tabWidget.setTabEnabled(2, True)
                self.tabWidget.setTabEnabled(3, False)
                self.tabWidget.setTabEnabled(4, False)
                self.tabWidget.setCurrentIndex(2)
            case 2:
                self.tabWidget.setTabEnabled(1, False)
                self.tabWidget.setTabEnabled(2, False)
                self.tabWidget.setTabEnabled(3, True)
                self.tabWidget.setTabEnabled(4, False)
                self.tabWidget.setCurrentIndex(3)
            case 3:
                self.tabWidget.setTabEnabled(1, False)
                self.tabWidget.setTabEnabled(2, False)
                self.tabWidget.setTabEnabled(3, False)
                self.tabWidget.setTabEnabled(4, True)
                self.tabWidget.setCurrentIndex(4)

    def chDigRange_validate(self):
        '''- Валидация значения поля отсечки цифровых каналов -'''
        s = self.lEd_ChDigRange.text()
        s = s.replace(',', '.') if ',' in s else s
        try:
            range = float(s)
        except ValueError:
            range = 0.0
        if range < 0:
            range = 0.0
        elif range > 5.0:
            range = 5.0
        self.lEd_ChDigRange.setText(str(range))
        self.hSld_ChDigRange.setValue(int(range*10))

    '''--- Управление мотором ---'''

    def init_motor(self) -> None:
        ''' -- Инициализация привода катушек --'''
        self.pBtn_Contunue.setDisabled(False) #TODO после отладки удалить
        try:
            self.servo = minimalmodbus.Instrument(self.cBox_SerialPort_1.currentText(), self.SERVO_MB_ADDRESS)
            # Настройка порта: скорость - 9600 бод/с, четность - нет, кол-во стоп-бит - 2.
            self.servo.serial.baudrate = 9600
            self.servo.serial.parity = serial.PARITY_NONE
            self.servo.serial.stopbits = 2
            # Команда включения серво; 0x0405 - адрес параметра; 0x83 - значение параметра
            self.servo.write_register(0x0405, 0x83, functioncode=6)
            self.lbl_ServoStatus_2.setText("Подключен")
            message = "Привод подключен"
            print(message)
            self.statusbar.showMessage(message)
            self.pBtn_Rotation.setDisabled(False)
            self.pBtn_Stop.setDisabled(False)
            self.pBtn_Contunue.setDisabled(False)
        except (serial.serialutil.SerialException, minimalmodbus.NoResponseError):
            self.lbl_ServoStatus_2.setText("Не подключен")
            message = "Привод не виден"
            print(message)
            self.statusbar.showMessage(message)

    def rotate_motor_continious(self) -> None:
        ''' -- Постоянное вращение катушек --'''
        message = "Старт вращения"
        print(message)
        self.statusbar.showMessage(message)
        try:
            self.motorSpeed = int(self.lEd_Speed.text())
            self.motorAcc = int(self.lEd_Acceleration.text())
            self.motorDec = int(self.lEd_Deceleration.text())
            self.motorTurns = int(self.lEd_Turns.text())
            # Формирование массива параметров для команды:
            # 0x0002 - режим управления скоростью, записывается по адресу 0x6200
            # 0x0000 - верхние два байта кол-ва оборотов (=0 для режима управления скоростью), записывается по адресу 0x6201
            # 0x0000 - нижние два байта кол-ва оборотов  (=0 для режима управления скоростью), записывается по адресу 0x6202
            # 0x03E8 - значение скорости вращения (1000 об/мин), записывается по адресу 0x6203
            # 0x0064 - значение времени ускорения (100 мс), записывается по адресу 0x6204
            # 0x0064 - значение времени торможения (100 мс), записывается по адресу 0x6205
            # 0x0000 - задержка перед началом движения (0 мс), записывается по адресу 0x6206
            # 0x0010 - значение триггера для начала движения, записывается по адресу 0x6207
            data = [0x0002, 0x0000, 0x0000, self.motorSpeed, self.motorAcc, self.motorDec, 0x0000, 0x0010]
            self.servo.write_registers(0x6200, data)
            message = "вращение..."
            print(message)
            self.statusbar.showMessage(message)
        except (NameError, AttributeError):
            message = "Привод не виден"
            print(message)
            self.statusbar.showMessage(message)

    def rotate_motor_absolute(self) -> None:
        ''' -- Вращение катушек на заданное число оборотов с заданной абсолютной позиции --'''
        message = "Старт вращения"
        print(message)
        self.statusbar.showMessage(message)
        try:
            # Формирование массива параметров для команды:
            # 0x0001 - Motion Mode, Absolute position mode, по адресу 0x6200
            # 0x0001 - Hexadecimal data of position=100000 pulse. All positions in PR mode are in units of 10000P/r, верхние два байта кол-ва оборотов (=0 для режима управления скоростью), записывается по адресу 0x6201
            # 0x86A0 - 00 01 86 A0 represents 10 turns of motor rotation - нижние два байта кол-ва оборотов  (=0 для режима управления скоростью), записывается по адресу 0x6202
            # 0x01F4 - Hexadecimal data of Speed=500r/min, записывается по адресу 0x6203
            # 0x0064 - значение времени ускорения (100 мс), записывается по адресу 0x6204
            # 0x0064 - значение времени торможения (100 мс), записывается по адресу 0x6205
            # 0x0000 - задержка перед началом движения (0 мс), записывается по адресу 0x6206
            # 0x0010 - значение триггера для начала движения, записывается по адресу 0x6207
            data = [0x0001, 0x0001, 0x86A0, 0x01F4, 0x0064, 0x0064, 0x0000, 0x0010]
            self.servo.write_registers(0x6200, data)
            message = "вращение 10 оборотов"
            print(message)
            self.statusbar.showMessage(message)
        except (NameError, AttributeError):
            message = "Привод не виден"
            print(message)
            self.statusbar.showMessage(message)

    def rotate_motor_relative(self) -> None:
        ''' -- Вращение катушек на заданное число оборотов с относительной позиции --'''
        message = "Старт вращения"
        print(message)
        self.statusbar.showMessage(message)
        try:
            # Формирование массива параметров для команды:
            # 0x0041 - Motion Mode, Relative position mode, по адресу 0x6200
            # 0x0000 - Hexadecimal data of position=10000 pulse. All positions in PR mode are in units of 10000P/r, верхние два байта кол-ва оборотов (=0 для режима управления скоростью), записывается по адресу 0x6201
            # 0x2710 - 00 01 86 A0 represents 10 turns of motor rotation - нижние два байта кол-ва оборотов  (=0 для режима управления скоростью), записывается по адресу 0x6202
            # 0x0258 - Hexadecimal data of Speed=600rpm, записывается по адресу 0x6203
            # 0x0032 - значение времени ускорения (50ms/1000rpm), записывается по адресу 0x6204
            # 0x0032 - значение времени торможения (50ms/1000rpm), записывается по адресу 0x6205
            # 0x0000 - задержка перед началом движения (0 мс), записывается по адресу 0x6206
            # 0x0010 - значение триггера для начала движения, записывается по адресу 0x6207
            data = [0x0001, 0x0001, 0x86A0, 0x01F4, 0x0064, 0x0064, 0x0000, 0x0010]
            self.servo.write_registers(0x6200, data)
            message = "вращение 10 оборотов"
            print(message)
            self.statusbar.showMessage(message)
        except (NameError, AttributeError):
            message = "Привод не виден"
            print(message)
            self.statusbar.showMessage(message)

    def stop_rotation(self) -> None:
        ''' -- Стоп вращения катушки --'''
        try:
            self.servo.write_register(0x6002, 0x40, functioncode=6)
            message = "Стоп вращения"
            print(message)
            self.statusbar.showMessage(message)
        except (NameError, AttributeError):
            message = "Привод не виден"
            print(message)
            self.statusbar.showMessage(message)

    '''--- Управление АЦП ---'''

    def open_scope_unit(self) -> None:
        '''- Захват управления блоком АЦП -'''
        match self.resolution:
            case 14:	resolution_code = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_14BIT"]
            case 15:	resolution_code = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_15BIT"]
            case 16:	resolution_code = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_16BIT"]
            
        # Получение статуса и chandle для дальнейшего использования
        self.status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(self.chandle), None, resolution_code)
        try:
            assert_pico_ok(self.status["openunit"])
        except: # PicoNotOkError:
            powerStatus = self.status["openunit"]
            if powerStatus == 286:
                self.status["changePowerSource"] = ps.ps5000aChangePowerSource(self.chandle, powerStatus)
            elif powerStatus == 282:
                self.status["changePowerSource"] = ps.ps5000aChangePowerSource(self.chandle, powerStatus)
            else:
                message = "Ошибка: смените питание"
                print(message) 
                self.statusbar.showMessage(message)
                raise assert_pico_ok(self.status["changePowerSource"])
    
    def stop_recording(self) -> None:
        ''' -- Остановка и отключение АЦП -- '''
        # Остановка осциллографа
        self.status["stop"] = ps.ps5000aStop(self.chandle)
        assert_pico_ok(self.status["stop"])
        
        # Закрытие и отключение осциллографа
        self.status["close"]=ps.ps5000aCloseUnit(self.chandle)
        assert_pico_ok(self.status["close"])
        # message = "Запись данных завершена."
        # print(message)
        # self.statusbar.showMessage(message)

    def resolutionUpdate(self) -> None:
        '''-- Выбор битности разрешения в зависимости от количества используемых каналов --'''
        self.channels[0] = self.chkBox_Ch1Enable.checkState()
        self.channels[1] = self.chkBox_Ch2Enable.checkState()
        self.channels[2] = self.chkBox_Ch3Enable.checkState()
        self.channels[3] = self.chkBox_Ch4Enable.checkState()
        self.channels[4] = self.chkBox_ChDigEnable.checkState()
        match self.channels[:4].count(2):
            case 4 | 3:
                self.cBox_Resolution.clear()
                self.cBox_Resolution.addItems(['14'])
            case 2:
                self.cBox_Resolution.clear()
                self.cBox_Resolution.addItems(['14', '15'])
                self.cBox_Resolution.setCurrentText('15')
            case 1:
                self.cBox_Resolution.clear()
                self.cBox_Resolution.addItems(['14', '15', '16'])
                self.cBox_Resolution.setCurrentText('16')
            case 0:
                self.cBox_Resolution.clear()

    def updateInterval(self) -> None:
        '''-- Выбор интервала сэмплирования для выбранной битности --'''
        self.resolution = 0
        if self.cBox_Resolution.count() != 0:
            self.resolution = int(self.cBox_Resolution.currentText())
            if self.resolution in [14, 15]:
                self.cBox_Interval.clear()
                self.cBox_Interval.addItems(self.intervals_14bit_15bit)
                self.cBox_Interval.setCurrentText('1000')
            elif self.resolution == 16:
                self.cBox_Interval.clear()
                self.cBox_Interval.addItems(self.intervals_16bit)
                self.cBox_Interval.setCurrentText('1008')
            self.interval = self.cBox_Interval.currentText()

    def calcTimeBase(self) -> None:
        '''-- Расчёт скорости сэмплирования (сэмплов/сек) --'''
        if self.resolution in [14, 15]:
            self.lbl_SampleRate.setText(self.sampleRates_14bit_15bit[self.cBox_Interval.currentIndex()])
        elif self.resolution == 16:
            self.lbl_SampleRate.setText(self.sampleRates_16bit[self.cBox_Interval.currentIndex()])
        self.interval = self.cBox_Interval.currentText()

    def channel_range(self, channel_checked) -> int:
        '''- Пределы измерения аналоговых каналов -'''
        match channel_checked.currentText():
            case "10 mV": 	return ps.PS5000A_RANGE["PS5000A_10MV"]
            case "20 mV": 	return ps.PS5000A_RANGE["PS5000A_20MV"]
            case "50 mV": 	return ps.PS5000A_RANGE["PS5000A_50MV"]
            case "100 mV": 	return ps.PS5000A_RANGE["PS5000A_100MV"]
            case "200 mV": 	return ps.PS5000A_RANGE["PS5000A_200MV"]
            case "500 mV": 	return ps.PS5000A_RANGE["PS5000A_500MV"]
            case "1 V": 	return ps.PS5000A_RANGE["PS5000A_1V"]
            case "2 V": 	return ps.PS5000A_RANGE["PS5000A_2V"]
            case "5 V": 	return ps.PS5000A_RANGE["PS5000A_5V"]
            case "10 V": 	return ps.PS5000A_RANGE["PS5000A_10V"]
            case "20 V": 	return ps.PS5000A_RANGE["PS5000A_20V"]
            case "50 V": 	return ps.PS5000A_RANGE["PS5000A_50V"]

    def setup_analogue_channels(self) -> None:
        ''' -- Настройка аналоговых каналов --'''
        self.chRange = {}
        coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]

        # Настройка канала A
        # handle = self.chandle
        channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
        enabled = 1 if self.chkBox_Ch1Enable.isChecked() else 0 # enabled == 1, disabled == 0
        # coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]
        self.chRange["A"] = self.channel_range(self.cBox_Ch1Range)
        # analogue offset = 0 V
        self.status["setChA"] = ps.ps5000aSetChannel(self.chandle, channel, enabled, coupling_type, self.chRange["A"], 0)
        assert_pico_ok(self.status["setChA"])
        
        # Настройка канала B
        # handle = self.chandle
        channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"]
        enabled = 1 if self.chkBox_Ch2Enable.isChecked() else 0 # enabled == 1, disabled == 0
        # coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]
        self.chRange["B"] = self.channel_range(self.cBox_Ch2Range)
        # analogue offset = 0 V
        self.status["setChB"] = ps.ps5000aSetChannel(self.chandle, channel, enabled, coupling_type, self.chRange["B"], 0)
        assert_pico_ok(self.status["setChB"])
        
        # Настройка канала C
        # handle = self.chandle
        channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_C"]
        enabled = 1 if self.chkBox_Ch3Enable.isChecked() else 0 # enabled == 1, disabled == 0
        # coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]
        self.chRange["C"] = self.channel_range(self.cBox_Ch3Range)
        # analogue offset = 0 V
        self.status["setChC"] = ps.ps5000aSetChannel(self.chandle, channel, enabled, coupling_type, self.chRange["C"], 0)
        assert_pico_ok(self.status["setChC"])

        # Настройка канала D
        # handle = self.chandle
        channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_D"]
        enabled = 1 if self.chkBox_Ch4Enable.isChecked() else 0 # enabled == 1, disabled == 0
        # coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]
        self.chRange["D"] = self.channel_range(self.cBox_Ch4Range)
        # analogue offset = 0 V
        self.status["setChD"] = ps.ps5000aSetChannel(self.chandle, channel, enabled, coupling_type, self.chRange["D"], 0)
        assert_pico_ok(self.status["setChD"])

    def setup_digital_channels(self) -> None:
        ''' -- Настройка цифровых каналов --'''
        # Set up digital port
        # handle = self.chandle
        # channel = ps5000a_DIGITAL_PORT0 = 0x80
        digital_port0 = ps.PS5000A_CHANNEL["PS5000A_DIGITAL_PORT0"]
        enabled = 1 if self.chkBox_ChDigEnable.isChecked() else 0
        logicLevel = int(float(self.lEd_ChDigRange.text())*32767/5) #Отсечка цифрового канала
        # logicLevel = 9830 #Отсечка цифрового канала на 1,5V
        harm.status["SetDigitalPort"] = ps.ps5000aSetDigitalPort(self.chandle, digital_port0, enabled, logicLevel)
        assert_pico_ok(self.status["SetDigitalPort"])

    def get_max_ADC_samples(self) -> None:
        ''' Получение максимального количества сэмплов АЦП '''
        self.maxADC = ctypes.c_int16()
        self.status["maximumValue"] = ps.ps5000aMaximumValue(self.chandle, ctypes.byref(self.maxADC))
        assert_pico_ok(self.status["maximumValue"])

    def set_max_samples(self) -> None:
        ''' Установка количества сэмплов до и после срабатывания триггера '''
        self.preTriggerSamples = 0
        self.postTriggerSamples = 10000000
        self.maxSamples = self.preTriggerSamples + self.postTriggerSamples

    def set_timebase(self) -> None:
        # Установка частоты сэмплирования
        if self.resolution in [14, 15]:
            self.timebase = self.intervals_14bit_15bit[self.interval] # 65-504нс, 127-1000 нс
        elif self.resolution == 16:
            self.timebase = self.intervals_16bit[self.interval] # 25 == 512 нс
        self.timeIntervalns = ctypes.c_float()
        self.returnedMaxSamples = ctypes.c_int32()
        self.status["getTimebase2"] = ps.ps5000aGetTimebase2(self.chandle, self.timebase, self.maxSamples, ctypes.byref(self.timeIntervalns), ctypes.byref(self.returnedMaxSamples), 0)
        assert_pico_ok(self.status["getTimebase2"])

    def channel_maxrange(self, channel_checked) -> float:
        ''' -- возвращает заданное максимальное значение диапазона канала --'''
        match channel_checked.currentText():
            case "10 mV": 	return 10
            case "20 mV": 	return 20
            case "50 mV": 	return 50
            case "100 mV": 	return 100
            case "200 mV": 	return 200
            case "500 mV": 	return 500
            case "1 V": 	return 1000
            case "2 V": 	return 2000
            case "5 V": 	return 5000
            case "10 V": 	return 10000
            case "20 V": 	return 20000
            case "50 V": 	return 50000

    '''--- Методы запуска мотора, получения и обработки данных ---'''

    def start_record_data(self) -> pd.DataFrame:
        ''' -- Запись данных с осциллографа --'''
        self.data = dict()
        # Подключение к осциллографу
        self.open_scope_unit()
        # Подключение каналов
        self.setup_analogue_channels()
        self.setup_digital_channels()

        # Установка разрешения
        self.get_max_ADC_samples()
        self.set_max_samples()
        self.set_timebase()
        
        message = "Начат сбор данных..."
        print(message)
        self.statusbar.showMessage(message)

        # Запуск сбора данных
        self.status["runBlock"] = ps.ps5000aRunBlock(self.chandle, self.preTriggerSamples, self.postTriggerSamples, self.timebase, None, 0, None, None)
        assert_pico_ok(self.status["runBlock"])
        
        # Ожидание готовности данных
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            self.status["isReady"] = ps.ps5000aIsReady(self.chandle, ctypes.byref(ready))
        
        # Создание буферов данных аналоговых каналов
        bufferAMax = (ctypes.c_int16 * self.maxSamples)()
        bufferAMin = (ctypes.c_int16 * self.maxSamples)()
        bufferBMax = (ctypes.c_int16 * self.maxSamples)()
        bufferBMin = (ctypes.c_int16 * self.maxSamples)()
        bufferCMax = (ctypes.c_int16 * self.maxSamples)()
        bufferCMin = (ctypes.c_int16 * self.maxSamples)()
        bufferDMax = (ctypes.c_int16 * self.maxSamples)()
        bufferDMin = (ctypes.c_int16 * self.maxSamples)()

        # Создание буферов данных цифровых каналов
        bufferDPort0Max = (ctypes.c_int16 * self.maxSamples)()
        bufferDPort0Min = (ctypes.c_int16 * self.maxSamples)()
        
        if self.chkBox_Ch1Enable.isChecked(): # Указание буфера для сбора данных канала А
            source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
            self.status["setDataBuffersA"] = ps.ps5000aSetDataBuffers(self.chandle, source, ctypes.byref(bufferAMax), ctypes.byref(bufferAMin), self.maxSamples, 0, 0)
            assert_pico_ok(self.status["setDataBuffersA"])
        
        if self.chkBox_Ch2Enable.isChecked():
            # Указание буфера для сбора данных канала B
            source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"]
            self.status["setDataBuffersB"] = ps.ps5000aSetDataBuffers(self.chandle, source, ctypes.byref(bufferBMax), ctypes.byref(bufferBMin), self.maxSamples, 0, 0)
            assert_pico_ok(self.status["setDataBuffersB"])

        if self.chkBox_Ch3Enable.isChecked():
            # Указание буфера для сбора данных канала C
            source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_C"]
            self.status["setDataBuffersC"] = ps.ps5000aSetDataBuffers(self.chandle, source, ctypes.byref(bufferCMax), ctypes.byref(bufferCMin), self.maxSamples, 0, 0)
            assert_pico_ok(self.status["setDataBuffersC"])

        if self.chkBox_Ch4Enable.isChecked():
            # Указание буфера для сбора данных канала D
            source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_D"]
            self.status["setDataBuffersD"] = ps.ps5000aSetDataBuffers(self.chandle, source, ctypes.byref(bufferDMax), ctypes.byref(bufferDMin), self.maxSamples, 0, 0)
            assert_pico_ok(self.status["setDataBuffersD"])

        if self.chkBox_ChDigEnable.isChecked(): # Указание буфера для сбора данных цифрового канала ps5000a_DIGITAL_PORT0
            # handle = self.chandle
            # source = ps.ps5000a_DIGITAL_PORT0 == 0x80
            digital_port0 = ps.PS5000A_CHANNEL["PS5000A_DIGITAL_PORT0"]
            # Buffer max = ctypes.byref(bufferDPort0Max)
            # Buffer min = ctypes.byref(bufferDPort0Min)
            # Buffer length = maxSamples
            # Segment index = 0
            # Ratio mode = ps5000a_RATIO_MODE_NONE = 0
            self.status["SetDataBuffersDigital"] = ps.ps5000aSetDataBuffers(self.chandle, digital_port0, ctypes.byref(bufferDPort0Max), ctypes.byref(bufferDPort0Min), self.maxSamples, 0, 0)
            assert_pico_ok(self.status["SetDataBuffersDigital"])

        # Выделение памяти для переполнения
        overflow = ctypes.c_int16()
        
        # Приведение типов
        cmaxSamples = ctypes.c_int32(self.maxSamples)
        
        # Получение данных из осциллографа в созданные буферы
        self.status["getValues"] = ps.ps5000aGetValues(self.chandle, 0, ctypes.byref(cmaxSamples), 0, 0, 0, ctypes.byref(overflow))
        assert_pico_ok(self.status["getValues"])

        message = "Сбор данных завершён."
        print(message)
        self.statusbar.showMessage(message)

        self.stop_recording()

        # Задаём шкалу времени
        time_axis = np.linspace(0, (cmaxSamples.value - 1) * self.timeIntervalns.value, cmaxSamples.value)
        self.data['timestamp'] = time_axis

        # Преобразование отсчетов АЦП в мВ
        if self.chkBox_Ch1Enable.isChecked():
            adc2mVChAMax = adc2mV(bufferAMax, self.chRange["A"], self.maxADC)
            self.data['ch_a'] = adc2mVChAMax
        if self.chkBox_Ch2Enable.isChecked():
            adc2mVChBMax = adc2mV(bufferBMax, self.chRange["B"], self.maxADC)
            self.data['ch_b'] = adc2mVChBMax
        if self.chkBox_Ch3Enable.isChecked():
            adc2mVChCMax = adc2mV(bufferCMax, self.chRange["C"], self.maxADC)
            self.data['ch_c'] = adc2mVChCMax
        if self.chkBox_Ch4Enable.isChecked():
            adc2mVChDMax = adc2mV(bufferDMax, self.chRange["D"], self.maxADC)
            self.data['ch_d'] = adc2mVChDMax

        # TODO: Уточнить проверку на выход за пределы измерений
        message = f'Валидация - {self.validate_data_range()}'
        print(message)
        self.statusbar.showMessage(message)

        # Получение бинарных данных для Digital Port 0
        # Возвращаемый кортеж содержит каналы в следующем порядке - (7-D0, 6-D1, 5, 4, 3, 2, 1, 0-D7).
        bufferDPort0 = splitMSODataFast(cmaxSamples, bufferDPort0Max)
        self.data['D0'] = bufferDPort0[5] # Z-канал энкодера - нуль оборота
        self.data['D1'] = bufferDPort0[6] # Угловой импульс

        df = pd.DataFrame(self.data)
        df['D0'] = df['D0'].apply(int)
        df['D1'] = df['D1'].apply(int)

        #self.save_data2file(df)
        return df

    def save_data2file(self, df: pd.DataFrame, i: int = '') -> None:
        ''' -- Сохранение полученных сырых данных на диск -- '''

        message = "Запись данных в файл..."
        print(message)
        self.statusbar.showMessage(message)
        
        filename = time.strftime("%Y-%m-%d_%H-%M")
        df.to_csv(f"rawdata_{i}_{filename}.csv")
        
        message = "Сохранение данных закончено"
        print(message)
        self.statusbar.showMessage(message)
    
    def validate_data_range(self) -> dict:
        ''' TODO: -- Проверка выхода измерений за предел канала --'''
        df = pd.DataFrame(self.data)
        if self.chkBox_Ch1Enable.isChecked():
            if df['ch_a'].max() >= self.channel_maxrange(self.cBox_Ch1Range):
                return ('a', df['ch_a'].max())
        if self.chkBox_Ch2Enable.isChecked():
            if df['ch_b'].max() >= self.channel_maxrange(self.cBox_Ch2Range):
                return ('b', df['ch_b'].max())
        if self.chkBox_Ch3Enable.isChecked():
            if df['ch_c'].max() >= self.channel_maxrange(self.cBox_Ch3Range):
                return ('c', df['ch_c'].max())
        if self.chkBox_Ch4Enable.isChecked():
            if df['ch_d'].max() >= self.channel_maxrange(self.cBox_Ch4Range):
                return ('d', df['ch_d'].max())
        return('ok')

    def operating_mode1(self) -> None:
        '''-- Многопоточность для режима 1 --'''
        t1 = threading.Thread(target=self.operate1, args=(), daemon=True)
        t1.start()
        # t1.join()

    def operating_mode2(self) -> None:
        '''-- Многопоточность для режима 2 --'''
        t2 = threading.Thread(target=self.operate2, args=(), daemon=True)
        t2.start()
        # t2.join()

    def operating_mode3_start(self) -> None:
        '''-- Многопоточность для режима 3 --'''
        t3 = threading.Thread(target=self.operate3_start, args=(), daemon=True)
        t3.start()
        # t3.join()
    
    def operating_mode3_cont(self) -> None:
        '''-- Многопоточность для режима 3 --'''
        t3 = threading.Thread(target=self.operate3_next, args=(), daemon=True)
        t3.start()
        # t3.join()
    
    def operating_mode3_fin(self) -> None:
        '''-- Многопоточность для режима 3 --'''
        t3 = threading.Thread(target=self.operate3_fin, args=(), daemon=True)
        t3.start()
        # t3.join()

    def operating_mode4(self) -> None:
        '''-- Многопоточность для режима 4 --'''
        t4 = threading.Thread(target=self.operate4, args=(), daemon=True)
        t4.start()
        # t4.join()

    def operate1(self) -> None:
        '''-- Выполнение режима 1 --'''
        self.df_result = pd.DataFrame(index=['harm01', 'harm02', 'harm03', 'harm04', 'harm05', 'harm06', 'harm07', 'harm08', 'harm09', 'harm10',
                                 'harm11', 'harm12', 'harm13', 'harm14', 'harm15', 'harm16', 'deltaX', 'deltaY', 'alpha', 'H_avg'])

        try:
            MeasurementsNumber = int(self.lEd_MeasurementsNumber_1.text())
            TimeDelay = int(self.lEd_Pause_1.text())
        except ValueError:
            message = "Введите данные для измерений"
            print(message)
            self.statusbar.showMessage(message)
            return

        if MeasurementsNumber <= 0 or TimeDelay < 0:
            message = "Введите корректные данные для измерений"
            print(message)
            self.statusbar.showMessage(message)
            return

        self.pBtn_Start_1.setEnabled(False)

        for i in range(1,MeasurementsNumber+1):
            self.lbl_Current_Measure_Nmb_1.setText(str(i))
            df1 = self.start_record_data()

            # self.save_data2file(df, i) # Запись сырых данных на диск

            calculus_result = list(self.calculate_result(df1)) # Расчёт коэффициентов
            self.df_result[i] = calculus_result[0]+calculus_result[1:5]
            time.sleep(TimeDelay)
      
        self.pBtn_Start_1.setEnabled(True)

        self.df_result['mean'] = self.df_result.mean(axis=1)
        self.df_result['stdev'] = self.df_result.drop(['mean'], axis=1).std(axis=1)
        self.df_result["percent"] = (100*self.df_result["stdev"]/self.df_result["mean"].abs()).round(decimals=1)

        # print(self.df_result)
        # self.df_result.to_csv("result_1.csv")

        for i in range(1,MeasurementsNumber+1):
            self.df_result.drop(i, axis=1, inplace=True)

        df_header_v = self.df_result.index
        df_header_h = self.df_result.columns

        model = PandasTableModel(self.df_result, df_header_h, df_header_v)
        self.tblView_Result_1.setModel(model)
        self.pBtn_Save2File_1.setEnabled(True)
        self.lbl_Current_Measure_Nmb_1.setText('0')
        message = "Измерения завершены, можно записывать файл."
        print(message)
        self.statusbar.showMessage(message)

    def operate2(self) -> None:
        '''-- Выполнение режима 2 --'''
        self.df_result = pd.DataFrame(index=['harm01', 'harm02', 'harm03', 'harm04', 'harm05', 'harm06', 'harm07', 'harm08', 'harm09', 'harm10',
                                 'harm11', 'harm12', 'harm13', 'harm14', 'harm15', 'harm16', 'deltaX', 'deltaY', 'alpha', 'H_avg'])

        try:
            MeasurementsNumber = int(self.lEd_MeasurementsNumber_2.text())
            TimeDelay = int(self.lEd_Pause_2.text())
        except ValueError:
            message = "Введите данные для измерений"
            print(message)
            self.statusbar.showMessage(message)
            return

        if MeasurementsNumber <= 0 or TimeDelay < 0:
            message = "Введите корректные данные для измерений"
            print(message)
            self.statusbar.showMessage(message)
            return

        self.pBtn_Start_2.setEnabled(False)

        for i in range(1,MeasurementsNumber+1):
            self.lbl_Current_Measure_Nmb_2.setText(str(i))
            df2 = self.start_record_data()

            # self.save_data2file(df, i) # Запись сырых данных на диск

            calculus_result = list(self.calculate_result(df2)) # Расчёт коэффициентов
            self.df_result[i] = calculus_result[0]+calculus_result[1:5]
            time.sleep(TimeDelay)
      
        self.pBtn_Start_2.setEnabled(True)

        # self.df_result['mean'] = self.df_result.mean(axis=1)
        # self.df_result['stdev'] = self.df_result.drop(['mean'], axis=1).std(axis=1)
        # self.df_result["percent"] = (100*self.df_result["stdev"]/self.df_result["mean"].abs()).round(decimals=1)

        # print(self.df_result)
        # self.df_result.to_csv("result_2.csv")

        # for i in range(1,MeasurementsNumber+1):
        #     self.df_result.drop(i, axis=1, inplace=True)

        df_header_v = self.df_result.index
        df_header_h = self.df_result.columns

        model = PandasTableModel(self.df_result, df_header_h, df_header_v)
        self.tblView_Result_2.setModel(model)
        self.pBtn_Save2File_2.setEnabled(True)
        self.lbl_Current_Measure_Nmb_2.setText('0')
        message = "Измерения завершены, можно записывать файл."
        print(message)
        self.statusbar.showMessage(message)

    def operate3_start(self) -> None:
        '''-- Старт режима 3 --'''
        self.df_result = pd.DataFrame(index=['harm01', 'harm02', 'harm03', 'harm04', 'harm05', 'harm06', 'harm07', 'harm08', 'harm09', 'harm10',
                                 'harm11', 'harm12', 'harm13', 'harm14', 'harm15', 'harm16', 'deltaX', 'deltaY', 'alpha', 'H_avg'])

        try:
            self.MeasurementsNumber = int(self.lEd_MeasurementsNumber_3.text())
        except ValueError:
            message = "Введите данные для измерений"
            print(message)
            self.statusbar.showMessage(message)
            return
        
        if self.MeasurementsNumber <= 0:
            message = "Введите корректные данные для измерений"
            print(message)
            self.statusbar.showMessage(message)
            return
        
        self.pBtn_Start_3.setEnabled(False)

        self.lbl_Current_Measure_Nmb_3.setText('1')
        df3 = self.start_record_data()

        # self.save_data2file(df, i) # Запись сырых данных на диск

        calculus_result = list(self.calculate_result(df3)) # Расчёт коэффициентов
        self.df_result[0] = calculus_result[0]+calculus_result[1:5]
        self.MeasurementsNumber -= 1
        self.pBtn_Next_3.setEnabled(True)
        self.pBtn_Start_3.setEnabled(False)
        message = "Следующее измерение"
        print(message)
        self.statusbar.showMessage(message)

    def operate3_next(self) -> None:
        '''-- Продолжение режима 3 --'''
        if self.MeasurementsNumber == 0:
            self.pBtn_Next_3.setEnabled(False)
            self.pBtn_Finish_3.setEnabled(True)
            return

        self.pBtn_Next_3.setEnabled(False)

        self.lbl_Current_Measure_Nmb_3.setText(str(int(self.lEd_MeasurementsNumber_3.text()) - self.MeasurementsNumber + 1))
        df3 = self.start_record_data()
        # self.save_data2file(df, i) # Запись сырых данных на диск
        calculus_result = list(self.calculate_result(df3)) # Расчёт коэффициентов
        self.df_result[int(self.lEd_MeasurementsNumber_3.text()) - self.MeasurementsNumber] = calculus_result[0]+calculus_result[1:5]
        self.MeasurementsNumber -= 1

        self.pBtn_Next_3.setEnabled(True)

        if self.MeasurementsNumber > 0:
            message = "Измерение завершено, можно переходить к следующему."
            print(message)
            self.statusbar.showMessage(message)

        if self.MeasurementsNumber == 0:
            message = "Измерение завершено, можно выводить таблицу."
            print(message)
            self.statusbar.showMessage(message)
            self.pBtn_Next_3.setEnabled(False)
            self.pBtn_Finish_3.setEnabled(True)

    def operate3_fin(self) -> None:
        '''-- Завершение режима 3 --'''
        self.df_result['mean'] = self.df_result.mean(axis=1)
        self.df_result['stdev'] = self.df_result.drop(['mean'], axis=1).std(axis=1)
        self.df_result["percent"] = (100*self.df_result["stdev"]/self.df_result["mean"].abs()).round(decimals=1)

        # print(self.df_result)
        # self.df_result.to_csv("result_3.csv")

        # for i in range(1,MeasurementsNumber+1):
        #     self.df_result.drop(i, axis=1, inplace=True)

        df_header_v = self.df_result.index
        df_header_h = self.df_result.columns

        model = PandasTableModel(self.df_result, df_header_h, df_header_v)
        self.tblView_Result_3.setModel(model)

        self.pBtn_Finish_3.setEnabled(False)
        self.pBtn_Start_3.setEnabled(True)
        self.pBtn_Save2File_3.setEnabled(True)
        self.lbl_Current_Measure_Nmb_3.setText('0')

        message = "Измерения завершены, можно записывать файл."
        print(message)
        self.statusbar.showMessage(message)

    def operate4(self) -> None:
        '''-- Выполнение режима 4 --'''
        self.df_result = pd.DataFrame(index=['harm01', 'harm02', 'harm03', 'harm04', 'harm05', 'harm06', 'harm07', 'harm08', 'harm09', 'harm10',
                                 'harm11', 'harm12', 'harm13', 'harm14', 'harm15', 'harm16', 'deltaX', 'deltaY', 'alpha', 'H_avg'])

        try:
            MeasurementsNumber = int(self.lEd_MeasurementsNumber_4.text())
            TimeDelay = int(self.lEd_Pause_4.text())
        except ValueError:
            message = "Введите данные для измерений"
            print(message)
            self.statusbar.showMessage(message)
            return

        if MeasurementsNumber <= 0 or TimeDelay < 0:
            message = "Введите корректные данные для измерений"
            print(message)
            self.statusbar.showMessage(message)
            return

        self.pBtn_Start_4.setEnabled(False)

        for i in range(1,MeasurementsNumber+1):
            self.lbl_Current_Measure_Nmb_4.setText(str(i))
            df4 = self.start_record_data()

            # self.save_data2file(df, i) # Запись сырых данных на диск

            calculus_result = list(self.calculate_result(df4)) # Расчёт коэффициентов
            self.df_result[i] = calculus_result[0]+calculus_result[1:5]
            time.sleep(TimeDelay)
      
        self.pBtn_Start_4.setEnabled(True)

        self.df_result['mean'] = self.df_result.mean(axis=1)
        self.df_result['stdev'] = self.df_result.drop(['mean'], axis=1).std(axis=1)
        self.df_result["percent"] = (100*self.df_result["stdev"]/self.df_result["mean"].abs()).round(decimals=1)

        # print(self.df_result)
        # self.df_result.to_csv("result_4.csv")

        # for i in range(1,MeasurementsNumber+1):
        #     self.df_result.drop(i, axis=1, inplace=True)

        df_header_v = self.df_result.index
        df_header_h = self.df_result.columns

        model = PandasTableModel(self.df_result, df_header_h, df_header_v)
        self.tblView_Result_4.setModel(model)
        self.pBtn_Save2File_4.setEnabled(True)
        self.lbl_Current_Measure_Nmb_4.setText('0')
        message = "Измерения завершены, можно записывать файл."
        print(message)
        self.statusbar.showMessage(message)

    def savedata(self, mode: str) -> None:
        '''-- Запись полученных данных в файл --'''
        
        if isinstance(self.df_result, pd.DataFrame) and not self.df_result.empty:
            message = "Запись данных в файл..."
            print(message)
            self.statusbar.showMessage(message)
            
            # try:
            try:
                os.mkdir('data')
            except FileExistsError:
                pass
            try:
                os.mkdir(os.path.join('data', mode))
            except FileExistsError:
                pass

            name = '_'.join([self.dateEdit.text().replace('.','-'), self.lEd_MagnetSerial.text(), self.lEd_Suffix.text(),'.csv'])
            prefferedFilename = os.path.join('data', mode, name)
            try:
                filename, _ = QFileDialog.getSaveFileName(self, caption="Сохранить файл", directory=prefferedFilename, filter='CSV Files (*.csv);;All Files (*)')
                with open (filename, 'w') as f:
                    f.write(''.join(['Оператор - ', self.lEd_Name.text(),'\n']))
                    f.write(''.join(['Дата - ', self.dateEdit.text(),'\n']))
                    f.write(''.join(['Тип магнита - ', self.cBox_MagnetType.currentText(),'\n']))
                    f.write(''.join(['Серийный номер магнита - ', self.lEd_MagnetSerial.text(),'\n']))
                    f.write(''.join(['Режим работы - ', self.cBox_OperatingModes.currentText(),'\n\n']))

                self.df_result.to_csv(filename, mode='a')
                message = "Сохранение данных закончено"
                print(message)
                self.statusbar.showMessage(message)
            except FileNotFoundError:
                message = "Запись файла не состоялась."
                print(message)
                self.statusbar.showMessage(message)

        else:
            message = "Выполните сбор данных"
            print(message)
            self.statusbar.showMessage(message)

    def operating_mode1_savedata(self) -> None:
        '''-- Сохранение данных по кнопке первого метода --'''
        self.savedata('mode1')

    def operating_mode2_savedata(self) -> None:
        '''-- Сохранение данных по кнопке второго метода --'''
        self.savedata('mode2')

    def operating_mode3_savedata(self) -> None:
        '''-- Сохранение данных по кнопке третьего метода --'''
        self.savedata('mode3')

    def operating_mode4_savedata(self) -> None:
        '''-- Сохранение данных по кнопке четвёртого метода --'''
        self.savedata('mode4')

    def calculate_result(self, df_name: pd.DataFrame) -> list:
        '''-- Обсчёт данных с помощью модуля calc --'''
        message = "Идёт расчёт..."
        print(message)
        self.statusbar.showMessage(message)

        spectrum = []
        deltaX = []
        deltaY = []
        P = []
        Q = []

        match self.cBox_MagnetType.currentIndex(): # Параметры катушек из инициализации
            case 0 | 1:
                N = 2
                magnet_type = 'quadrupole'
                r = 1.915
                h = 2.1
                aperture_radius = 0.016
                coef_E = 2.56*pow(10, -5) # 1/39000
                coef_C = 1*pow(10, -5)    #1/100000
                magnet_length = 0.09   #длина магнита
            case 2:
                N = 3
                magnet_type = 'sextupole'
                r = 2.065 #mm
                h = 2.4 #mm
                aperture_radius = 0.019 #m
                coef_E = 2.56*pow(10, -5) # 1/39000
                coef_C = 1*pow(10, -5)    #1/100000
                magnet_length = 0.090   #длина магнита m
            
            case 3:
                N = 4
                magnet_type = 'octupole'
                r = 1.79 #mm
                h = 2.1 #mm
                aperture_radius = 0.0185 #m
                coef_E = 2.56*pow(10, -5) # 1/39000
                coef_C = 1*pow(10, -5)    #1/100000
                magnet_length = 0.090   #длина магнита m

        # Отладочный параметр для расчётов
        quant = 1

        param_list = [quant, r, h, coef_E, coef_C, N, aperture_radius, magnet_length, magnet_type]
        calc_result = calc.run(df_name, param_list)

        # spectrum, deltaX, deltaY, alpha, H_avg, P, Q = calc_result # P, Q - временные коэффициенты, потом уберутся

        return calc_result
   
if __name__ == '__main__':
    # app = QApplication(sys.argv)
    app = QApplication([])
    harm = MainUI()
    harm.show()
    
    try: app.exec_()
    # try: sys.exit(app.exec_())
    except SystemExit: print("Closing Window...")