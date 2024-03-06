# программа принимает на вход массив данных, находит нулевые импульсы и отдельные угловые импульсы 
# проводит интегрирование по одному периоду и далее усреднение по нескольким периодам
# вариант для использования в качестве модуля
# применяется округление до 6 знаков

# import pandas as pd
import numpy as np
import math

# time;ch_a;ch_c;D0;D4
# filename_output = f'Result_{filename[df_count]}.txt'

def integr(df_name) -> tuple:
	'''
	Функция вычисляет интеграл датафрейма
	roundN - порядок округления для ускорения расчетов.
	'''
	roundN = 5 #количество символов для округления(достаточно и 3)
	
	timestamp = df_name.timestamp
	ch_A = df_name.ch_a
	ch_C = df_name.ch_c
	tick = df_name.D0
	zeroPulse = df_name.D4
	
	ch_A_norm = []
	compSignal = []
	compSignalR = []
	zeroed = []
	tickPos = []
	

	#определяется фронт импульса 0 энкодера и позиция пишется в отдельный файл
	for i in range(1, len(timestamp)):
		if (zeroPulse[i-1] == 0) & (zeroPulse[i] == 1):
			zeroed.append(i)
		if (tick[i-1] == 0) & (tick[i] == 1):
			tickPos.append(i)
		for k in range(len(timestamp)):
			compSignal.append(ch_C[k]) #для 2 каналов

	#вычисление постоянной составляющей
	periods = range(2, (len(zeroed)-1))
	if len(periods)<2:
		return
	allPeriodInt = []
	allPeriodUncomp = []
	summaComp = 0
	summaUncomp = 0
				
	for k in range(zeroed[0], (zeroed[-1]+1)):
		summaUncomp = summaUncomp + ch_A[k]
		summaComp = summaComp + compSignal[k]
	
	constantComp = summaComp/ ((zeroed[-1]+1)-zeroed[0]) 
	constantUncomp = summaUncomp/ ((zeroed[-1]+1)-zeroed[0])

	for i in range(zeroed[0], (zeroed[-1]+1)):
		ch_A_norm.append(round((ch_A[i] - constantUncomp), roundN))
		compSignalR.append(round((compSignal[i] - constantComp), roundN))
	
	for p in periods:
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
			
	#вычисление усредненного значения интегралов по нескольким периодам через транспонирование двухмерного списка			
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
	
	return (avgIntComp, avgIntUncomp)
	
def qcoef(r: float, h: float) -> tuple:
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
	for n in range (1, depth+1):
		s_ED = 1 - math.pow(betaE, n) - math.pow(roD, n)*(1 - math.pow(betaD, n))
		s_BC = math.pow(roC, n)*(1 - math.pow(-1, n)) - math.pow(-1, n)*math.pow(roB, n)*(1 - math.pow(betaB, n))
		sens.append(s_ED - s_BC)
	Sens = (1 - math.pow(betaE, N))
	return (sens, Sens)

def scoef(r: float, h: float) -> tuple:
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
	for n in range (1, depth+1):
		s_ED = 1 - math.pow(betaE, n) - muD*math.pow(roD, n)*(1 - math.pow(betaD, n))
		s_BC = muC*math.pow(roC, n)*(1 - math.pow(-1, n)) - math.pow(-1, n)*math.pow(roB, n)*(1 - math.pow(betaB, n))
		sens.append(s_ED + s_BC)
		
		
	Sens = (1 - math.pow(betaE, N))
	print(type(sens))
	print(type(Sens))
	return (sens, Sens)
		
def compute(comp, uncomp, sens, Sens, r) -> list:
	step = math.pi/180
	M = 56
		
	LCn = []
	psi = []
	p = []
	q = []
	
	for n in range (1, 20):
		f_cos = []
		f_sin = []
	
		summa_c = 0
		summa_s = 0
	
		pee = 0
		quu = 0
		#компенсированная чувствительность
		start = 0 #начальный угол
		end = len(comp)
		
	
		for teta in range(start, end):
		#подынтегральные выражения для расчета коэффициентов разложения в ряд Фурье
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
	
	for teta in range(start, end):
		#подынтегральные выражения для расчета коэффициентов разложения в ряд Фурье
		F_cos.append(uncomp[teta]*math.cos(N*teta*math.pi/180))
		F_sin.append(uncomp[teta]*math.sin(N*teta*math.pi/180))
	
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

	for n in range (3, 16):
		B_otn.append (math.pow(10, 4)*(n*Sens*math.sqrt(math.pow(p[n], 2) + math.pow(q[n], 2)))/(N*sens[n]*math.sqrt(math.pow(Pee, 2) + math.pow(Quu, 2))))
			
	return(B_otn)	

if __name__ == "0":
	r = 1.45
	h = 1.4

	result = calc.integr(df)
	sens = calc.qcoef(r, h)[0]
	Sens = calc.qcoef(r, h)[1]

	comp = result[0]
	uncomp = result[1]

	final_result = calc.compute(comp, uncomp, sens, Sens, r)