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
import __main__ as calc  # Самоимпорт для совместимости кода
import time


def integrate_dataframe(df_name, coef_E, coef_C, quant, time_coef) -> tuple:
    '''
    Функция вычисляет интеграл датафрейма
    roundN - порядок округления для ускорения расчетов.
    '''
    
    timestamp = df_name.timestamp 
    ch_E = -1*df_name.ch_a      
    ch_C = df_name.ch_c 
    zeroPulse = df_name.D4
    
    angular_step = 160/quant #160 - 1 degree, quant - fraction of a degree
    ch_E_norm = []
    compSignalR = []
   
    ic('DF has been read successfully')
    
    zeroPos = []#list of encoder zero positions
   
    # Итерируемся только по тем индексам, где значения целевого показателя == 1
      
    for i in tqdm(df_name[df_name.D4 == 1].index):
        if (df_name.iloc[i-1].D4 == 0) & (df_name.iloc[i].D4 == 1):
            zeroPos.append(i)

    ic('Period count is', len(zeroPos))
    ic(zeroPos)    
    periods = range(1, len(zeroPos)-3)
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
    # TODO Stepan: лучше выделить в отдельную функцию
    for p in periods:
        
        tickPos = []
        df_work = df_name[zeroPos[p]:zeroPos[p+1]].reset_index(drop = True)
        ic(df_work.head(n = 10))
        tick = dict([(i,d) for i,d in zip(df_work.index, df_work.D0)])
        for j in (df_work[df_work.D0 == 1].index):
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
       
    return (avgIntC, avgIntUc) # Stepan: после служебной команды return надо ставить пробел,
                               # чтобы не путать по синтаксису с вызовом функции.
                               # Здесь в круглых скобках - не аргументы, а кортеж (tuple)

def integral_averaging (allPeriod) -> list:
  
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

    for n in range (1, depth+1):
        s_ED = 1 - math.pow(betaE, n) - muD*math.pow(roD, n)*(1 - math.pow(betaD, n))
        s_BC = muC*math.pow(roC, n)*(1 - math.pow(-1, n)) - math.pow(-1, n)*math.pow(roB, n)*(1 - math.pow(betaB, n))
        sensitivity_compensated.append(s_ED + s_BC)
        
    sensitivity_uncompensated = (1 - math.pow(betaE, N))
    sensitivity_uncomp_minus = (1 - math.pow(betaE, N-1))

    return (sensitivity_compensated, sensitivity_uncompensated, sensitivity_uncomp_minus)

#def octupole_coefficient():


def harmonic_calculation(integral_compensated_value, integral_uncompensated_value, sensitivity_compensated, sensitivity_uncompensated, R, N, sensitivity_uncomp_minus, quant, aperture_radius, magnet_length):
    dx = math.pi/(quant*180)# шаг в градусах
    M = 56
    depth = 16  # Хорошее имя переменной, но можно лучше
    LCn = []    # Плохое имя переменной
    psi = []
    
    p = []
    q = []
    alpha = []
    start = 1 #начальный угол
    end = 360
    period = np.arange(start, end+1, 1/quant)
    mu0 = 4*math.pi*math.pow(10, -7)
    
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
    G_Nminus = ((N-1)*N*math.sqrt(math.pow(P[N-1], 2) + math.pow(Q[N-1], 2)))/(magnet_length*M*math.pow(R, N)*sensitivity_uncompensated)
    ic(G_Nminus)
    Bn = G_Nminus*math.pow(aperture_radius, N-1)
    ic(Bn)
    H_avg = Bn/(2*mu0)
    
    harmonics_relative_coeffs = []
    
    #R = math.sqrt(math.pow(Pee, 2) + math.pow(Quu, 2))/math.sqrt(math.pow(p[1], 2) + math.pow(q[1], 2))

    # формулы разбить на части и выделить в читаемые переменные значения типа math.sqrt(math.pow(P[N-1], 2)
    for n in range (3, 17):
        harmonics_relative_coeffs.append((n * sensitivity_uncompensated * math.sqrt(math.pow(p[n-3], 2) + math.pow(q[n-3], 2))) / (N*sensitivity_compensated[n-3] * math.sqrt(math.pow(P[N-1], 2) + math.pow(Q[N-1], 2))))
        #ic(harmonics_relative_coeffs[n-3])
    # формулы разбить на части и выделить в читаемые переменные значения типа math.sqrt(math.pow(P[N-1], 2)
    deltaX = R * sensitivity_uncompensated * P[N-2] / (sensitivity_uncomp_minus * N * math.sqrt(math.pow(P[N-1], 2) + math.pow(Q[N-1], 2)))
    deltaY = R * sensitivity_uncompensated * Q[N-2] / (sensitivity_uncomp_minus * N * math.sqrt(math.pow(P[N-1], 2) + math.pow(Q[N-1], 2)))

    return (harmonics_relative_coeffs, deltaX, deltaY, source_rotation_angle_a, H_avg)


if __name__ == "__main__":
    '''
    Стартовый код, в котором показан порядок вызова модуля calc, не стоит пока удалять
    '''
    print("Reading data...")
    df = pd.read_csv('data1.csv', delimiter=',') # Импорт данных для отладки модуля
    
    quant = 1 #указание шага интегрирования (доли градуса)
    time_coef = math.pow(10, -9) #перевод в секунды
    coef_E = 0.000025641 # параметры усиления катушки, передаются исходя из выбранного типа катушки (таблицу с данными пришлю отдельно). 
    coef_C = 0.000001009 # указанные коэффициенты - для квадрупольной катушки макетной шириной 30мм

    # integral_compensated_value, integral_uncompensated_value = calc.integrate_dataframe(df)
    result = calc.integrate_dataframe(df, coef_E, coef_C, quant, time_coef)

    # r24mm = 1.45  #24mm coil
    # h24mm = 1.4
    # r30mm = 1.915 #30mm coil
    # h30mm = 2.1

    r = 1.915 # параметры катушки в мм
    h = 2.1 # параметры катушки в мм
    N = 2 # половинное количество полюсов магнита, 2 для квадруполя, 3 для секступоля и т.д.
    magnet_length = 0.09 #длина магнита в м

    R_A =(5*r + 2*h)/1000 #радиус внешней катушки в м
    aperture_radius = 0.016 #радиус апертуры магнита (сейчас для квадруполя), тоже надо получать при инициализации из выбранного типа магнита, в м

    comp, uncomp = result
    sens30, Sens, sens_m = calc.quadrupole_coefficient(r, h)
    # ФУНКЦИЯ ВЫЧИСЛЕНИЯ ВЕЛИЧИН
    final_res = calc.harmonic_calculation(comp, uncomp, sens30, Sens, R_A, N, sens_m, quant, aperture_radius, magnet_length)
    spectrum, deltaX, deltaY, alpha, H_avg = final_res

    ic(spectrum, deltaX, deltaY, alpha, H_avg)