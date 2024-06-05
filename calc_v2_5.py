# программа принимает на вход массив данных df,
# находит нулевые импульсы и отдельные угловые импульсы 
# проводит интегрирование по одному периоду и далее усреднение по нескольким периодам
# вариант для использования в качестве модуля
# применяется округление до 6 знаков
#Version 2.5 - 04/06/24 - добавлена октупольная катушка и выровнены потоки обработки

import pandas as pd
import numpy as np
import math

from tqdm import tqdm   # Progress bar
from icecream import ic # Debug print
import calc_v2_5 as calc             # Самоимпорт для совместимости кода
import time
import pathlib
import os
from datetime import date


def integrate_dataframe(df_name, coef_E, coef_C, quant, time_coef) -> tuple:
    '''
    Функция вычисляет интеграл датафрейма
    roundN - порядок округления для ускорения расчетов.
    '''
    
    timestamp = df_name.timestamp 
    ch_E = -1*df_name.ch_a      # channel_A = ...
    ch_C = df_name.ch_c # channel_C = ... для катушки с коэффициентом усиления 991
    zeroPulse = df_name.D0
    
    angular_step = 160/quant #160 - 1 degree, quant - fraction of a degree
    ch_E_norm = []
    compSignal_norm = []
   
    ic('DF has been read successfully')
    
    zeroPos = []
    tickPos = []
        
    for i in tqdm(df_name[df_name.D0 == 1].index):
        if (df_name.iloc[i-1].D0 == 0) & (df_name.iloc[i].D0 == 1):
            zeroPos.append(i)
               
    ic('Period count is', len(zeroPos))
    ic(zeroPos)    
    
    start_period = 1
    end_period = len(zeroPos)-2
    
    #tick = dict([(i,d) for i,d in zip(df_name.index, df_name.D1)])
    #for j in (df_name[df_name.D1 == 1].index):
    #    if j > zeroPos[start_period]:
    #        if (tick[j-1] == 0) & (tick[j] == 1):
    #            tickPos.append(j)

    periods = range(start_period, end_period)
    if len(periods)<2:
        return
  
    allPeriodC = []
    allPeriodUc = []
    
    #вычисление постоянной составляющей
    #TODO переработать устранение постоянной составляющей
        
    ch_E_norm = calc.minus_constant (ch_E, zeroPos[0], zeroPos[-1])
    compSignal_norm = calc.minus_constant (ch_C, zeroPos[0], zeroPos[-1])
        
    # Интегрирование по каждому периоду отдельно
    # TODO Stepan: лучше выделить в отдельную функцию
    
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
        #file = open('debug.txt', 'w')
        #file.write(str(intC))
        #file.write(str(intUc))
        
        corrIntUc = calc.minus_integration_constant(intUc)
        
        #file.write(str(corrIntUc))
        allPeriodC.append(intC)
        allPeriodUc.append(corrIntUc)
    
    avgIntC = calc.integral_averaging(allPeriodC)
    avgIntUc = calc.integral_averaging(allPeriodUc) 
    #file.write('average')
    #file.write(str(avgIntC))
    #file.write(str(avgIntUc))
    #file.close()    
        
    return (avgIntC, avgIntUc) # Stepan: после служебной команды return надо ставить пробел,
                               # чтобы не путать по синтаксису с вызовом функции.
                               # Здесь в круглых скобках - не аргументы, а кортеж (tuple)

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
    for teta in tqdm(range(len(integral_list)), desc = 'Correcting for integration constant'):
        corrected_integral.append(integral_list[teta] - teta*integral_list[-1]/len(integral_list))
    return corrected_integral

def minus_constant (channel_name, zeroPos_start, zeroPos_end):
    '''
    функция убирает постоянную составляющую из входного сигнала
    '''
    constant = sum(channel_name[k] for k in range (zeroPos_start, zeroPos_end + 1))/ ((zeroPos_end+1)-zeroPos_start) 
    channel_name_norm = []   
    for i in tqdm(range(zeroPos_start, zeroPos_end + 1), desc = 'Correcting signal for constant component'):
        channel_name_norm.append(channel_name[i] - constant)
 
    return channel_name_norm

def quadrupole_coefficient(r: float, h: float) -> tuple:
    '''
    Функция вычисляет чувствительность катушки с квадруполльной компенсацией и заданными параметрами r, h. 
    При этом дополнительно задается тип 
    sensitivity_uncompensated - некомпенсированная чувствительность
    sensitivity_compensated - компенсированная чувствительность
    r = 1.915 
    h = 2.1 #старая катушка 30 мм

    r = 1.45
    h = 1.4 #новая узкая катушка 24 мм
    '''
    ic('Calculating quadrupole bucking coefficient...')
    N = 2
    depth = 16
    r4 = r
    r5 = r + h
    r2 = r + h
    r1 = 2*r + r2
    r6 = r5 + 2*r
    r7 = r6 + h
    r8 = r7 + 2*r

    betaE = r7/r8
    betaD = r5/r6
    betaB = r1/r2
    roB = r2/r8
    roC = r4/r8
    roD = r6/r8
        
    sensitivity_compensated = []
    
    for n in range (1, depth+1):
        s_ED = 1 - math.pow(betaE, n) - math.pow(roD, n)*(1 - math.pow(betaD, n))
        s_BC = math.pow(roC, n)*(1 - math.pow(-1, n)) - math.pow(-1, n)*math.pow(roB, n)*(1 - math.pow(betaB, n))
        SCC = s_ED - s_BC #sensitivity compensated coefficient
        if SCC < 0.001: 
            SCC = 0
        sensitivity_compensated.append(SCC)
    sensitivity_uncompensated = (1 - math.pow(betaE, N))
    sensitivity_uncomp_minus = (1 - math.pow(betaE, N-1))
    
    return sensitivity_compensated, sensitivity_uncompensated, sensitivity_uncomp_minus

def sextupole_coefficient(r: float, h: float) -> tuple:
    '''
    Функция вычисляет чувствительность катушки с секступольной компенсацией и заданными параметрами r, h. 
    При этом дополнительно задается тип 
    sensitivity_uncompensated - некомпенсированная чувствительность
    sensitivity_compensated - компенсированная чувствительность
    r = 1.915 
    h = 2.1 #старая катушка 30 мм

    r = 1.45
    h = 1.4 #новая узкая катушка 24 мм
    '''
    ic('Calculating sextupole bucking coefficient...')
    N = 3
    depth = 16
    r4 = r
    r5 = r + h
    r2 = r + h
    r1 = 2*r + r2
    r6 = r5 + 2*r
    r7 = r6 + h
    r8 = r7 + 2*r

    betaE = r7/r8
    betaD = r5/r6
    betaB = r1/r2
    roB = r2/r8
    roC = r4/r8
    roD = r6/r8
    muC = 3
    muD = 3
    muB = 1
        
    sensitivity_compensated = []
    
    for n in range (1, depth+1):
        s_ED = 1 - math.pow(betaE, n) - muD*math.pow(roD, n)*(1 - math.pow(betaD, n))
        s_BC = muC*math.pow(roC, n)*(1 - math.pow(-1, n)) - math.pow(-1, n)*math.pow(roB, n)*(1 - math.pow(betaB, n))
        SCC = s_ED + s_BC
        if SCC < 0.001: 
            SCC = 0
        sensitivity_compensated.append(SCC)
        
    sensitivity_uncompensated = (1 - math.pow(betaE, N))
    sensitivity_uncomp_minus = (1 - math.pow(betaE, N-1))

    return sensitivity_compensated, sensitivity_uncompensated, sensitivity_uncomp_minus

def octupole_coefficient(r: float, h: float, Nw: int, R0: float) -> tuple:
    ic('Calculating octupole bucking coefficient...')
    N = 4
    Leff = 0.2
    r1 = 0
    r2 = 2*r
    r3 = 2*r + h
    r4 = 4*r + h
    r5 = 2*(2*r + h)
    r6 = 2*(3*r + h)
    r7 = 3*(2*r + h)
    r8 = 8*r + 3*h
    betaD = r6/r5
    delta_y1b = 2*r + h
    delta_y1d = delta_y1b
    delta_y1c = 0
    z_u1 = complex(0, delta_y1b)
    z_u2 = complex(r2, delta_y1b)
    z_d1 = complex(0, -delta_y1b)
    z_d2 = complex(r2, -delta_y1b)
    z_u3 = complex(r3, delta_y1c)
    z_u4 = complex(r4, delta_y1c)
    z_d3 = complex(r3, -delta_y1c)
    z_d4 = complex(r4, -delta_y1c)
    z_u5 = complex(r5, delta_y1d)
    z_u6 = complex(r6, delta_y1d)
    z_d5 = complex(r5, -delta_y1d)
    z_d6 = complex(r6, -delta_y1d)
    sensitivity_compensated = []
    Leff_Nw = Leff*Nw    

    for n in range(1, 21):
        coef = Leff_Nw/(n*pow(R0, n-1))
        slag_1 = -1*((pow(z_u2, n) - pow(z_u1, n)) + (pow(z_d2, n) - pow(z_d1, n)))
        slag_2 = 2*((pow(z_u4, n) - pow(z_u3, n)) + (pow(z_d4, n) - pow(z_d3, n)))
        slag_3 = -1*((pow(z_u6, n) - pow(z_u5, n)) + (pow(z_d6, n) - pow(z_d5, n)))
        SCC = (coef*(slag_1 + slag_2 + slag_3)).real
        if (SCC > -0.000001) & (SCC < 0):
            SCC = 0 
        sensitivity_compensated.append(SCC)
    
   
    sensitivity_uncompensated = (2*Leff_Nw*(pow(r4, N) - pow(r3, N))/(N*pow(R0, N-1))).real
    sensitivity_uncomp_minus = (2*Leff_Nw*(pow(r4, N-1) - pow(r3, N-1))/((N-1)*pow(R0, N-2))).real
    
    return sensitivity_compensated, sensitivity_uncompensated, sensitivity_uncomp_minus

def harmonic_calculation(integral_compensated_value, integral_uncompensated_value, sensitivity_compensated, sensitivity_uncompensated, outer_coil_radius, N, sensitivity_uncomp_minus, quant, aperture_radius, magnet_length, coil_count):
    dx = math.pi/(quant*180)
    depth = 16  # Хорошее имя переменной, но можно лучше
       
    p = []
    q = []
    alpha = []
    start = 0 #начальный угол
    end = 360
    period = np.arange(start+1/quant, end+1/quant, 1/quant)
    mu0 = 4*math.pi*math.pow(10, -7)
    
    ic(len(period))

    for n in range (1, depth+1):
        f_cos = []
        f_sin = []
        sumC = 0
        sumS = 0
                       
        for count, teta in enumerate(period):
        #подынтегральные выражения для расчета коэффициентов разложения в ряд Фурье
            f_cos.append(integral_compensated_value[count]*math.cos(n*teta*math.pi/180))
            f_sin.append(integral_compensated_value[count]*math.sin(n*teta*math.pi/180))
    
        sumC = sum(f_cos)
        sumS = sum(f_sin)
        
        p.append((1/math.pi)*sumC*dx)
        q.append((1/math.pi)*sumS*dx)
    ic(len(p))
    ic(len(q))       
        
    P = []	
    Q = []
              
    for n in range(1, N+1):
        F_cos = []
        F_sin = []
    
        sum_C = 0
        sum_S = 0
        for count, teta in enumerate(period):
        #подынтегральные выражения для расчета коэффициентов разложения в ряд Фурье
            F_cos.append(integral_uncompensated_value[count]*math.cos(n*(teta)*math.pi/180))
            F_sin.append(integral_uncompensated_value[count]*math.sin(n*(teta)*math.pi/180))#
    
        sum_C = sum(F_cos)
        sum_S = sum(F_sin)
        
        P.append((1/math.pi)*sum_C*dx)
        Q.append((1/math.pi)*sum_S*dx)

    ic(len(F_cos))    
    
    ic(len(P))
    psy_angle = -math.atan(Q[-1] / P[-1])
    source_rotation_angle_a = psy_angle * N # Угол поворота источника поля альфа
    G_Nminus_up = ((N-1)*N*math.sqrt(math.pow(P[-1], 2) + math.pow(Q[-1], 2))) #числитель дроби
    G_Nminus_down = (magnet_length*coil_count*math.pow(outer_coil_radius, N)*sensitivity_uncompensated) #знаменатель дроби
    G_Nminus = G_Nminus_up/G_Nminus_down
    Bn = G_Nminus*math.pow(aperture_radius, N-1)
    H_avg = Bn/(2*mu0)
    
    harmonics_relative_coeffs = []

    for n in range (1, depth+1):
        try:
            HRC_up = (n * sensitivity_uncompensated * math.sqrt(math.pow(p[n-1], 2) + math.pow(q[n-1], 2))) #числитель дроби
            HRC_down = (N*sensitivity_compensated[n-1] * math.sqrt(math.pow(P[-1], 2) + math.pow(Q[-1], 2))) #знаменатель дроби
            harmonics_relative_coeffs.append(HRC_up/HRC_down)
        except ZeroDivisionError:
            harmonics_relative_coeffs.append(0)
    
    # формулы разбить на части и выделить в читаемые переменные значения типа math.sqrt(math.pow(P[N-1], 2)
    deltaX = outer_coil_radius * sensitivity_uncompensated * P[-2] / (sensitivity_uncomp_minus * N * math.sqrt(math.pow(P[-1], 2) + math.pow(Q[-1], 2)))
    deltaY = outer_coil_radius * sensitivity_uncompensated * Q[-2] / (sensitivity_uncomp_minus * N * math.sqrt(math.pow(P[-1], 2) + math.pow(Q[-1], 2)))

    return harmonics_relative_coeffs, deltaX, deltaY, source_rotation_angle_a, H_avg, P, Q

def octupole_harmonic_calculation(integral_compensated_value, integral_uncompensated_value, sensitivity_compensated, sensitivity_uncompensated, outer_coil_radius, N, sensitivity_uncomp_minus, quant, aperture_radius, magnet_length, coil_count, R0):
    dx = math.pi/(quant*180)
    depth = 16  # Хорошее имя переменной, но можно лучше
    
    p = []
    q = []
    P = []	
    Q = []
    alpha = []
    start = 0 #начальный угол
    end = 360
    period = np.arange(start+1/quant, end+1/quant, 1/quant)
    mu0 = 4*math.pi*math.pow(10, -7)
    
    ic(len(period))

    for n in range (1, depth+1):
        f_cos = []
        f_sin = []
        sumC = 0
        sumS = 0
                       
        for count, teta in enumerate(period):
        #подынтегральные выражения для расчета коэффициентов разложения в ряд Фурье
            f_cos.append(integral_compensated_value[count]*math.cos(n*teta*math.pi/180))
            f_sin.append(integral_compensated_value[count]*math.sin(n*teta*math.pi/180))
    
        sumC = sum(f_cos)
        sumS = sum(f_sin)
        
        p.append((1/math.pi)*sumC*dx)
        q.append((1/math.pi)*sumS*dx)
    ic(len(p))
    ic(len(q))       
    # LBn.append(n*math.sqrt(math.pow(pee, 2) + math.pow(quu, 2))/(M*r*s))	
              
    for n in range(1, N+1):
        F_cos = []
        F_sin = []
    
        sum_C = 0
        sum_S = 0
        for count, teta in enumerate(period):
        #подынтегральные выражения для расчета коэффициентов разложения в ряд Фурье
            F_cos.append(integral_uncompensated_value[count]*math.cos(n*(teta)*math.pi/180))
            F_sin.append(integral_uncompensated_value[count]*math.sin(n*(teta)*math.pi/180))#
    
        sum_C = sum(F_cos)
        sum_S = sum(F_sin)
        
        P.append((1/math.pi)*sum_C*dx)
        Q.append((1/math.pi)*sum_S*dx)

    ic(len(F_cos))    
    # LCN.append(math.sqrt(math.pow(Pee, 2) + math.pow(Quu, 2))/(M*math.pow(r, n)*S))	
    ic(len(P))
    harmonics_relative_coeffs = []
    for n in range (1, depth+1):
        try:
            HRC_coef = pow(R0, N-n)
            HRC_up = (sensitivity_uncompensated * math.sqrt(math.pow(p[n-1], 2) + math.pow(q[n-1], 2))) #числитель дроби
            HRC_down = (sensitivity_compensated[n-1] * math.sqrt(math.pow(P[-1], 2) + math.pow(Q[-1], 2))) #знаменатель дроби
            harmonics_relative_coeffs.append(HRC_coef*HRC_up/HRC_down)
        except ZeroDivisionError:
            harmonics_relative_coeffs.append(0)
    
    psy_angle = -math.atan(Q[-1] / P[-1])
    source_rotation_angle_a = psy_angle * N # Угол поворота источника поля альфа
    Leff = 0.2 #octupole effective length
    
    #LBN = (N*math.sqrt(math.pow(P, 2) + math.pow(Q, 2))/(M*r*sensitivity_uncompensated))
    G_Nminus_up = ((N-1)*N*math.sqrt(math.pow(P[-1], 2) + math.pow(Q[-1], 2))) #числитель дроби
    G_Nminus_down = (magnet_length*coil_count*math.pow(outer_coil_radius, N)*sensitivity_uncompensated) #знаменатель дроби
    G_Nminus = G_Nminus_up/G_Nminus_down
    Bn = G_Nminus*math.pow(aperture_radius, N-1)
    H_avg = Bn/(2*mu0)
    
    
    
    #R = math.sqrt(math.pow(Pee, 2) + math.pow(Quu, 2))/math.sqrt(math.pow(p[1], 2) + math.pow(q[1], 2))

    # формулы разбить на части и выделить в читаемые переменные значения типа math.sqrt(math.pow(P[N-1], 2)
    deltaX = outer_coil_radius * sensitivity_uncompensated * P[-2] / (sensitivity_uncomp_minus * N * math.sqrt(math.pow(P[-1], 2) + math.pow(Q[-1], 2)))
    deltaY = outer_coil_radius * sensitivity_uncompensated * Q[-2] / (sensitivity_uncomp_minus * N * math.sqrt(math.pow(P[-1], 2) + math.pow(Q[-1], 2)))

    return harmonics_relative_coeffs, deltaX, deltaY, source_rotation_angle_a, H_avg, P, Q


def run_quadrupole(df, parameters):
    coil_count = 56
    quant, r, h, coef_E, coef_C = parameters[4]
    N = parameters[5]
    aperture_radius = parameters[6]
    magnet_length = parameters[7]
    magnet_type = parameters[8]
    intC = []
    intU = []
    posArray = []
    spectrum = []
    time_coef = math.pow(10, -9)
    outer_coil_radius =(5*r + 2*h) # mm
        
    integration_result = calc.integrate_dataframe(df, coef_E, coef_C, quant, time_coef)
    intC, intU = integration_result

    
    sensC, sensU, sens_minus = calc.quadrupole_coefficient(r, h) # чувствительность порядка N-1
    calculation_result = calc.harmonic_calculation(intC, intU, sensC, sensU, outer_coil_radius, N, sens_minus, quant, aperture_radius, magnet_length, coil_count)

    ic('calculation complete')
    return calculation_result
def run_sextupole(df, parameters):
    coil_count = 64
    quant = parameters[0]
    r = parameters[1]
    h = parameters[2]
    coef_E = parameters[3]
    coef_C = parameters[4]
    N = parameters[5]
    aperture_radius = parameters[6]
    magnet_length = parameters[7]
    magnet_type = parameters[8]
    intC = []
    intU = []
    posArray = []
    spectrum = []
    time_coef = math.pow(10, -9)
    outer_coil_radius =(5*r + 2*h) # mm
        
    integration_result = calc.integrate_dataframe(df, coef_E, coef_C, quant, time_coef)
    intC, intU = integration_result

    
    sensC, sensU, sens_minus = calc.sextupole_coefficient(r, h) # чувствительность порядка N-1  
    calculation_result = calc.harmonic_calculation(intC, intU, sensC, sensU, outer_coil_radius, N, sens_minus, quant, aperture_radius, magnet_length, coil_count) 

    
    ic('calculation complete')
    return (calculation_result)

def run_octupole(df, parameters):
    coil_count = 28
    R0 = 12.3
    quant = parameters[0]
    r = parameters[1]
    h = parameters[2]
    coef_E = parameters[3]
    coef_C = parameters[4]
    N = parameters[5]
    aperture_radius = parameters[6]
    magnet_length = parameters[7]
    magnet_type = parameters[8]
    intC = []
    intU = []
    posArray = []
    spectrum = []
    time_coef = math.pow(10, -9)
    outer_coil_radius =(5*r + 2*h) # mm
        
    integration_result = calc.integrate_dataframe(df, coef_E, coef_C, quant, time_coef)
    intC, intU = integration_result
    
    sensC, sensU, sens_minus = calc.octupole_coefficient(r, h, coil_count, R0)
    calculation_result = calc.octupole_harmonic_calculation(intC, intU, sensC, sensU, outer_coil_radius, N, sens_minus, quant, aperture_radius, magnet_length, coil_count, R0)
    
    ic('calculation complete')
    return calculation_result    

def run(df_name, parameters):
    N = parameters[5]
    if N == 2:
        result = calc.run_quadrupole(df_name, parameters)
    elif N == 3:
        result = calc.run_sextupole(df_name, parameters)
    elif N == 4:
        result = calc.run_octupole(df_name, parameters)
    
    return result

if __name__ == "__main__":
    '''-- Обсчёт данных с помощью модуля calc без использования праграммы управления harm --'''

    startTime = time.time()
    dirPath = pathlib.Path(__file__).parent
    result_dir = pathlib.Path('result') # каталог для сохранения результатов обработки
    filename = ["rawdata_5_2024-06-04_17-05.csv", "rawdata_5_2024-06-04_17-09.csv", "rawdata_5_2024-06-04_17-12.csv", "rawdata_5_2024-06-04_17-15.csv", "rawdata_5_2024-06-04_17-18.csv"] #сюда вводятся имена файлов, подлежащие обработке, сами файлы должнылежать в каталоге data относительно места запуска скрипта
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

        
        #coil parameters
        N = 4
        #int(input('Input N for 2n-pole magnet: '))
        
        quant = 1
            
        if N == 2:
            magnet_type = 'quadrupole'
            r = 1.915 #mm
            h = 2.1 #mm
            aperture_radius = 0.016 #mm
            coef_E = 2.56*pow(10, -5) # 1/39000
            coef_C = 1*pow(10, -5)    #1/100000
            magnet_length = 0.090   #длина магнита m
            ic(N)
            ic(magnet_type)
            param_list = [quant, r, h, coef_E, coef_C, N, aperture_radius, magnet_length, magnet_type]
            

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
            param_list = [quant, r, h, coef_E, coef_C, N, aperture_radius, magnet_length, magnet_type]
            

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

        result_name = f'result_{magnet_type}_calc2.5_{file}_{p}.txt'
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
            output.write('H_avg ' + "\n" + str('%.7f' %H_avg)+ "\n" + 'Run ID' + "\n" + str(num))
            
    ic('Job start time', time.ctime(startTime))
    ic('Job finish time', time.ctime(finalTime))