from icecream import ic
import math
from tqdm import tqdm
import numpy as np

def quadrupole_coefficient(r: float, h: float) -> tuple:
    """
    Функция вычисляет коэффициенты чувствительности квадрупольной катушки. В качестве входных данных принимаются параметры катушки.
    
    ------------------------------------------------------------------------------------
    Переменные

        r : float
            Параметр катушки, ширина 
        h : float
            Параметр катушки, расстояние между центрами соседних катушек в плате
       
   
    """
    ic('вычисляются коэффициенты чувствительности для квадрупольной катушки...')
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
    """
    Функция вычисляет коэффициенты чувствительности квадрупольной катушки. В качестве входных данных принимаются параметры катушки.
    
    ------------------------------------------------------------------------------------
    Переменные

        r : float
            Параметр катушки, ширина 
        h : float
            Параметр катушки, расстояние между центрами соседних катушек в плате
       
   
    """
    ic('вычисляются коэффициенты чувствительности для секступольной катушки...')
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
    betaA = r7/r8
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
        
    sensitivity_uncompensated = math.pow(-1, N)*(1 - math.pow(betaA, N))
    sensitivity_uncomp_minus = math.pow(-1, N-1)*(1 - math.pow(betaA, N-1))

    return sensitivity_compensated, sensitivity_uncompensated, sensitivity_uncomp_minus

def harmonic_calculation(P, Q, p, q, sensitivity_compensated, sensitivity_uncompensated, outer_coil_radius, N, sensitivity_uncomp_minus, quant, aperture_radius, magnet_length, coil_count):
    '''
    Функция вычисляет коэффициенты разложения в ряд Фурье интегрированных сигналов компенсированной и некомпенсировнной катушек. 
    После этого по коэффициентам вычисляются отношения гармоник и параметры смещения магнитной оси.
    
    ------------------------------------------------------------------------------------
    Переменные

        integral_compensated_value : tuple
            Кортеж компенсированного сигнала после усреднения 
            по всем период в одном измерении
        integral_uncompensated_value : tuple
            Кортеж некомпенсированного сигнал после усреднения 
            по всем период в одном измерении
        sensitivity_compensated : tuple
            Коэффициенты компенсированной чувствительности 
            к гармоникам от N+1 до 16.
        sensitivity_uncompensated : float
            Коэффициент некомпенсированной чувствительности 
            к гармонике N
        outer_coil_radius : float
            Параметр катушки, расстояние от оси вращения 
            до центра внешней обмотки крайней катушки (А или Е)
        N : int
            Количество пар полюсов, характеристика типа магнита 
            (2 для квадрупольного, 3 для секступольного, 4 для октупольного)
        sensitivity_uncomp_minus : float
            Некомпенсированная чувствительность к гармонике N-1
        quant : float
            Кратность шага интегрирования 
            (q = 1 соответствует привязке к 1 градусу поворота)
        aperture_radius : float
            Радиус апертуры магнита
        magnet_length: float
            Длина рабочей области магнита
        coil_count : int
            Параметр катушки, число витков
        
    '''
   
    depth = 16  # количество гармоник
       
   
    mu0 = 4*math.pi*math.pow(10, -7)
    
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
            harmonics_relative_coeffs.append(abs(HRC_up/HRC_down))
        except ZeroDivisionError:
            harmonics_relative_coeffs.append(0)
        
    deltaX = outer_coil_radius * sensitivity_uncompensated * P[-2] / (sensitivity_uncomp_minus * N * math.sqrt(math.pow(P[-1], 2) + math.pow(Q[-1], 2)))
    deltaY = -1 * outer_coil_radius * sensitivity_uncompensated * Q[-2] / (sensitivity_uncomp_minus * N * math.sqrt(math.pow(P[-1], 2) + math.pow(Q[-1], 2)))

    return harmonics_relative_coeffs, deltaX, deltaY, source_rotation_angle_a, H_avg, P, Q

