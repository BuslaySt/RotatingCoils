# программа принимает на вход массив данных, находит нулевые импульсы и отдельные угловые импульсы 
# проводит интегрирование по одному периоду и далее усреднение по нескольким периодам
# вариант для использования в качестве модуля
# применяется округление до 6 знаков

import pandas as pd
import numpy as np
import math
from tqdm import tqdm
import matplotlib.pyplot as plt

from icecream import ic
# time;ch_a;ch_c;D0;D4


def integr(df_name):
	'''
	Функция вычисляет интеграл датафрейма
	roundN - порядок округления для ускорения расчетов.
	'''
	roundN = 4 #округление величин измерений для ускорения отладки
	timestamp = df_name.timestamp
	ch_A = df_name.ch_a
	ch_C = df_name.ch_c
	tick = df_name.D0
	zeroPulse = df_name.D4
	
	ch_A_norm = []
	compSignalR = []
	zeroed = []
	tickPos = []
	ic('DF has been read successfully')
	
	#определяется фронт импульса 0 энкодера и позиция пишется в отдельный файл
	for i in tqdm(range(1, len(timestamp)), desc = 'Detecting zero pulses and ticks'):
		if (zeroPulse[i-1] == 0) & (zeroPulse[i] == 1):
			zeroed.append(i)
			
		if (tick[i-1] == 0) & (tick[i] == 1):
			tickPos.append(i)
	
	ic('Zero pulses located')
	ic('Period count is', len(zeroed))
	ic(zeroed)
		
	periods = range(2, len(zeroed)-2)
	if len(periods)<2:
		return
	allPeriodInt = []
	allPeriodUncomp = []
	
	#вычисление постоянной составляющей
	#переработать устранение постоянной составляющей
	summaComp = 0
	summaUncomp = 0
	
	for k in tqdm(range(zeroed[0], (zeroed[-1]+1)), desc = 'Averaging signals'):
		summaUncomp = summaUncomp + ch_A[k]
		summaComp = summaComp + ch_C[k]
	
	constantComp = summaComp/ ((zeroed[-1]+1)-zeroed[0]) 
	constantUncomp = summaUncomp/ ((zeroed[-1]+1)-zeroed[0])
	
	for i in tqdm(range(zeroed[0], (zeroed[-1]+1)),"Calculating periods"):
		ch_A_norm.append(round((ch_A[i] - constantUncomp), roundN))
		compSignalR.append(round((ch_C[i] - constantComp), roundN))
	
	
	ic('periods, total', periods)
	for p in tqdm(periods, "Periods"):
		
		print('Integral calculation for period', p)
		step = timestamp[zeroed[p]+1] - timestamp[zeroed[p]]
		integral = []
		integralUncompA = []
		end, counter = 0, 0
		start = zeroed[p]
		finish = zeroed[p+1]

		for pos in tickPos:
			summaC = 0 #суммы для вычисления интеграла методом трапеций
			summaU = 0
			if (pos >= start) & (pos < finish):
				counter +=1
				
				if counter == 160: #160 - 1 градус при разрешении 57600
					end = pos
				
					for j in range(start+1, end):
						summaC = summaC + compSignalR[j]
						summaU = summaU + ch_A_norm[j]
									
					integral.append(round(0.5*step*(compSignalR[start] + compSignalR[end] + 2*summaC), roundN))
					integralUncompA.append(round(0.5*step*(ch_A_norm[start] + ch_A_norm[end] + 2*summaU), roundN))
					
					counter = 0
				
			if end > (finish+1):
				break
		
		allPeriodInt.append(integral)
		allPeriodUncomp.append(integralUncompA)
		print('CIntegral calculation for this period finished')
	#return(allPeriodInt, allPeriodUncomp)	

	#вычисление усредненного значения интегралов по нескольким периодам через транспонирование двухмерного списка			
	# summaM = sum(compSignal[n] for n in range (zeroed[3], zeroed[4]))
	
	arrInt = np.asarray(allPeriodInt)
	arrUncomp = np.asarray(allPeriodUncomp)
	
	avgIntComp = []
	avgIntUncomp = []
	
	avgI_transp = arrInt.transpose()
	avgU_transp = arrUncomp.transpose()
	for item in avgI_transp:
		avgIntComp.append(sum(item)/len(arrInt))
	for item in avgU_transp:
		avgIntUncomp.append(sum(item)/len(arrUncomp))
	# sumC = sum(avgArrInt[i, :] for i in range (len(avgArrInt)))
	# sumU = sum(avgArrUncomp[k, :] for k in range (len(avgArrUncomp)))

	# for m in range (len(sumC)):
		# avgIntComp.append(sumC[m]/len(avgArrInt))
	
	# for n in range (len(sumU)):
		# avgIntUncomp.append(sumU[n]/len(avgArrUncomp))
	
	# counter_j = len(allPeriodInt[0])
	# transpI = [[row[i] for row in allPeriodInt] for i in range(counter_j)]
	# avgIntComp = []
	# for item in transpI:
		# avgIntComp.append(sum(item)/len(allPeriodInt))
	
	# counter_i = len(allPeriodUncomp[0])
	# transpU = [[row[i] for row in allPeriodUncomp] for i in range(counter_i)]
	# avgIntUncomp = []
	# for item in transpU:
		# avgIntUncomp.append(sum(item)/len(allPeriodUncomp))		
	
	#return(allPeriodUncomp, avgIntComp, avgIntUncomp)
	return(avgIntComp, avgIntUncomp)
	
def qcoef(r, h):
	'''
	Функция вычисляет чувствительность катушки с квадруполльной компенсацией и заданными параметрами r, h. 
	При этом дополнительно задается тип 
	Sens - некомпенсированная чувствительность
	sens - компенсированная чувствительность3
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
	
	sens = []
	Sens = 0
	for n in tqdm(range(1, depth+1), "Sensitivity"):
		s_ED = 1 - math.pow(betaE, n) - math.pow(roD, n)*(1 - math.pow(betaD, n))
		s_BC = math.pow(roC, n)*(1 - math.pow(-1, n)) - math.pow(-1, n)*math.pow(roB, n)*(1 - math.pow(betaB, n))
		sens.append(s_ED - s_BC)
	Sens = (1 - math.pow(betaE, N))
	return(sens, Sens)

def scoef(r, h):
	'''
	Функция вычисляет чувствительность катушки с секступольной компенсацией и заданными параметрами r, h. 
	При этом дополнительно задается тип 
	Sens - некомпенсированная чувствительность
	sens - компенсированная чувствительность3
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
	
	sens = []
	Sens = 0
	for n in tqdm(range(1, depth+1), "Sensitivity"):
		s_ED = 1 - math.pow(betaE, n) - muD*math.pow(roD, n)*(1 - math.pow(betaD, n))
		s_BC = muC*math.pow(roC, n)*(1 - math.pow(-1, n)) - math.pow(-1, n)*math.pow(roB, n)*(1 - math.pow(betaB, n))
		sens.append(s_ED + s_BC)
		
		
	Sens = (1 - math.pow(betaE, N))
	return(sens, Sens)
		
def compute(comp, uncomp, sens, Sens, r):
	step = math.pi/180
	M = 56
		
	LCn = []
	psi = []
	p = []
	q = []
	
	for n in tqdm(range (1, 20), "order"):
		f_cos = []
		f_sin = []
	
		summa_c = 0
		summa_s = 0
	
		pee = 0
		quu = 0
	 	# компенсированная чувствительность
		start = 0 #начальный угол
		end = len(comp)
		
	
		for teta in range(start, end):
		# подынтегральные выражения для расчета коэффициентов разложения в ряд Фурье
			f_cos.append(comp[teta]*math.cos(n*teta*math.pi/180))
			f_sin.append(comp[teta]*math.sin(n*teta*math.pi/180))#
	
		f_c_start = f_cos[start]
		f_c_end = f_cos[end-1]
		f_s_start = f_sin[start]
		f_s_end = f_sin[end-1]
		
		for s in range(start+1, end):
			summa_c += f_cos[s]
			summa_s += f_sin[s]
		
		pee = ((1/math.pi)*0.5*step*(f_c_start + f_c_end + 2*summa_c))
		quu = ((1/math.pi)*0.5*step*(f_s_start + f_s_end + 2*summa_s))
			
	# LCn.append(math.sqrt(math.pow(pee, 2) + math.pow(quu, 2))/(M*math.pow(r, n)*s))	
		psi.append(-math.atan(quu/pee))
		p.append(pee)
		q.append(quu)
		
		
	# LBn.append(n*math.sqrt(math.pow(pee, 2) + math.pow(quu, 2))/(M*r*s))	
	
	
	
	LCN = []
	PSI = []
	P = []	
	Q = []
	N = 2
	# LBN = []


	F_cos = []
	F_sin = []
	
	summa_C = 0
	summa_S = 0
	Pee = 0
	Quu = 0
	
	
	start = 0 #начальный угол
	end = len(uncomp)
	
	for teta in tqdm(range(start, end), "Theta"):
		# подынтегральные выражения для расчета коэффициентов разложения в ряд Фурье
		F_cos.append(uncomp[teta]*math.cos(N*teta*math.pi/180))
		F_sin.append(uncomp[teta]*math.sin(N*teta*math.pi/180))#
	
	F_c_start = F_cos[start]
	F_c_end = F_cos[end-1]
	F_s_start = F_sin[start]
	F_s_end = F_sin[end-1]
		
	for s in range(start+1, end):
		summa_C += F_cos[s]
		summa_S += F_sin[s]
		
	Pee = ((1/math.pi)*0.5*step*(F_c_start + F_c_end + 2*summa_C))
	Quu = ((1/math.pi)*0.5*step*(F_s_start + F_s_end + 2*summa_S))
	
	
	# LCN.append(math.sqrt(math.pow(Pee, 2) + math.pow(Quu, 2))/(M*math.pow(r, n)*S))	
	PSI.append(-math.atan(Quu/Pee))
	# P.append(Pee)
	# Q.append(Quu)
	LBN = (N*math.sqrt(math.pow(Pee, 2) + math.pow(Quu, 2))/(M*r*Sens))

	B_otn = []

	R = math.sqrt(math.pow(Pee, 2) + math.pow(Quu, 2))/math.sqrt(math.pow(p[1], 2) + math.pow(q[1], 2))

	for n in tqdm(range (3, 16), "Order2"):
		B_otn.append (math.pow(10, 4)*(n*Sens*math.sqrt(math.pow(p[n], 2) + math.pow(q[n], 2)))/(N*sens[n]*math.sqrt(math.pow(Pee, 2) + math.pow(Quu, 2))))
			
	return(B_otn)	

if __name__ == "__main__":
	r = 1.45
	h = 1.4

	print("Reading data...")
	df = pd.read_csv('harm_data/data1.csv', delimiter=',')

	result = integr(df)
	sens, Sens = qcoef(r, h)

	comp, uncomp = result

	final_result = compute(comp, uncomp, sens, Sens, r)
	ic(final_result)
	plt.plot(final_result)
	plt.show()