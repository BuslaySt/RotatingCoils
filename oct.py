from icecream import ic
import math
import numpy as np

def octupole_coefficient(r: float, h: float) -> tuple:
    '''
    Функция вычисляет коэффициенты чувствительности катушки. В качестве входных данных принимаются параметры катушки.
    
    ------------------------------------------------------------------------------------
    Переменные

        r : float
            Параметр катушки, ширина 
        h : float
            Параметр катушки, расстояние между центрами соседних катушек в плате
       
    '''
    ic('вычисляются коэффициенты чувствительности для октуполньой катушки...')
    N = 4
    
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
    

    for n in range(1, 21):
        
        slag_1 = -1*(pow(z_u2, n) - pow(z_u1, n) + pow(z_d2, n) - pow(z_d1, n))
        slag_2 = 2*(pow(z_u4, n) - pow(z_u3, n) + pow(z_d4, n) - pow(z_d3, n))
        slag_3 = -1*(pow(z_u6, n) - pow(z_u5, n) + pow(z_d6, n) - pow(z_d5, n))
        SCC = (slag_1 + slag_2 + slag_3).real
        if (abs(SCC) < 0.0001):
            SCC = 0 
        sensitivity_compensated.append(SCC)
    
   
    sensitivity_uncompensated = 2*(pow(r4, N) - pow(r3, N))
    sensitivity_uncomp_minus = 2*(pow(r4, N-1) - pow(r3, N-1))
    
    return sensitivity_compensated, sensitivity_uncompensated, sensitivity_uncomp_minus



def harmonic_calculation(P, Q, p, q, sensitivity_compensated, sensitivity_uncompensated, outer_coil_radius, N, sensitivity_uncomp_minus, quant, aperture_radius, magnet_length, coil_count, R0, Leff):
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
        R0 : float
            Параметр катушки, расстояние между центром вращения системы катушек 
            и верхним краем платы системы катушек
        Leff : float
            Параметр катушки, эффективная длина катушки 
    '''
    mu0 = 4*math.pi*math.pow(10, -7)
    depth = 16

    harmonics_relative_coeffs = []
    for n in range (1, depth+1):
        try:
            HRC_coef = pow(outer_coil_radius, n-N)
            HRC_up = n*sensitivity_uncompensated * math.sqrt(math.pow(p[n-1], 2) + math.pow(q[n-1], 2)) #числитель дроби
            HRC_down = N*sensitivity_compensated[n-1] * math.sqrt(math.pow(P[-1], 2) + math.pow(Q[-1], 2)) #знаменатель дроби
            harmonics_relative_coeffs.append(abs(HRC_coef*HRC_up/HRC_down))
        except ZeroDivisionError:
            harmonics_relative_coeffs.append(0)
    
    psy_angle = -math.atan(Q[-1] / P[-1])
    source_rotation_angle_a = psy_angle * N # Угол поворота источника поля альфа
    
    G_Nminus_up = ((N-1)*N*math.sqrt(math.pow(P[-1], 2) + math.pow(Q[-1], 2))) #числитель дроби
    G_Nminus_down = (magnet_length*coil_count*math.pow(outer_coil_radius, N)*sensitivity_uncompensated) #знаменатель дроби
    G_Nminus = G_Nminus_up/G_Nminus_down
    Bn = G_Nminus*math.pow(aperture_radius, N-1)
    H_avg = Bn/(2*mu0)
    
    deltaX = sensitivity_uncompensated * P[-2] / (sensitivity_uncomp_minus * N * math.sqrt(math.pow(P[-1], 2) + math.pow(Q[-1], 2)))
    deltaY = -1 * sensitivity_uncompensated * Q[-2] / (sensitivity_uncomp_minus * N * math.sqrt(math.pow(P[-1], 2) + math.pow(Q[-1], 2)))

    return harmonics_relative_coeffs, deltaX, deltaY, source_rotation_angle_a, H_avg, P, Q
