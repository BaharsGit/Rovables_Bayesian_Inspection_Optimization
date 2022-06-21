import csv
import numpy as np
#import seaborn as sns
from scipy import stats, integrate
import matplotlib.pyplot as plt
from matplotlib import image
import pandas as pd
import os
import re

num_particles = 15
num_gen = 30

# target = "local_fitness_*"
# query = re.compile(query)

fitness_df = pd.DataFrame()

rootdir = '/home/darren/Documents/DARS/Run_2/'

for i in range(num_gen):
    particle_fit_temp = []
    gen = rootdir + "Generation_" + str(i)
    #print(gen)
    for j in range(num_particles):
        text = gen + "/local_fitness_" + str(j) + ".txt"
        #print(text)
        with open(text) as f:
           fit = f.read().splitlines()
           #print(float(fit[0]))
           particle_fit_temp.append(float(fit[0]))
    #print(particle_fit_temp)
    fitness_df[str(i)] = particle_fit_temp

print(fitness_df)
generation_mean = fitness_df.mean(axis=0)
generation_std = fitness_df.std(axis=0, ddof=0)
generation_best = fitness_df.min(axis=0)
print(generation_std)
plt.xlabel('Generation')
plt.ylabel('Decision Time')
plt.plot(np.arange(num_gen), generation_best, color='darkgreen', label='Best')
plt.plot(np.arange(num_gen), generation_mean, color='red', label='PSO Average')
plt.fill_between(np.arange(num_gen), generation_mean - generation_std, generation_mean + generation_std, color='lightcoral', alpha=0.3)
plt.legend()
plt.show()