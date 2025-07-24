# программа принимает на вход массив данных df_name,
# находит нулевые импульсы и отдельные угловые импульсы 
# проводит интегрирование по одному периоду и далее усреднение по нескольким периодам

# Version 4 - 24/07/25 - разделение по разным модулям
#
# Changelog: часть функций из модуля calc вынесены в универсальный модуль service. Код существенно упрощен, исправлены ошибки,  
# повышено быстродействие. 
#

import pandas as pd
import numpy as np
import math
import service

from icecream import ic # Debug print
import calc            # Самоимпорт для совместимости кода
import qs  #модуль вычисления коэффициентов и параметров для квадруполей и секступолей
import oct #модуль вычисления коэффициентов и параметров для октуполей
import time
import pathlib
import os
from datetime import date

#ic.disable()
def integrate_dataframe(df_name, coef_E, coef_C, quant, time_coef) -> tuple:
    '''
      
    Функция определяет границы периодов по каналу D0 энкодера, заведенному в АЦП, выделяет из всего датафрейма отдельные наборы, соответствующие периодам, 
    вычисляет интегралы компенсированного и некомпенссированного сигналов по каждому периоду.
    Численное интегрирование реализовано по методу прямоугольников.
    После интегрирования проводится компенсация нарастающего дрейфа как линейной зависимости от угла поворота (реализовано в отдельной функции)
    и усреднение результата интегрирования по соответствующим угловым отсчетам всех периодов (реализовано в отдельной функции).
    Функция возвращает кортежи компенсированного и некомпенсированного сигналов, каждый
    представляет один усредненный период для вычисления коэффициентов преобразования Фурье.
    
    ------------------------------------------------------------------------------------
    Переменные

        df_name : датафрейм Pandas
            Содержит выдачу данных АЦП по двум аналоговым каналам 
            (компенсированная и некомпенсированная катушки)
            и двум цифровым (угловой и нулевой выходы энкодера), 
            также содержит временную метку.
        quant : float
            Кратность шага интегрирования 
            (q = 1 соответствует привязке к 1 градусу поворота)
        coef_E : float
            Коэффициент усиления для некомпенсированного сигнала
        coef_C : float
            Коэффициент усиления для компенсированного сигнала
        time_coef : float
            Перевод из формата АЦП в секунды
    
    '''
    
    timestamp = df_name.timestamp 
    #ch_E = df_name.ch_a      #: channel_A = некомпенсированный сигнал
    #ch_C = df_name.ch_c #: channel_C = компенсированный канал
    zeroPulse = df_name.D0 # канал импульса оборота
    angular_step = 160/quant #:160 - 1 градус поворота, quant - доля градуса
       
    ic('Чтение датафрейма проведено успешно')
    
    zeroPos = []
    zeroPos = [n for n in df_name[df_name.D0 == 1].index if (df_name.iloc[n-1].D0 == 0) & (df_name.iloc[n].D0 == 1)]
    ic('Количество периодов: ', len(zeroPos))
    ic(zeroPos)    
    
    start_period = 0
    end_period = len(zeroPos)-1
    
    periods = range(start_period, end_period)
    if len(periods)<2:
        return
  
    allPeriodC = []
    allPeriodUc = []
    
    #вычитание постоянной составляющей из сигналов
    print('Вычисление постоянной составляющей в канале E')       
    ch_E_avg = service.avg_constant (df_name.ch_a, zeroPos[0], zeroPos[-1])
    
    print('Вычисление постоянной составляющей в канале C')
    compSignal_avg = service.avg_constant (df_name.ch_c, zeroPos[0], zeroPos[-1])
    dx = abs(time_coef * (timestamp[1] - timestamp[0])) #перевод отметок времени из нс в с 
    ic(dx)       
    # Интегрирование по каждому периоду отдельно
    for p in periods:
        ch_E_norm = []
        compSignal_norm = []
        tickPos = []
        df_work = df_name[zeroPos[p]:zeroPos[p+1]].reset_index(drop = True)
        tick = dict([(i,d) for i,d in zip(df_work.index, df_work.D1)])
        ch_E_norm = np.array(df_work.ch_a) - ch_E_avg
        ic(len(ch_E_norm))
        compSignal_norm = np.array(df_work.ch_c) - compSignal_avg
        ic(len(compSignal_norm))

        for j in (df_work[df_work.D1 == 1].index):
            if (j == 0) & (tick[j] == 1):
                tickPos.append(j)
            elif (j > 0) & (tick[j] == 1) & (tick[j-1] == 0):
                tickPos.append(j)
             
        #delta = tickPos[1] - tickPos[0]
        ic('Integral calculation for period', p)
        ic(len(tickPos))
        #ic(delta)
        intC = []
        intUc = []
        
        period = len(df_work)
        ic(period)
        
        #поиск границ отдельных периодов для вычисления интеграла по ним
                
        counter = 0
        start = tickPos[0]
        sumC_current = compSignal_norm[start]
        sumU_current = ch_E_norm[start]
                
        for pos in tickPos:
            counter +=1
            if counter == angular_step:
                sumC_current = sumC_current + sum(compSignal_norm[start:pos+1]) 
                sumU_current = sumU_current + sum(ch_E_norm[start:pos+1])
                                
                intC.append(coef_C*sumC_current*dx)
                intUc.append(coef_E*sumU_current*dx)
                counter = 0
                start = pos + 1
            
                    
        ic(len(intC))
        ic(len(intUc))
               
        corrIntUc = service.minus_integration(intUc)
        corrIntС = service.minus_integration(intC)
        allPeriodC.append(corrIntС)
        allPeriodUc.append(corrIntUc)
    
    avgIntC = service.array_averaging(allPeriodC)
    avgIntUc = service.array_averaging(allPeriodUc)
    avgValC = np.mean(avgIntC) 
    avgValUc = np.mean(avgIntUc)
    avgIntC = np.array(avgIntC) - avgValC
    avgIntUc = np.array(avgIntUc) - avgValUc
    
    return avgIntC, avgIntUc


def fourier (integral_compensated_value, integral_uncompensated_value, N, quant):
    
    dx = math.pi/(quant*180)
    depth = 16  # количество гармоник
    
    p = []
    q = []
    P = []	
    Q = []
    alpha = []
    start = 0 #начальный угол
    end = 360
    period = np.arange(start+1/quant, end+1/quant, 1/quant)
    ic(len(period))

    for n in range (1, depth+1):
        f_cos = []
        f_sin = []
        sumC = 0
        sumS = 0
        
        #подынтегральные выражения для расчета коэффициентов разложения в ряд Фурье
        f_cos = [(integral_compensated_value[count]*math.cos(n*teta*math.pi/180)) for count, teta in enumerate(period)]
        f_sin = [(integral_compensated_value[count]*math.sin(n*teta*math.pi/180)) for count, teta in enumerate(period)]
    
        sumC = sum(f_cos)
        sumS = sum(f_sin)
        
        p.append((1/math.pi)*sumC*dx)
        q.append((1/math.pi)*sumS*dx)
    ic(len(p))
    ic(len(q))       
                  
    for n in range(1, N+1):
        F_cos = []
        F_sin = []
    
        sum_C = 0
        sum_S = 0
        
        #подынтегральные выражения для расчета коэффициентов разложения в ряд Фурье
        F_cos = [(integral_uncompensated_value[count]*math.cos(n*(teta)*math.pi/180)) for count, teta in enumerate(period)]
        F_sin = [(integral_uncompensated_value[count]*math.sin(n*(teta)*math.pi/180)) for count, teta in enumerate(period)]#
    
        sum_C = sum(F_cos)
        sum_S = sum(F_sin)
        
        P.append((1/math.pi)*sum_C*dx)
        Q.append((1/math.pi)*sum_S*dx)

    ic(len(F_cos))    
    ic(len(P))
    ic(len(Q))
    return P, Q, p, q

def run (df_name, parameters):
    '''
    Функция обеспечивает начальный запуск скриптов обработки с определением типа магнита 
    и соответствующей последовательности обработки данных.
    В зависимости от типа магнита запускаются скрипты из модулей qs (для квадрупольных и секступольных источников)
    или oct (для октупольных источников).

    ------------------------------------------------------------------------------------
    Переменные
    
        df_name : датафрейм Pandas
            Содержит выдачу данных АЦП по двум аналоговым каналам 
            (компенсированная и некомпенсированная катушки) и двум 
            цифровым (угловой и нулевой выходы энкодера), 
            также содержит временную метку.
        parameters : list
            Содержит параметры катушки, тип и параметры магнита:
                quant : float
                    Кратность шага интегрирования 
                    (q = 1 соответствует привязке к 1 градусу поворота)
                r : float
                    Параметр катушки, ширина 
                h : float
                    Параметр катушки, расстояние между центрами 
                    соседних катушек в плате
                coef_E : float
                    Коэффициент усиления для некомпенсированного сигнала
                coef_C : float
                    Коэффициент усиления для компенсированного сигнала
                N : int
                    Количество пар полюсов, характеристика типа магнита 
                    (2 для квадрупольного, 3 для секступольного, 4 для октупольного) 
                aperture_radius : float
                    Радиус апертуры магнита
                magnet_length : float
                    Длина рабочей области магнита
                magnet_type : str
                    Наименование типа магнита
    
    '''
    
    quant  = parameters[0]
    coef_E = parameters[3]
    coef_C = parameters[4]
    N = parameters[5]
    time_coef = math.pow(10, -9)
    intC = []
    intU = []
    
    intC, intU = calc.integrate_dataframe(df_name, coef_E, coef_C, quant, time_coef)
    P, Q, p, q = calc.fourier(intC, intU, N, quant)
    calc_result = calc.values_computation(P, Q, p, q, parameters)
    ic('DFT coefs are ready')
    return calc_result  #, intC, intU - отключен вывод внутренних данных, необходимых для программы диагностики

def values_computation(P, Q, p, q, parameters):
    '''
    Функция обеспечивает начальный запуск скриптов обработки с определением типа магнита 
    и соответствующей последовательности обработки данных.
    В зависимости от типа магнита запускаются скрипты из модулей qs (для квадрупольных и секступольных источников)
    или oct (для октупольных источников).

    ------------------------------------------------------------------------------------
    Переменные
    
        P : list

        Q: list

        p: list

        q: list

        Переменные содержат списки с коэффициентам разложения некомпенсированного сигнала в ряд Фурье.
        parameters : list
            Содержит параметры катушки, тип и параметры магнита:
                quant : float
                    Кратность шага интегрирования 
                    (q = 1 соответствует привязке к 1 градусу поворота)
                r : float
                    Параметр катушки, ширина 
                h : float
                    Параметр катушки, расстояние между центрами 
                    соседних катушек в плате
                coef_E : float
                    Коэффициент усиления для некомпенсированного сигнала
                coef_C : float
                    Коэффициент усиления для компенсированного сигнала
                N : int
                    Количество пар полюсов, характеристика типа магнита 
                    (2 для квадрупольного, 3 для секступольного, 4 для октупольного) 
                aperture_radius : float
                    Радиус апертуры магнита
                magnet_length : float
                    Длина рабочей области магнита
                magnet_type : str
                    Наименование типа магнита
    
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
    
    
    if N == 2:
        coil_count = 56
        outer_coil_radius =(5*r + 2*h)/1000# в метрах
        sensC, sensU, sens_minus = qs.quadrupole_coefficient(r, h)
        calculation_result = qs.harmonic_calculation(P, Q, p, q, sensC, sensU, outer_coil_radius, N, sens_minus, quant, aperture_radius, magnet_length, coil_count)
        
    elif N == 3:
        coil_count = 64
        outer_coil_radius =(5*r + 2*h)/1000 # в метрах
        sensC, sensU, sens_minus = qs.sextupole_coefficient(r, h)
        calculation_result = qs.harmonic_calculation(P, Q, p, q, sensC, sensU, outer_coil_radius, N, sens_minus, quant, aperture_radius, magnet_length, coil_count)
        
    elif N == 4:
        coil_count = 28
        R0 = 12.3#0.0123 mm
        Leff = 0.200 #m
        outer_coil_radius = (4*r + h)/1000# в метрах
        sensC, sensU, sens_minus = oct.octupole_coefficient(r, h)
        calculation_result = oct.harmonic_calculation(P, Q, p, q, sensC, sensU, outer_coil_radius, N, sens_minus, quant, aperture_radius, magnet_length, coil_count, R0, Leff)
    return calculation_result

if __name__ == "__main__":
    '''
    Автономный обсчёт данных с помощью модуля без использования запускающей программы управления. 
    Применим для обработки сохраненных датафреймов отдельно от процесса измерения. 
    Каждый файл, внесенный в список filename, содержит 10-20 периодов вращения катушки и является объектом последующей обработки. 
    ------------------------------------------------------------------------------------
    Переменные
        
        filename : list
            Содержит перечень файлов в формате .csv с результатами измерения. 
        N : int
            Количество пар полюсов, характеристика типа магнита 
            (2 для квадрупольного, 3 для секступольного, 4 для октупольного) 
        r : float
            Параметр катушки, ширина 
        h : float
            Параметр катушки, расстояние между центрами соседних катушек в плате
        aperture_radius : float
            Радиус апертуры магнита
        coef_E : float
            Коэффициент усиления для некомпенсированного сигнала
        coef_C : float
            Коэффициент усиления для компенсированного сигнала
        magnet_length : float
            Длина рабочей области магнита
    
    '''

    startTime = time.time()
    dirPath = pathlib.Path(__file__).parent
    result_dir = pathlib.Path('result') # каталог для сохранения результатов обработки
    
    data_dir = pathlib.Path('src_data') # каталог с данными, подлежащими обработке
    P = []
    Q = []
    spectrum = []
    deltaX = []
    deltaY = []
    alpha = []
    H_avg = []
    def collect_csv_files(data_path):
        filename = []
 
        for file in os.listdir(data_path):
            if file.endswith(".csv"):
                filename.append(file)
 
        return filename    
    filename = collect_csv_files(data_dir)

    #запрос количества полюсов магнита
    N = 2#int(input('Input N for 2n-pole magnet: '))
        
    quant = 1
            
    if N == 2:
        magnet_type = 'quadrupole'
        r = 1.915# 0.001915 #m
        h = 2.1 # 0.0021 #m
        aperture_radius = 0.016 #m
        coef_E = 2.56*pow(10, -5) # 1/39000  
        coef_C = 1*pow(10, -5)    #1/100000 
        magnet_length = 0.090   #длина магнита m
        ic(N)
        ic(magnet_type)
            
    elif N == 3:
        magnet_type = 'sextupole'
        r = 2.065 #mm 1.45 эксп. на 24мм катушке
        h = 2.4 #mm 1.4 эксп. на 24мм катушке
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
   
    for file in filename:
        csvLoc = os.path.join(dirPath, data_dir, file)
        df_name = pd.read_csv(csvLoc, delimiter="," ) 
        ic(file)
        
        calc_result = calc.run(df_name, param_list)
        spectrum.append(calc_result[0])
        deltaX.append(calc_result[1])
        deltaY.append(calc_result[2])
        alpha.append(calc_result[3])
        H_avg.append(calc_result[4])
        P.append(calc_result[5])
        Q.append(calc_result[6])
        
    finalTime = time.time()
    d = date.today()
    frmt = d.strftime("%d_%m_%y")
    p = time.strftime("%H_%M_%d_%m_%y")
    result_name = f'_res_{magnet_type}_calc3.2_{p}.txt'
    resultLoc = os.path.join(dirPath, result_dir, result_name)
    
    num = abs(hash(p))

    ic(resultLoc)
    with open(resultLoc, 'w') as output:
        output.write(resultLoc  + ' quant is ' + str(quant) + "\n" + 'P = ' + str(P) + "\n" + 'Q = ' + str(Q) + "\n")
        output.write('Spectrum is'+ "\n")
        output.write(str(spectrum) + "\n")
        output.write('Delta X'+ "\n")
        output.write(str(deltaX) + "\n")
        output.write('Delta Y'+ "\n")
        output.write(str(deltaY) + "\n")
        output.write('Alpha ' + "\n" + str(alpha) + "\n")
        output.write('H_avg ' + "\n" + str(H_avg)+ "\n" + 'Run ID' + "\n" + str(num))
            
    ic('Job start time', time.ctime(startTime))
    ic('Job finish time', time.ctime(finalTime))
