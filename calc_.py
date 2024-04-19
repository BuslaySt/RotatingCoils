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
import calc_ as calc             # Самоимпорт для совместимости кода
import time


def integrate_dataframe(df_name, coef_A, coef_C, quant) -> tuple:
    '''
    Функция вычисляет интеграл датафрейма
    roundN - порядок округления для ускорения расчетов.
    '''
    
    timestamp = df_name.timestamp 
    ch_A = coef_A*df_name.ch_a      # channel_A = ...
    ch_C = coef_C*df_name.ch_c # channel_C = ... для катушки с коэффициентом усиления 991
    #tick = df_name.D0
    zeroPulse = df_name.D4
    
    angular_step = 160/quant #160 - 1 degree, quant - fraction of a degree
    ch_A_norm = []
    compSignalR = []
   
    ic('DF has been read successfully')
    
    tick = dict([(i,d) for i,d in zip(df_name.index, df_name.D0)])
    zeroPos = []
    tickPos = []

  #  for i in tqdm(range(1, len(timestamp)), desc = 'Detecting zero pulses and ticks'):
   #     if (zeroPulse[i-1] == 0) & (zeroPulse[i] == 1):
    #        zeroPos.append(i)
     #       
      #  if (tick[i-1] == 0) & (tick[i] == 1):
       #     tickPos.append(i)   

# Итерируемся только по тем индексам, где значения целевого показателя == 1
  
    
    
    for i in tqdm(df_name[df_name.D4 == 1].index):
        if (df_name.iloc[i-1].D4 == 0) & (df_name.iloc[i].D4 == 1):
            zeroPos.append(i)
# Во втором условии применение функции iloc только замедляет, для этого сделали отдельный словарь для tick
    
    #for j in (df_name[df_name.D0 == 1].index):
    #    if (tick[j-1] == 0) & (tick[j] == 1):
    #        tickPos.append(j)
    
    for j in (df_name[df_name.D0 == 1].index):
        if j > zeroPos[0]:
            if (tick[j-1] == 0) & (tick[j] == 1):
                tickPos.append(j)
    p = time.strftime("%H_%M_%d_%m_%y")
    with open(f'zeroPos_{p}.txt', 'w') as output:
        output.write(str(p)  + '\n' + str(zeroPos) + '\n')
        output.write(str(tickPos))

    ic('Zero pulses located and written to file')
    ic('Period count is', len(zeroPos))
    ic(zeroPos)    
    periods = range(4, len(zeroPos)-3)
    if len(periods)<2:
        return
    allPeriodC = []
    allPeriodUc = []
    
    #вычисление постоянной составляющей
    #TODO переработать устранение постоянной составляющей
    summU = 0
    summC = 0        
    #? comment here for bypass minus const
    for k in range(zeroPos[0], (zeroPos[-1]+1)):
        summU += ch_A[k]
        summC += ch_C[k]
    
    constantComp = summC/ ((zeroPos[-1]+1)-zeroPos[0]) 
    constantUncomp = summU/ ((zeroPos[-1]+1)-zeroPos[0])
    
    for i in tqdm(range(zeroPos[0], (zeroPos[-1]+1)), desc = 'Averaging signals'):
        ch_A_norm.append(ch_A[i] - constantUncomp)
        compSignalR.append(ch_C[i] - constantComp)
    ic(len(ch_A_norm))
    ic(len(tickPos))
    ic('periods, total', periods)
    posArr = []

    # Интегрирование по каждому периоду отдельно
    # TODO Stepan: лучше выделить в отдельную функцию
    for p in periods:
        ic('Integral calculation for period', p)
        dx = math.pow(10, -9) * (timestamp[zeroPos[p]+1] - timestamp[zeroPos[p]]) #перевод отметок времени из нс в с 
        #dx = abs(timestamp[zeroPos[p]+1] - timestamp[zeroPos[p]])
        
        intC = []
        intU = []
        counter = 0
        start = zeroPos[p]
        finish = zeroPos[p+1]
        
        
        #поиск границ отдельных периодов для вычисления интеграла по ним
        for i in range(len(tickPos)):
            if ((tickPos[i] - start) < 18) & ((tickPos[i] - start) >= 0):
                startPos = i
                ic(start)
                ic(tickPos[startPos])
                
            if ((finish - tickPos[i]) < 18) & ((finish - tickPos[i]) >= 0):
                finishPos = i
                ic(finish)
                ic(tickPos[finishPos])


        for pos in tickPos[startPos:finishPos+1]:
            
            sumC = 0 # суммы для вычисления интеграла методом трапеций
            sumU = 0
            counter +=1
            if counter == angular_step:
                curr_pos = pos 
                
                for int_counter in range(start, curr_pos+1):
                    
                    sumC += compSignalR[int_counter]
                    sumU += ch_A_norm[int_counter]
                #ic(range(start, curr_pos+1))
                # 160 - 1 градус при разрешении 57600
                intC.append(sumC*dx)
                intU.append(sumU*dx)
                counter = 0
                if curr_pos > finish:
                    break
        
        ic(len(intC))
        ic(len(intU))
        allPeriodC.append(intC)
        allPeriodUc.append(intU)
        
    avgIntC = calc.integral_averaging(allPeriodC)
    avgIntUc = calc.integral_averaging(allPeriodUc)
       
    return (avgIntC, avgIntUc) # Stepan: после служебной команды return надо ставить пробел,
                               # чтобы не путать по синтаксису с вызовом функции.
                               # Здесь в круглых скобках - не аргументы, а кортеж (tuple)

def integral_averaging (allPeriod) -> tuple:
  
   #вычисление усредненного значения интегралов по нескольким периодам через транспонирование двухмерного списка			
   #summaM = sum(compSignal[n] for n in range (zeroPos[3], zeroPos[4]))
    
    avgInt = []
    arrInt = np.asarray(allPeriod)
    aarrIntTransp = arrInt.transpose()
    
    for item in aarrIntTransp:
        avgInt.append(sum(item)/len(arrInt))
   
    return (avgInt)

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
    
    return (sensitivity_compensated, sensitivity_uncompensated, sensitivity_uncomp_minus)

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

    for n in range (4, depth+1):
        s_ED = 1 - math.pow(betaE, n) - muD*math.pow(roD, n)*(1 - math.pow(betaD, n))
        s_BC = muC*math.pow(roC, n)*(1 - math.pow(-1, n)) - math.pow(-1, n)*math.pow(roB, n)*(1 - math.pow(betaB, n))
        sensitivity_compensated.append(s_ED + s_BC)
        
    sensitivity_uncompensated = (1 - math.pow(betaE, N))
    sensitivity_uncomp_minus = (1 - math.pow(betaE, N-1))

    return (sensitivity_compensated, sensitivity_uncompensated, sensitivity_uncomp_minus)
        
def harmonic_calculation(integral_compensated_value, integral_uncompensated_value, sensitivity_compensated, sensitivity_uncompensated, R, N, sensitivity_uncomp_minus, quant):
    dx = math.pi/(quant*180)
    M = 56
    depth = 16  # Хорошее имя переменной, но можно лучше
    LCn = []    # Плохое имя переменной
    psi = []
    p = []
    q = []
    alpha = []
    start = 0 #начальный угол
    end = 360
    period = np.arange(start, end, 1/quant)
    ic(len(period))

    for n in range (3, depth+1):
        f_cos = []
        f_sin = []
        sumC = 0
        sumS = 0
        pee = 0
        quu = 0
        #компенсированная чувствительность
                
        for teta in range(len(period)):
        #подынтегральные выражения для расчета коэффициентов разложения в ряд Фурье
            f_cos.append(integral_compensated_value[teta]*math.cos(n*(teta/quant)*math.pi/180))
            f_sin.append(integral_compensated_value[teta]*math.sin(n*(teta/quant)*math.pi/180))#
    
        
        for s in range(len(period)):
            sumC += f_cos[s]
            sumS += f_sin[s]
        
        pee = (1/math.pi)*sumC*dx
        quu = (1/math.pi)*sumS*dx
            
        # LCn.append(math.sqrt(math.pow(pee, 2) + math.pow(quu, 2))/(M*math.pow(r, n)*s))	
        #psi = -math.atan(quu/pee)
        #alpha.append(psi/n)
        p.append(pee)
        q.append(quu)
    ic(len(p))
    ic(len(f_cos))       
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
        for teta in range(len(period)):
        #подынтегральные выражения для расчета коэффициентов разложения в ряд Фурье
            F_cos.append(integral_uncompensated_value[teta]*math.cos(n*(teta/quant)*math.pi/180))
            F_sin.append(integral_uncompensated_value[teta]*math.sin(n*(teta/quant)*math.pi/180))#
    
                
        for s in range(len(period)):
            sum_C += F_cos[s]
            sum_S += F_sin[s]
        
        P.append((1/math.pi)*sum_C*dx)
        Q.append((1/math.pi)*sum_S*dx)
    ic(len(F_cos))    
    # LCN.append(math.sqrt(math.pow(Pee, 2) + math.pow(Quu, 2))/(M*math.pow(r, n)*S))	
    ic(len(P))
    psy_angle = (-math.atan(Q[N-1] / P[N-1]))
    source_rotation_angle_a = psy_angle * N # Угол поворота источника поля альфа
    # P.append(Pee)
    # Q.append(Quu)
    #LBN = (N*math.sqrt(math.pow(P, 2) + math.pow(Q, 2))/(M*r*sensitivity_uncompensated))

    harmonics_relative_coeffs = []
    
    #R = math.sqrt(math.pow(Pee, 2) + math.pow(Quu, 2))/math.sqrt(math.pow(p[1], 2) + math.pow(q[1], 2))

    # формулы разбить на части и выделить в читаемые переменные значения типа math.sqrt(math.pow(P[N-1], 2)
    for n in range (3, 17):
        harmonics_relative_coeffs.append((n * sensitivity_uncompensated * math.sqrt(math.pow(p[n-3], 2) + math.pow(q[n-3], 2))) / (N*sensitivity_compensated[n-3] * math.sqrt(math.pow(P[N-1], 2) + math.pow(Q[N-1], 2))))
        #ic(harmonics_relative_coeffs[n-3])
    # формулы разбить на части и выделить в читаемые переменные значения типа math.sqrt(math.pow(P[N-1], 2)
    deltaX = R * sensitivity_uncompensated * P[N-2] / (sensitivity_uncomp_minus * N * math.sqrt(math.pow(P[N-1], 2) + math.pow(Q[N-1], 2)))
    deltaY = R * sensitivity_uncompensated * Q[N-2] / (sensitivity_uncomp_minus * N * math.sqrt(math.pow(P[N-1], 2) + math.pow(Q[N-1], 2)))

    return (harmonics_relative_coeffs, deltaX, deltaY, source_rotation_angle_a)


if __name__ == "__main__":
    '''
    Стартовый код, в котором показан порядок вызова модуля calc, не стоит пока удалять
    '''
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