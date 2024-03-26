# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'harmonic.ui'
#
# Created by: PyQt5 UI code generator 5.15.10
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1171, 905)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tab1 = QtWidgets.QWidget()
        self.tab1.setObjectName("tab1")
        self.tabWidget.addTab(self.tab1, "")
        self.tab2 = QtWidgets.QWidget()
        self.tab2.setObjectName("tab2")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.tab2)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.groupBox_motor = QtWidgets.QGroupBox(self.tab2)
        self.groupBox_motor.setMinimumSize(QtCore.QSize(510, 600))
        self.groupBox_motor.setObjectName("groupBox_motor")
        self.btn_Connect = QtWidgets.QPushButton(self.groupBox_motor)
        self.btn_Connect.setGeometry(QtCore.QRect(350, 40, 151, 31))
        self.btn_Connect.setObjectName("btn_Connect")
        self.cbox_SerialPort = QtWidgets.QComboBox(self.groupBox_motor)
        self.cbox_SerialPort.setGeometry(QtCore.QRect(210, 40, 121, 31))
        self.cbox_SerialPort.setObjectName("cbox_SerialPort")
        self.lbl_Port = QtWidgets.QLabel(self.groupBox_motor)
        self.lbl_Port.setGeometry(QtCore.QRect(10, 40, 61, 21))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.lbl_Port.setFont(font)
        self.lbl_Port.setObjectName("lbl_Port")
        self.Acceleration = QtWidgets.QLineEdit(self.groupBox_motor)
        self.Acceleration.setGeometry(QtCore.QRect(350, 90, 151, 31))
        self.Acceleration.setAlignment(QtCore.Qt.AlignCenter)
        self.Acceleration.setObjectName("Acceleration")
        self.lbl_Acceleration = QtWidgets.QLabel(self.groupBox_motor)
        self.lbl_Acceleration.setGeometry(QtCore.QRect(10, 89, 201, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.lbl_Acceleration.setFont(font)
        self.lbl_Acceleration.setObjectName("lbl_Acceleration")
        self.Deceleration = QtWidgets.QLineEdit(self.groupBox_motor)
        self.Deceleration.setGeometry(QtCore.QRect(350, 140, 151, 31))
        self.Deceleration.setAlignment(QtCore.Qt.AlignCenter)
        self.Deceleration.setObjectName("Deceleration")
        self.lbl_Deceleration = QtWidgets.QLabel(self.groupBox_motor)
        self.lbl_Deceleration.setGeometry(QtCore.QRect(10, 139, 211, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.lbl_Deceleration.setFont(font)
        self.lbl_Deceleration.setObjectName("lbl_Deceleration")
        self.lbl_Speed = QtWidgets.QLabel(self.groupBox_motor)
        self.lbl_Speed.setGeometry(QtCore.QRect(10, 189, 221, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.lbl_Speed.setFont(font)
        self.lbl_Speed.setObjectName("lbl_Speed")
        self.Speed = QtWidgets.QLineEdit(self.groupBox_motor)
        self.Speed.setGeometry(QtCore.QRect(350, 190, 151, 31))
        self.Speed.setAlignment(QtCore.Qt.AlignCenter)
        self.Speed.setObjectName("Speed")
        self.btn_StopRotation = QtWidgets.QPushButton(self.groupBox_motor)
        self.btn_StopRotation.setGeometry(QtCore.QRect(350, 500, 151, 81))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.btn_StopRotation.setFont(font)
        self.btn_StopRotation.setObjectName("btn_StopRotation")
        self.Turns = QtWidgets.QLineEdit(self.groupBox_motor)
        self.Turns.setGeometry(QtCore.QRect(350, 240, 151, 31))
        self.Turns.setAlignment(QtCore.Qt.AlignCenter)
        self.Turns.setObjectName("Turns")
        self.lbl_Turns = QtWidgets.QLabel(self.groupBox_motor)
        self.lbl_Turns.setGeometry(QtCore.QRect(10, 239, 221, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.lbl_Turns.setFont(font)
        self.lbl_Turns.setObjectName("lbl_Turns")
        self.btn_ContRotation = QtWidgets.QPushButton(self.groupBox_motor)
        self.btn_ContRotation.setGeometry(QtCore.QRect(10, 500, 171, 81))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.btn_ContRotation.setFont(font)
        self.btn_ContRotation.setObjectName("btn_ContRotation")
        self.btn_StartRotation = QtWidgets.QPushButton(self.groupBox_motor)
        self.btn_StartRotation.setGeometry(QtCore.QRect(190, 500, 151, 81))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.btn_StartRotation.setFont(font)
        self.btn_StartRotation.setObjectName("btn_StartRotation")
        self.lbl_ServoStatus = QtWidgets.QLabel(self.groupBox_motor)
        self.lbl_ServoStatus.setGeometry(QtCore.QRect(10, 290, 221, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.lbl_ServoStatus.setFont(font)
        self.lbl_ServoStatus.setObjectName("lbl_ServoStatus")
        self.ServoStatus = QtWidgets.QLabel(self.groupBox_motor)
        self.ServoStatus.setGeometry(QtCore.QRect(370, 290, 121, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        font.setItalic(True)
        self.ServoStatus.setFont(font)
        self.ServoStatus.setObjectName("ServoStatus")
        self.lbl_Time = QtWidgets.QLabel(self.groupBox_motor)
        self.lbl_Time.setGeometry(QtCore.QRect(10, 340, 151, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.lbl_Time.setFont(font)
        self.lbl_Time.setObjectName("lbl_Time")
        self.Time = QtWidgets.QLabel(self.groupBox_motor)
        self.Time.setGeometry(QtCore.QRect(420, 340, 41, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.Time.setFont(font)
        self.Time.setObjectName("Time")
        self.horizontalLayout.addWidget(self.groupBox_motor)
        self.groupBox_ADC = QtWidgets.QGroupBox(self.tab2)
        self.groupBox_ADC.setMinimumSize(QtCore.QSize(510, 600))
        self.groupBox_ADC.setObjectName("groupBox_ADC")
        self.cbox_SerialPort_Instrument = QtWidgets.QComboBox(self.groupBox_ADC)
        self.cbox_SerialPort_Instrument.setGeometry(QtCore.QRect(310, 40, 191, 31))
        self.cbox_SerialPort_Instrument.setObjectName("cbox_SerialPort_Instrument")
        self.cbox_SerialPort_Instrument.addItem("")
        self.lbl_Instrument = QtWidgets.QLabel(self.groupBox_ADC)
        self.lbl_Instrument.setGeometry(QtCore.QRect(20, 40, 131, 21))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.lbl_Instrument.setFont(font)
        self.lbl_Instrument.setObjectName("lbl_Instrument")
        self.lbl_Interval = QtWidgets.QLabel(self.groupBox_ADC)
        self.lbl_Interval.setGeometry(QtCore.QRect(20, 89, 201, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.lbl_Interval.setFont(font)
        self.lbl_Interval.setObjectName("lbl_Interval")
        self.lbl_Ch1 = QtWidgets.QLabel(self.groupBox_ADC)
        self.lbl_Ch1.setGeometry(QtCore.QRect(20, 189, 211, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.lbl_Ch1.setFont(font)
        self.lbl_Ch1.setObjectName("lbl_Ch1")
        self.btn_Autorecord = QtWidgets.QPushButton(self.groupBox_ADC)
        self.btn_Autorecord.setGeometry(QtCore.QRect(350, 500, 151, 81))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.btn_Autorecord.setFont(font)
        self.btn_Autorecord.setObjectName("btn_Autorecord")
        self.btn_StartRecord = QtWidgets.QPushButton(self.groupBox_ADC)
        self.btn_StartRecord.setGeometry(QtCore.QRect(10, 500, 151, 81))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.btn_StartRecord.setFont(font)
        self.btn_StartRecord.setObjectName("btn_StartRecord")
        self.lbl_Ch2 = QtWidgets.QLabel(self.groupBox_ADC)
        self.lbl_Ch2.setGeometry(QtCore.QRect(20, 240, 211, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.lbl_Ch2.setFont(font)
        self.lbl_Ch2.setObjectName("lbl_Ch2")
        self.lbl_Ch3 = QtWidgets.QLabel(self.groupBox_ADC)
        self.lbl_Ch3.setGeometry(QtCore.QRect(20, 290, 211, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.lbl_Ch3.setFont(font)
        self.lbl_Ch3.setObjectName("lbl_Ch3")
        self.lbl_Ch4 = QtWidgets.QLabel(self.groupBox_ADC)
        self.lbl_Ch4.setGeometry(QtCore.QRect(20, 340, 211, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.lbl_Ch4.setFont(font)
        self.lbl_Ch4.setObjectName("lbl_Ch4")
        self.btn_File = QtWidgets.QPushButton(self.groupBox_ADC)
        self.btn_File.setGeometry(QtCore.QRect(10, 430, 151, 51))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.btn_File.setFont(font)
        self.btn_File.setObjectName("btn_File")
        self.btn_StopRecord = QtWidgets.QPushButton(self.groupBox_ADC)
        self.btn_StopRecord.setGeometry(QtCore.QRect(170, 500, 171, 81))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.btn_StopRecord.setFont(font)
        self.btn_StopRecord.setObjectName("btn_StopRecord")
        self.Channel1Range = QtWidgets.QComboBox(self.groupBox_ADC)
        self.Channel1Range.setGeometry(QtCore.QRect(380, 190, 121, 31))
        self.Channel1Range.setObjectName("Channel1Range")
        self.Channel3Range = QtWidgets.QComboBox(self.groupBox_ADC)
        self.Channel3Range.setGeometry(QtCore.QRect(380, 290, 121, 31))
        self.Channel3Range.setObjectName("Channel3Range")
        self.Channel2Range = QtWidgets.QComboBox(self.groupBox_ADC)
        self.Channel2Range.setGeometry(QtCore.QRect(380, 240, 121, 31))
        self.Channel2Range.setObjectName("Channel2Range")
        self.Channel4Range = QtWidgets.QComboBox(self.groupBox_ADC)
        self.Channel4Range.setGeometry(QtCore.QRect(380, 340, 121, 31))
        self.Channel4Range.setObjectName("Channel4Range")
        self.Channel1Enable = QtWidgets.QCheckBox(self.groupBox_ADC)
        self.Channel1Enable.setEnabled(True)
        self.Channel1Enable.setGeometry(QtCore.QRect(330, 200, 31, 17))
        self.Channel1Enable.setText("")
        self.Channel1Enable.setChecked(True)
        self.Channel1Enable.setObjectName("Channel1Enable")
        self.Channel2Enable = QtWidgets.QCheckBox(self.groupBox_ADC)
        self.Channel2Enable.setEnabled(True)
        self.Channel2Enable.setGeometry(QtCore.QRect(330, 250, 31, 17))
        self.Channel2Enable.setText("")
        self.Channel2Enable.setObjectName("Channel2Enable")
        self.Channel3Enable = QtWidgets.QCheckBox(self.groupBox_ADC)
        self.Channel3Enable.setEnabled(True)
        self.Channel3Enable.setGeometry(QtCore.QRect(330, 300, 31, 17))
        self.Channel3Enable.setText("")
        self.Channel3Enable.setChecked(True)
        self.Channel3Enable.setObjectName("Channel3Enable")
        self.Channel4Enable = QtWidgets.QCheckBox(self.groupBox_ADC)
        self.Channel4Enable.setEnabled(True)
        self.Channel4Enable.setGeometry(QtCore.QRect(330, 350, 31, 17))
        self.Channel4Enable.setText("")
        self.Channel4Enable.setObjectName("Channel4Enable")
        self.lbl_Samples = QtWidgets.QLabel(self.groupBox_ADC)
        self.lbl_Samples.setGeometry(QtCore.QRect(20, 390, 131, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.lbl_Samples.setFont(font)
        self.lbl_Samples.setObjectName("lbl_Samples")
        self.lbl_Resolution = QtWidgets.QLabel(self.groupBox_ADC)
        self.lbl_Resolution.setGeometry(QtCore.QRect(20, 139, 201, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.lbl_Resolution.setFont(font)
        self.lbl_Resolution.setObjectName("lbl_Resolution")
        self.Resolution = QtWidgets.QComboBox(self.groupBox_ADC)
        self.Resolution.setGeometry(QtCore.QRect(310, 140, 191, 31))
        self.Resolution.setObjectName("Resolution")
        self.Samples = QtWidgets.QLabel(self.groupBox_ADC)
        self.Samples.setGeometry(QtCore.QRect(380, 390, 41, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.Samples.setFont(font)
        self.Samples.setObjectName("Samples")
        self.Interval = QtWidgets.QComboBox(self.groupBox_ADC)
        self.Interval.setGeometry(QtCore.QRect(310, 90, 91, 31))
        self.Interval.setObjectName("Interval")
        self.SampleRate = QtWidgets.QLabel(self.groupBox_ADC)
        self.SampleRate.setGeometry(QtCore.QRect(430, 100, 61, 16))
        self.SampleRate.setObjectName("SampleRate")
        self.horizontalLayout.addWidget(self.groupBox_ADC)
        self.tabWidget.addTab(self.tab2, "")
        self.horizontalLayout_2.addWidget(self.tabWidget)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Harmonic coil"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab1), _translate("MainWindow", "Измерение"))
        self.groupBox_motor.setTitle(_translate("MainWindow", "Управление приводом"))
        self.btn_Connect.setText(_translate("MainWindow", "Подключиться"))
        self.lbl_Port.setText(_translate("MainWindow", "Порт"))
        self.Acceleration.setText(_translate("MainWindow", "20"))
        self.lbl_Acceleration.setText(_translate("MainWindow", "Ускорение, мс"))
        self.Deceleration.setText(_translate("MainWindow", "20"))
        self.lbl_Deceleration.setText(_translate("MainWindow", "Торможение, мс"))
        self.lbl_Speed.setText(_translate("MainWindow", "Скорость, град/сек"))
        self.Speed.setText(_translate("MainWindow", "60"))
        self.btn_StopRotation.setText(_translate("MainWindow", "Стоп"))
        self.Turns.setText(_translate("MainWindow", "10"))
        self.lbl_Turns.setText(_translate("MainWindow", "Количество оборотов"))
        self.btn_ContRotation.setText(_translate("MainWindow", "Непрерывно"))
        self.btn_StartRotation.setText(_translate("MainWindow", "Старт"))
        self.lbl_ServoStatus.setText(_translate("MainWindow", "Статус привода"))
        self.ServoStatus.setText(_translate("MainWindow", "Не подключен"))
        self.lbl_Time.setText(_translate("MainWindow", "Время движения, сек"))
        self.Time.setText(_translate("MainWindow", "0"))
        self.groupBox_ADC.setTitle(_translate("MainWindow", "Настройки АЦП"))
        self.cbox_SerialPort_Instrument.setItemText(0, _translate("MainWindow", "Picoscope 5442D MSO"))
        self.lbl_Instrument.setText(_translate("MainWindow", "Инструмент"))
        self.lbl_Interval.setText(_translate("MainWindow", "Интервал сэмплирования, нс"))
        self.lbl_Ch1.setText(_translate("MainWindow", "Канал A"))
        self.btn_Autorecord.setText(_translate("MainWindow", "Авто"))
        self.btn_StartRecord.setText(_translate("MainWindow", "Начать запись"))
        self.lbl_Ch2.setText(_translate("MainWindow", "Канал B"))
        self.lbl_Ch3.setText(_translate("MainWindow", "Канал C"))
        self.lbl_Ch4.setText(_translate("MainWindow", "Канал D"))
        self.btn_File.setText(_translate("MainWindow", "Выбор файла.."))
        self.btn_StopRecord.setText(_translate("MainWindow", "Остановить запись"))
        self.lbl_Samples.setText(_translate("MainWindow", "Количество сэмплов"))
        self.lbl_Resolution.setText(_translate("MainWindow", "Разрядность, бит"))
        self.Samples.setText(_translate("MainWindow", "0"))
        self.SampleRate.setText(_translate("MainWindow", "1 МС/c"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab2), _translate("MainWindow", "Настройки"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
