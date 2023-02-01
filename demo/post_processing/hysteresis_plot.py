import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

p = np.arange(0, 1.01, 0.01)
h = np.arange(0, 101, 1)
XS = []
YS = []
ZS = []
p_c = 0.95
time_steps = 100
h_t = 80
d = -1

def hysteresis_logic(d, h_i, p_i, XS, YS):
    print(d)
    # print(h[h_i])
    # print(p[p_i])
    if (d == -1):
        if (h[h_i] == 0) and ((p[p_i] > p_c) or ((1-p[p_i])>p_c)):
            XS.append(h[h_i])
            YS.append(p[p_i])
            d = 0
            return d, XS, YS
        elif((h[h_i] != 0) and ((p[p_i] < p_c) and (1-p[p_i]) < p_c)):
            XS.append(h[h_i])
            YS.append(p[p_i])
            d = 0
            return d, XS, YS
        elif(((p[p_i] > p_c) or ((1-p[p_i]) > p_c)) and (h[h_i] > h_t)):
            XS.append(h[h_i])
            YS.append(p[p_i])
            d = 1
            return d, XS, YS
        else:
            XS.append(h[h_i])
            YS.append(p[p_i])
            d = -1 
            return d, XS, YS
    else:
        if ((d==1 and p[p_i] > p_c) or (d == 0 and (1-p[p_i]) > p_c)):
            if ((h[h_i]) > h_t):
                if (p[p_i] > p_c):
                    XS.append(h[h_i])
                    YS.append(p[p_i])
                    d = 0
                    return d, XS, YS
                if ((1-p[p_i])> p_c):
                    XS.append(h[h_i])
                    YS.append(p[p_i])
                    d = 1
                    return d, XS, YS
        else:
            return d, XS, YS


# Iterate through as if simulation
for i in range(time_steps):
    for j in range(time_steps):
        d, XS, YS = hysteresis_logic(d, i, j, XS, YS)
        ZS.append(d)
print(XS)
print(YS)
print(ZS)
plt.scatter(XS, YS, ZS)
plt.show()