# программа принимает на вход массив данных df,
# находит нулевые импульсы и отдельные угловые импульсы 
# проводит интегрирование по одному периоду и далее усреднение по нескольким периодам
# вариант для использования в качестве модуля
# применяется округление до 6 знаков

import pandas as pd
import numpy as np
import math
from tqdm import tqdm   # Progress bar
from icecream import ic # Debug print
import calc_v3 as calc             # Самоимпорт для совместимости кода
import time
import pathlib
import os
from datetime import date

#16 may 2024 version 3.0

def integrate_dataframe(df_name: pd.DataFrame, coef_E: float, coef_C: float, quant: float, time_coef: float) -> tuple:
    '''
    Функция вычисляет интеграл датафрейма
    roundN - порядок округления для ускорения расчетов.
    '''
    
    timestamp = df_name.timestamp 
    ch_E = -1*df_name.ch_a      
    ch_C = df_name.ch_c 
    zeroPulse = df_name.D0
    
    angular_step = 160/quant #160 - 1 degree, quant - fraction of a degree
    ch_E_norm = []
    compSignalR = []
   
    ic('DF has been read successfully')
    
    zeroPos = []#list of encoder zero positions
   
    # Итерируемся только по тем индексам, где значения целевого показателя == 1
      
    for i in tqdm(df_name[df_name.D0 == 1].index):
        if (df_name.iloc[i-1].D0 == 0) & (df_name.iloc[i].D0 == 1):
            zeroPos.append(i)
   
    start_period = 3
    end_period = len(zeroPos)-3

    ic('Period count is', len(zeroPos))
    ic(zeroPos)    
    periods = range(start_period, end_period)
    if len(periods)<2:
        return
    allPeriodC = []
    allPeriodUc = []
    
    #const elimination
    #TODO переработать устранение постоянной составляющей
    summU = 0
    summC = 0        
    
    for k in range(zeroPos[0], (zeroPos[-1]+1)):
        summU += ch_E[k]
        summC += ch_C[k]
    
    constantComp = summC/ ((zeroPos[-1]+1)-zeroPos[0]) 
    constantUncomp = summU/ ((zeroPos[-1]+1)-zeroPos[0])
    
    for i in tqdm(range(zeroPos[0], (zeroPos[-1]+1)), desc = 'Averaging signals'):
        ch_E_norm.append(ch_E[i] - constantUncomp)
        compSignalR.append(ch_C[i] - constantComp)
    ic(len(ch_E_norm))
    
    ic('periods, total', periods)

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
        intU = []
        counter = 0
        start = zeroPos[p]
        finish = zeroPos[p+1]
        period = finish - start
        
        
        #поиск границ отдельных периодов для вычисления интеграла по ним
        for i in range(len(tickPos)):
            if (tickPos[i] <= delta):
                startPos = i
                ic(tickPos[startPos])
                
            if ((period - tickPos[i]) <= delta) & ((period - tickPos[i]) >= 0):
                finishPos = i
                ic(period)
                ic(tickPos[finishPos])

        sumC = 0
        sumU = 0
        for pos in tickPos[startPos:finishPos+1]:
            
            counter +=1
            if counter == angular_step:
                curr_pos = pos 
                
                for int_counter in range(curr_pos+1):
                    
                    sumC += compSignalR[int_counter]
                    sumU += ch_E_norm[int_counter]
                    
                intC.append(coef_C*sumC*dx)
                intU.append(coef_E*sumU*dx)
                counter = 0
                
                if curr_pos > finish:
                    break
        
        ic(len(intC))
        ic(len(intU))
        allPeriodC.append(intC)
        allPeriodUc.append(intU)
   
    avgIntC = calc.integral_averaging(allPeriodC)
    avgIntUc = calc.integral_averaging(allPeriodUc)
       
    return avgIntC, avgIntUc

def integral_averaging (allPeriod: list) -> tuple:
  
   #вычисление усредненного значения интегралов по нескольким периодам через транспонирование двухмерного списка			
     
    avgInt = []
    arrInt = np.asarray(allPeriod)
    aarrIntTransp = arrInt.transpose()
    
    for item in aarrIntTransp:
        avgInt.append(sum(item)/len(arrInt))
   
    return avgInt

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
    
    N = 2
    sensitivity_compensated = []
    
    for n in range (3, depth+1):
        s_ED = 1 - math.pow(betaE, n) - math.pow(roD, n)*(1 - math.pow(betaD, n))
        s_BC = math.pow(roC, n)*(1 - math.pow(-1, n)) - math.pow(-1, n)*math.pow(roB, n)*(1 - math.pow(betaB, n))
        sensitivity_compensated.append(s_ED - s_BC)
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
    N = 3
    
    sensitivity_compensated = []
    sensitivity_uncompensated = 0

    for n in range (1, depth+1):
        s_ED = 1 - math.pow(betaE, n) - muD*math.pow(roD, n)*(1 - math.pow(betaD, n))
        s_BC = muC*math.pow(roC, n)*(1 - math.pow(-1, n)) - math.pow(-1, n)*math.pow(roB, n)*(1 - math.pow(betaB, n))
        sensitivity_compensated.append(s_ED + s_BC)
        
    sensitivity_uncompensated = (1 - math.pow(betaE, N))
    sensitivity_uncomp_minus = (1 - math.pow(betaE, N-1))

    return sensitivity_compensated, sensitivity_uncompensated, sensitivity_uncomp_minus

def octupole_coefficient(r: float, h: float) -> tuple:
    r1 = 0
    r2 = 2*r
    r3 = 2*r + h
    r4 = 4*r + h
    r5 = 2*(2*r + h)
    r6 = 2*(3*r + h)
    r7 = 3*(2*r + h)
    r8 = 8*r + 3*h
    N = 4
    betaD = r6/r5
    R0 = 0.0123
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
    Leff_Nw = 11.2 # Leff*Nw    

    for n in range(1, 21):
        coef = Leff_Nw/(n*pow(R0, n-1))
        slag_1 = -1*((pow(z_u2, n) - pow(z_u1, n)) + (pow(z_d2, n) - pow(z_d1, n)))
        slag_2 = 2*((pow(z_u4, n) - pow(z_u3, n)) + (pow(z_d4, n) - pow(z_d3, n)))
        slag_3 = -1*((pow(z_u6, n) - pow(z_u5, n)) + (pow(z_d6, n) - pow(z_d5, n)))
        sensitivity_compensated.append(coef*(slag_1 + slag_2 + slag_3))
    
    sensitivity_uncompensated = (1 - math.pow(betaD, N))

    return sensitivity_compensated, sensitivity_uncompensated
    
def harmonic_calculation(integral_compensated_value: list, integral_uncompensated_value: list, sensitivity_compensated, sensitivity_uncompensated,
                         outer_coil_radius: int, N: int, sensitivity_uncomp_minus, quant: float, aperture_radius: float, magnet_length: float) -> tuple:
    dx = math.pi/(quant*180)# шаг в градусах
    M = 56
    depth = 16  # Хорошее имя переменной, но можно лучше
    LCn = []    # Плохое имя переменной
    psi = []
    
    p = []
    q = []

    alpha = []
    start = 0 #начальный угол
    end = 360
    period = np.arange(start+1/quant, end+1/quant, 1/quant)
    mu0 = 4*math.pi*math.pow(10, -7)
    
    ic(len(period))

    for n in range (3, depth+1):
        f_cos = []
        f_sin = []
        sumC = 0
        sumS = 0
       
        #компенсированная чувствительность
        for count, teta in enumerate(period):
        #подынтегральные выражения для расчета коэффициентов разложения в ряд Фурье
            f_cos.append(integral_compensated_value[count]*math.cos(n*teta*math.pi/180))
            f_sin.append(integral_compensated_value[count]*math.sin(n*teta*math.pi/180))
    
        sumC = sum(f_cos)
        sumS = sum(f_sin)
        
        p.append((1/math.pi)*sumC*dx)
        q.append((1/math.pi)*sumS*dx)

    ic(p)
    ic(q)
  

    # LBn.append(n*math.sqrt(math.pow(pee, 2) + math.pow(quu, 2))/(M*r*s))	
    
    LCN = []
    
    P = []	
    Q = []
    
    # LBN = []
    
       
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
   
    # LCN.append(math.sqrt(math.pow(Pee, 2) + math.pow(Quu, 2))/(M*math.pow(r, n)*S))	
    ic(P)
    ic(Q)

    psy_angle = (-math.atan(Q[N-1] / P[N-1]))
    source_rotation_angle_a = psy_angle * N # Угол поворота источника поля альфа
    
    #LBN = (N*math.sqrt(math.pow(P, 2) + math.pow(Q, 2))/(M*r*sensitivity_uncompensated))
    G_Nminus = ((N-1)*N*math.sqrt(math.pow(P[-1], 2) + math.pow(Q[-1], 2)))/(magnet_length*M*math.pow(outer_coil_radius, N)*sensitivity_uncompensated)
    ic(G_Nminus)
    Bn = G_Nminus*math.pow(aperture_radius, N-1)
    ic(Bn)
    H_avg = Bn/(2*mu0)
    
    harmonics_relative_coeffs = []
    
    #R = math.sqrt(math.pow(Pee, 2) + math.pow(Quu, 2))/math.sqrt(math.pow(p[1], 2) + math.pow(q[1], 2))
    ic(sensitivity_compensated)
    # формулы разбить на части и выделить в читаемые переменные значения типа math.sqrt(math.pow(P[N-1], 2)
    for n in range (3, 17):
        ic(sensitivity_compensated[n-3])
        harmonics_relative_coeffs.append((n * sensitivity_uncompensated * math.sqrt(math.pow(p[n-3], 2) + math.pow(q[n-3], 2))) / (N*sensitivity_compensated[n-3] * math.sqrt(math.pow(P[-1], 2) + math.pow(Q[-1], 2))))

    # формулы разбить на части и выделить в читаемые переменные значения типа math.sqrt(math.pow(P[N-1], 2)
    deltaX = outer_coil_radius * sensitivity_uncompensated * P[-2] / (sensitivity_uncomp_minus * N * math.sqrt(math.pow(P[-1], 2) + math.pow(Q[-1], 2)))
    deltaY = outer_coil_radius * sensitivity_uncompensated * Q[-2] / (sensitivity_uncomp_minus * N * math.sqrt(math.pow(P[-1], 2) + math.pow(Q[-1], 2)))
    
    ic(harmonics_relative_coeffs, deltaX, deltaY, source_rotation_angle_a, H_avg, P, Q)
    return harmonics_relative_coeffs, deltaX, deltaY, source_rotation_angle_a, H_avg, P, Q

def run(df: pd.DataFrame, parameters: list) -> list:
    
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
    outer_coil_radius = (5*r + 2*h) # mm


    # df = pd.read_csv(df_name, sep = ',', low_memory = False)
   
    df['timestamp'] = pd.to_numeric(df['timestamp'], errors = 'coerce')
    df['ch_a'] = pd.to_numeric(df['ch_a'], errors = 'coerce') 
    df['ch_c'] = pd.to_numeric(df['ch_c'], errors = 'coerce')
    ic('reading DF complete')

    ic('calculating final res')
    integration_result = calc.integrate_dataframe(df, coef_E, coef_C, quant, time_coef)
    sensC = calc.quadrupole_coefficient(r, h)[0] #компенсированная чувствительность
    sens_minus = calc.quadrupole_coefficient(r, h)[2]
    sensU = calc.quadrupole_coefficient(r, h)[1] #некомпенсированная чувствительность
    intC, intU = integration_result
    calculation_result = calc.harmonic_calculation(intC, intU, sensC, sensU, outer_coil_radius, N, sens_minus, quant, aperture_radius, magnet_length)
    ic('calculation complete')
    
    return calculation_result


if __name__ == "__main__":
    startTime = time.time()
    dirPath = pathlib.Path(__file__).parent
    result_dir = pathlib.Path('result')
    filename = ["rawdata_2024-05-14_13-08.csv", "rawdata_2024-05-14_13-13.csv"]
    data_dir = pathlib.Path('data')
        

    for file in filename:
        
        spectrum = []
        deltaX = []
        deltaY = []
        P = []
        Q = []

        csvLoc = os.path.join(dirPath, data_dir, file)
        #coil parameters
        N = 2
        r = 1.915
        h = 2.1
        aperture_radius = 0.016
        quant = 1
        coef_E = 2.56*pow(10, -5) # 1/39000
        coef_C = 1*pow(10, -5)    #1/100000
        magnet_length = 0.09   #длина магнита
        magnet_type = 'quadrupole'

        param_list = [quant, r, h, coef_E, coef_C, N, aperture_radius, magnet_length, magnet_type]

        calc_result = calc.run(csvLoc, param_list)
        spectrum, deltaX, deltaY, alpha, H_avg, P, Q = calc_result # P, Q - временные коэффициенты, потом уберутся

        finalTime = time.time()
        d = date.today()
        frmt = d.strftime("%d_%m_%y")
        p = time.strftime("%H_%M_%d_%m_%y")

        result_name = f'result_{file}_{p}.txt'
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
            output.write('H_avg ' + "\n" + str('%.7f' %H_avg)+ "\n")
            
    ic('Job start time', time.ctime(startTime))
    ic('Job finish time', time.ctime(finalTime))
    
    
    
    '''
    Старый код, в котором показан порядок вызова модуля calc, можно удалять

    # print("Reading data...")
    # df = pd.read_csv('data.csv', delimiter=',') # Импорт данных для отладки модуля

    r24mm = 1.45  #24mm coil
    h24mm = 1.4
    r30mm = 1.915 #30mm coil
    h30mm = 2.1
    r24mm_coilA = 5*r24mm + 2*h24mm #radius for A coil in 24mm PCB
    r30mm_coilA = 5*r30mm + 2*h30mm #radius for A coil in 30mm PCB
    N = 2         #for quadrupole

    integral_compensated_value, integral_uncompensated_value = calc.integrate_dataframe(df)

    sensitivity_compensated, sensitivity_uncompensated, sensitivity_uncomp_minus = calc.quadrupole_coefficient(r30mm, h30mm) 

    final_result = calc.harmonic_calculation(integral_compensated_value, integral_uncompensated_value, sensitivity_compensated, sensitivity_uncompensated, r30mm_coilA, N, sensitivity_uncomp_minus)
    
    # Генерация данных по осям графика
    axis_y_harmonics_relative = final_result[0]
    axis_x_harmonic_number = [n for n in range(3, (len(axis_y_harmonics_relative)+3))]

    # Вписать график в окно программы
    sc = MplCanvas(width=5, height=4, dpi=100)
    sc.axes.plot(axis_x_harmonic_number, axis_y_harmonics_relative)
    harm.ui.hLayout_Graph.addWidget(sc)

    # Вывод данных в текстовое поле txt_Result
    harm.ui.txt_Result.setText('Результат вычислений: \n'+str(final_result[0], '\n', str(final_result[1:])))
    '''