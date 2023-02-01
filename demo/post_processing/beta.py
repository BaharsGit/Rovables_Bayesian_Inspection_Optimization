import sys 
import numpy as np
from scipy.stats import beta
import matplotlib.pyplot as plt
import math
error = 0.1
a = int(sys.argv[1])
b = int(sys.argv[2])
x = float(sys.argv[3])
p = float(sys.argv[4])

n = 1000
cdf = -1
print("Finding alpha for p=",p)

# ax.plot(x, beta.pdf(x, a, b), 'r-', alpha=0.6, label='beta pdf with cdf: ' + str(cdf))

for i in range(0, n):
    a = i
    cdf = beta.cdf(x, a, b)
    if (math.fabs(cdf - p) < error):
        break

print("Alpha=", a)