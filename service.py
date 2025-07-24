#service module for rotating coil and Epstein software
#v. 0.1 July 2025
import numpy as np
import math
from tqdm import tqdm   # Progress bar


def array_averaging (allPeriod) -> tuple:
  
    '''
    Функция выполняет вычисление усредненного значения интегралов 
    по нескольким периодам через транспонирование двумерного списка.			
     ------------------------------------------------------------------------------------
    Переменные
        
        allPeriod : list
            Двумерный список. Каждая строка списка представляет собой 
            отдельный список, являющийся интегрированным сигналом 
            по одному периоду датафрейма. 

    ''' 
    
    avgArr = []
    arr = np.asarray(allPeriod)
    arrTransp = arr.transpose()
    avgArr = [sum(item)/len(arr) for item in arrTransp]

    return (avgArr)

def minus_integration (integral_list):
    '''
    Функция убирает постоянную составляющую после интегрирования. 
    ------------------------------------------------------------------------------------
    Переменные
    
        integral_list : list
            Список с отметками интегрированного сигнала по одному периоду из всего 
            датафрейма. Применяется к каждому периоду из датафрейма.
            
    '''
   
    corrected_integral = []
    delta = integral_list[-1] - integral_list[0]
    corrected_integral = [(value - delta*(i+1)/len(integral_list)) for i, value in enumerate(integral_list)]
    
    return corrected_integral

def minus_constant (input_channel, zeroPos_start, zeroPos_end):
    '''
    Функция убирает постоянную составляющую из входного сигнала. 
    ------------------------------------------------------------------------------------
    Переменные
    
        input_channel : столбец датафрейма
            Наименование столбца из входного датафрейма, 
            к которому применяется коррекция
        zeroPos_start : int
            Индекс строки датафрейма, в которой зарегистрирован 
            первый нулевой импульс энкодера в датафрейме
        zeroPos_end : int
            Индекс строки датафрейма, в которой зарегистрирован 
            последний нулевой импульс энкодера в датафрейме     
    '''
    
    constant = sum(input_channel[zeroPos_start:zeroPos_end + 1])/ len(input_channel[zeroPos_start:zeroPos_end + 1])
    channel_name_norm = [(input_channel[n] - constant) for n in tqdm(range(zeroPos_start, zeroPos_end + 1))]

    return channel_name_norm

def avg_constant (input_channel, zeroPos_start, zeroPos_end):
    '''
    Функция вычисляет постоянную составляющую из входного сигнала. 
    ------------------------------------------------------------------------------------
    Переменные
    
        input_channel : столбец датафрейма
            Наименование столбца из входного датафрейма, 
            к которому применяется коррекция
        zeroPos_start : int
            Индекс строки датафрейма, в которой зарегистрирован 
            первый нулевой импульс энкодера в датафрейме
        zeroPos_end : int
            Индекс строки датафрейма, в которой зарегистрирован 
            последний нулевой импульс энкодера в датафрейме     
    '''
    
    avg_constant = sum(input_channel[zeroPos_start:zeroPos_end + 1])/ len(input_channel[zeroPos_start:zeroPos_end + 1])

    return avg_constant
