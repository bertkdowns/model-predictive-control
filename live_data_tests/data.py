import random
# initialise python random number generator

random.seed("1234")

indexes = range(0,20)

# temperature data: constant at 600 K, with a random noise of 1 K
temperature = [600 + random.uniform(-1,1) for i in indexes]

# power data: ramp from 100 kw to 1MW
power = [(10*i +  random.uniform(-3,3)) * 1000 for i in indexes]

# pressure data: constant at 101325 Pa, with a random noise of 50 Pa
pressure = [101325 + random.uniform(-5,5) for i in indexes]
