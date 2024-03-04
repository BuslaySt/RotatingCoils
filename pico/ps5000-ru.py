# ПОдключение необходимых модулей
import ctypes
import numpy as np
from picosdk.ps5000a import ps5000a as ps
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc

# Создание объектов chandle, status
chandle = ctypes.c_int16()
status = {}

# Подключение к осциллографу
# Установка разрешения 12 бит
resolution =ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_12BIT"]
# Получение статуса и chandle для дальнейшего использования
status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(chandle), None, resolution)

try:
    assert_pico_ok(status["openunit"])
except: # PicoNotOkError:

    powerStatus = status["openunit"]

    if powerStatus == 286:
        status["changePowerSource"] = ps.ps5000aChangePowerSource(chandle, powerStatus)
    elif powerStatus == 282:
        status["changePowerSource"] = ps.ps5000aChangePowerSource(chandle, powerStatus)
    else:
        raise

    assert_pico_ok(status["changePowerSource"])

# Настройка канала A
# handle = chandle
channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
# enabled = 1
coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]
chARange = ps.PS5000A_RANGE["PS5000A_20V"]
# analogue offset = 0 V
status["setChA"] = ps.ps5000aSetChannel(chandle, channel, 1, coupling_type, chARange, 0)
assert_pico_ok(status["setChA"])

# Настройка канала B
# handle = chandle
channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"]
# enabled = 1
# coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]
chBRange = ps.PS5000A_RANGE["PS5000A_2V"]
# analogue offset = 0 V
status["setChB"] = ps.ps5000aSetChannel(chandle, channel, 1, coupling_type, chBRange, 0)
assert_pico_ok(status["setChB"])

# Получение максимального количества сэмплов АЦП
maxADC = ctypes.c_int16()
status["maximumValue"] = ps.ps5000aMaximumValue(chandle, ctypes.byref(maxADC))
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
adc2mVChAMax =  adc2mV(bufferAMax, chARange, maxADC)
adc2mVChBMax =  adc2mV(bufferBMax, chBRange, maxADC)

# Остановка осциллографа
status["stop"] = ps.ps5000aStop(chandle)
assert_pico_ok(status["stop"])

# Закрытие и отключение осциллографа
status["close"]=ps.ps5000aCloseUnit(chandle)
assert_pico_ok(status["close"])