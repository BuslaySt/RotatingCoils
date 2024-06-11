# программа принимает на вход массив данных df,
# находит нулевые импульсы и отдельные угловые импульсы 
# проводит интегрирование по одному периоду и далее усреднение по нескольким периодам
# вариант для использования в качестве модуля
# применяется округление до 6 знаков
#Version 3 - 07/06/24 - разделение по разным модулям

import pandas as pd
import numpy as np
import math

from tqdm import tqdm   # Progress bar
from icecream import ic # Debug print
import calc_v3a as calc             # Самоимпорт для совместимости кода
import qs #модуль вычисления коэффициентов и параметров для квадруполей и секступолей
import oct #модуль вычисления коэффициентов и параметров для октуполей
import time
import pathlib
import os
from datetime import date


def integrate_dataframe(df_name, coef_E, coef_C, quant, time_coef) -> tuple:
    '''
    Функция вычисляет интеграл датафрейма
   
    '''
    
    timestamp = df_name.timestamp 
    ch_E = -1*df_name.ch_a      # channel_A = некомпенсированный сигнал
    ch_C = df_name.ch_c # channel_C = компенсированный канал
    zeroPulse = df_name.D0
    
    angular_step = 160/quant #160 - 1 градус поворота, quant - доля градуса
    ch_E_norm = []
    compSignal_norm = []
   
    ic('Чтение датафрейма проведено успешно')
    
    zeroPos = []
    tickPos = []
        
    for i in tqdm(df_name[df_name.D0 == 1].index):
        if (df_name.iloc[i-1].D0 == 0) & (df_name.iloc[i].D0 == 1):
            zeroPos.append(i)
               
    ic('Количество периодов: ', len(zeroPos))
    ic(zeroPos)    
    
    start_period = 1
    end_period = len(zeroPos)-2
    
    periods = range(start_period, end_period)
    if len(periods)<2:
        return
  
    allPeriodC = []
    allPeriodUc = []
    
    #вычисление постоянной составляющей
           
    ch_E_norm = calc.minus_constant (ch_E, zeroPos[0], zeroPos[-1])
    compSignal_norm = calc.minus_constant (ch_C, zeroPos[0], zeroPos[-1])
        
    # Интегрирование по каждому периоду отдельно
     
    for p in periods:
        
        tickPos = []
        df_work = df_name[zeroPos[p]:zeroPos[p+1]].reset_index(drop = True)
        tick = dict([(i,d) for i,d in zip(df_work.index, df_work.D1)])
        for j in (df_work[df_work.D1 == 1].index):
            if j > 0:
                if (tick[j-1] == 0) & (tick[j] == 1):
                    tickPos.append(j)
             
        delta = tickPos[1] - tickPos[0]
        ic(len(tickPos))
        ic(delta)
        ic('Integral calculation for period', p)
        dx = abs(time_coef * (df_work.timestamp[1] - df_work.timestamp[0])) #перевод отметок времени из нс в с 
        ic(dx)
                
        intC = []
        intUc = []
        counter = 0
        start = zeroPos[p]
        finish = zeroPos[p+1]
        period = finish - start
        
        
        #поиск границ отдельных периодов для вычисления интеграла по ним
        for i in range(len(tickPos)):
            if (tickPos[i] <= delta):
                startPos = i
                ic(tickPos[startPos])
                ic(start)
                
            if ((period - tickPos[i]) <= delta):
                finishPos = i
                
                ic(tickPos[finishPos])
                ic(finish)
        
        curr_pos = 0
        sumC = 0
        sumU = 0
        for pos in tickPos[startPos:finishPos+1]:
            counter +=1
            if counter == angular_step:
                curr_pos = pos 
                
                for int_counter in range(start, curr_pos+1):
                    
                    sumC += compSignal_norm[int_counter]
                    sumU += ch_E_norm[int_counter]
                                
                intC.append(coef_C*sumC*dx)
                intUc.append(coef_E*sumU*dx)
                counter = 0
                start = curr_pos + 1
            
            if curr_pos > finish:
                break
        
        ic(len(intC))
        ic(len(intUc))
               
        corrIntUc = calc.minus_integration_constant(intUc)
        
        allPeriodC.append(intC)
        allPeriodUc.append(corrIntUc)
    
    avgIntC = calc.integral_averaging(allPeriodC)
    avgIntUc = calc.integral_averaging(allPeriodUc) 
    
    return avgIntC, avgIntUc 

def integral_averaging (allPeriod) -> tuple:
  
    '''
    вычисление усредненного значения интегралов по нескольким периодам через транспонирование двухмерного списка			
    ''' 
    
    avgInt = []
    arrInt = np.asarray(allPeriod)
    aarrIntTransp = arrInt.transpose()
    
    for item in aarrIntTransp:
        avgInt.append(sum(item)/len(arrInt))
   
    return (avgInt)

def minus_integration_constant (integral_list):
    corrected_integral = []
    for teta in range(len(integral_list)):
        corrected_integral.append(integral_list[teta] - teta*integral_list[-1]/len(integral_list))
    return corrected_integral

def minus_constant (channel_name, zeroPos_start, zeroPos_end):
    '''
    функция убирает постоянную составляющую из входного сигнала
    '''
    constant = sum(channel_name[k] for k in range (zeroPos_start, zeroPos_end + 1))/ ((zeroPos_end+1)-zeroPos_start) 
    channel_name_norm = []   
    for i in tqdm(range(zeroPos_start, zeroPos_end + 1), desc = 'Коррекция постоянной составляющей во входном сигнале'):
        channel_name_norm.append(channel_name[i] - constant)
 
    return channel_name_norm


def run(df_name, parameters):
    '''
    Функция обеспечивает начальный запуск скриптов обработки 
    с определением типа магнита и соответствующего пути

    
    '''

    quant  = parameters[0]
    r  = parameters[1]
    h = parameters[2]
    coef_E = parameters[3]
    coef_C = parameters[4]
    N = parameters[5]
    aperture_radius = parameters[6]
    magnet_length = parameters[7]
    magnet_type = parameters[8]

    time_coef = math.pow(10, -9)
    intC = []
    intU = []
    
    if N == 2:
        coil_count = 56
        outer_coil_radius =(5*r + 2*h)/1000# в метрах
        intC, intU = calc.integrate_dataframe(df_name, coef_E, coef_C, quant, time_coef)
        sensC, sensU, sens_minus = qs.quadrupole_coefficient(r, h)
        calculation_result = qs.harmonic_calculation(intC, intU, sensC, sensU, outer_coil_radius, N, sens_minus, quant, aperture_radius, magnet_length, coil_count)
        
    elif N == 3:
        coil_count = 64
        outer_coil_radius =(5*r + 2*h)/1000 # в метрах
        intC, intU = calc.integrate_dataframe(df_name, coef_E, coef_C, quant, time_coef)
        sensC, sensU, sens_minus = qs.sextupole_coefficient(r, h)
        calculation_result = qs.harmonic_calculation(intC, intU, sensC, sensU, outer_coil_radius, N, sens_minus, quant, aperture_radius, magnet_length, coil_count)
        
    elif N == 4:
        coil_count = 28
        R0 = 12.3#0.0123 mm
        Leff = 0.200 #m
        outer_coil_radius = (4*r + h)/1000# в метрах
        intC, intU = calc.integrate_dataframe(df_name, coef_E, coef_C, quant, time_coef)
        sensC, sensU, sens_minus = oct.octupole_coefficient(r, h, coil_count, R0, Leff)
        calculation_result = oct.harmonic_calculation(intC, intU, sensC, sensU, outer_coil_radius, N, sens_minus, quant, aperture_radius, magnet_length, coil_count, R0, Leff)
    return calculation_result

if __name__ == "__main__":
    '''-- Обсчёт данных с помощью модуля calc без использования праграммы управления harm --'''

    startTime = time.time()
    dirPath = pathlib.Path(__file__).parent
    result_dir = pathlib.Path('result') # каталог для сохранения результатов обработки
    filename = ["rawdata_5_2024-06-06_16-33.csv", "rawdata_4_2024-06-06_16-30.csv", "rawdata_3_2024-06-06_16-27.csv", "rawdata_2_2024-06-06_16-24.csv", "rawdata_1_2024-06-06_16-21.csv"] #сюда вводятся имена файлов, подлежащие обработке, сами файлы должнылежать в каталоге data относительно места запуска скрипта
    data_dir = pathlib.Path('data')
        

    for file in filename:
        csvLoc = os.path.join(dirPath, data_dir, file)
        df_name = pd.read_csv(csvLoc, delimiter="," )
        
        spectrum = []
        deltaX = []
        deltaY = []
        alpha = []
        H_avg = []
        P = []
        Q = []

        
        #запрос количества полюсов магнита
        int(input('Input N for 2n-pole magnet: '))
        
        quant = 1
            
        if N == 2:
            magnet_type = 'quadrupole'
            r = 1.915#0.001915 #m
            h = 2.1#0.0021 #m
            aperture_radius = 0.016 #m
            coef_E = 2.56*pow(10, -5) # 1/39000
            coef_C = 1*pow(10, -5)    #1/100000
            magnet_length = 0.090   #длина магнита m
            ic(N)
            ic(magnet_type)
            
        elif N == 3:
            magnet_type = 'sextupole'
            r = 2.065 #mm
            h = 2.4 #mm
            aperture_radius = 0.019 #m
            coef_E = 2.56*pow(10, -5) # 1/39000
            coef_C = 1*pow(10, -5)    #1/100000
            magnet_length = 0.090   #длина магнита m
            ic(N)
            ic(magnet_type)
          
        elif N == 4:
            magnet_type = 'octupole'
            r = 1.79 #mm
            h = 2.1 #mm
            aperture_radius = 0.0185 #m
            coef_E = 2.56*pow(10, -5) # 1/39000
            coef_C = 1*pow(10, -5)    #1/100000
            magnet_length = 0.090   #длина магнита m
            ic(N)
            ic(magnet_type)
        
        param_list = [quant, r, h, coef_E, coef_C, N, aperture_radius, magnet_length, magnet_type]
            
        calc_result = calc.run(df_name, param_list)
        spectrum, deltaX, deltaY, alpha, H_avg, P, Q = calc_result

        finalTime = time.time()
        d = date.today()
        frmt = d.strftime("%d_%m_%y")
        p = time.strftime("%H_%M_%d_%m_%y")

        result_name = f'result_{magnet_type}_calc3.0_{file}_{p}.txt'
        resultLoc = os.path.join(dirPath, result_dir, result_name)
    
        num = abs(hash(p))

        ic(resultLoc)
        with open(resultLoc, 'w') as output:
            output.write(resultLoc  + ' quant is ' + str(quant) + "\n" + 'P = ' + str(P) + "\n" + 'Q = ' + str(Q) + "\n")
            output.write('Spectrum is'+ "\n")
            output.write(str(spectrum) + "\n")
            output.write('Delta X'+ "\n")
            output.write(str('%.7f' %deltaX) + "\n")
            output.write('Delta Y'+ "\n")
            output.write(str('%.7f' %deltaY) + "\n")
            output.write('Alpha ' + "\n" + str('%.7f' %alpha) + "\n")
            output.write('H_avg ' + "\n" + str('%.9f' %H_avg)+ "\n" + 'Run ID' + "\n" + str(num))
            
    ic('Job start time', time.ctime(startTime))
    ic('Job finish time', time.ctime(finalTime))