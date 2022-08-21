import csv
import statistics
import numpy as np
#import seaborn as sns
from scipy import stats, integrate
import matplotlib.pyplot as plt
from matplotlib import image
import pandas as pd
import os
import re
crash_fitness = 100000
incorrect_fitness = 11200
num_particles = 10
num_noise = 10
num_gen = 30
n_robots = 4
particle_dim = 6
probIn = []
prob_column_names = []
pos_column_names = []
best_param = []
param_max = [150, 350, 3000, 90, 100, 250]
param_min = [10, 10, 20, 10, 5, 200]
averages = pd.DataFrame()
fitness_df = pd.DataFrame()
fitness_df_median = pd.DataFrame()
param_df = pd.DataFrame()
best_param_df = pd.DataFrame()
incorrect_list_x = []
incorrect_list_y = []
std_gen = []

for i in range(n_robots):
    prob_column_names.append('rov_{}'.format(i))
    pos_column_names.append('rov_{}_x'.format(i))
    pos_column_names.append('rov_{}_y'.format(i))
    
savePlots = 0
#rootdir = '/Users/darrenchiu/Documents/DARS/Linear_Fitness/'
#PSO FITNESS
rootdir = '/home/darren/Documents/ICRA_LAUNCH/demo/jobfiles/Run_2/'
#rootdir = '/home/dchiu/Documents/ICRA_LAUNCHES/demo/jobfiles/Run_2/'
#BASELINE DIRECTORY
baselinedir = '/home/darren/Documents/DARS/NoiseResistance/Linear_pso_halfma'

################################### 2D Position Histogram ########################
def create2dHist(run):
    #Normalize frequency in bins. 
    #, bins=[np.arange(0,1,0.0001),np.arange(0,1,0.0001)]

    plt.figure(1)
    plt.hist2d(xPos,yPos)
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.colorbar()
    if(savePlots):
        saveDest = 'Log/Run' + str(run) + '/Hist.png'
        plt.savefig(saveDest)
    plt.clf()

#################################### CDF Line Graph ############################
# The changes of values would not line not with eachother since the random walk takes precedence -- number of steps in random walk differs per robot.
def createCDF(run):
    plt.figure(2)
    for i in range(n_robots):
        plt.plot((probData.loc[:, prob_column_names[i]]).to_list(), label = 'r{} CDF'.format(i))

    plt.legend()
    if(savePlots):
        saveDest = 'Log/Run' + str(run) + '/Decision.png'
        plt.savefig(saveDest)
    plt.clf()


####################################### Scatter Plot ##############################
#Add starting position and end position
def createLine(run):
    plt.figure(3)
    xIndex = 0
    yIndex = 1
    markers = ['-bo', '-go', '-ro', '-yo']
    
    for i in range(n_robots):
        plt.plot(posData.loc[:,pos_column_names[xIndex]].to_list(), posData.loc[:,pos_column_names[yIndex]].to_list(), markers[i] , markevery=[0],label = 'r{} path'.format(i))        
        xIndex = xIndex + 2
        yIndex = yIndex + 2
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.legend()
    if(savePlots):
        saveDest = 'Log/Run' + str(run) + '/Path.png'
        plt.savefig(saveDest)
    plt.clf()

#################################### Gaussian Heat Map #############################
# From this: https://zbigatron.com/generating-heatmaps-from-coordinates/ and https://stackoverflow.com/questions/50091591/plotting-seaborn-heatmap-on-top-of-a-background-picture
def createGauss(run):
    combined=1

    if not (combined):
        plt.figure(4)
        print("Creating Gaussian Heatmap...")
        cmap = plt.cm.get_cmap('coolwarm')
        xIndex = 0
        yIndex = 1
        for i in range(n_robots):
            heatmap = sns.kdeplot(x=posData.loc[:,pos_column_names[xIndex]].to_list(), y=posData.loc[:,pos_column_names[yIndex]].to_list(), label='r{} path'.format(i), alpha=0.75, fill=True, zorder = 1)
            xIndex = xIndex + 2
            yIndex = yIndex + 2
        heatmap.imshow(image, extent=[0,1,0,1], zorder = 0, cmap='gray')
        plt.xlim([0, 1])
        plt.ylim([0, 1])
        plt.title('Run 92 Exploration Heatmap')
        if(savePlots):
            plt.savefig('GaussHeat.png')
        plt.clf()
        
    else:
        plt.figure(4)
        cmap = plt.cm.get_cmap('coolwarm')
        heatmap = sns.kdeplot(x=xPos, y=yPos, cmap=cmap, alpha=0.75, fill=True, zorder = 1)
        heatmap.imshow(image, extent=[0,1,0,1], zorder = 0, cmap='gray')
        plt.xlim([0, 1])
        plt.ylim([0, 1])
        plt.title('Run 92 Exploration Heatmap')
        if(savePlots):
            saveDest = 'Log/Run' + str(run) + '/GaussHeat.png'
            plt.savefig(saveDest, transparent=True)
        plt.clf()

######################################## CREATES FITNESS EVOLUATION ##############################
def psoFitness():
    fig = plt.figure()
    ax = fig.add_subplot(111)
    generation_mean = fitness_df.mean(axis=0)
    generation_std = fitness_df.std(axis=0, ddof=0)
    for i in range(len(generation_std)):
        if generation_std[i] < 0:
            generation_std[i] = 0
    #print(generation_std)
    generation_best = fitness_df.min(axis=0)
    #print(generation_best)
    best = float('inf')
    for i in range(len(generation_best)):
        if generation_best[i] < best:
            print(best, i)
            best = generation_best[i]
        else:
            generation_best[i] = best
    #print(generation_best)
    # print(generation_std)
    ax.set_xlabel('Iterations')
    ax.set_ylabel('Fitness')
    ax2 = ax.twinx()
    #plt.yscale('log')
    param_fade = 0.4
    ax2.plot(np.arange(num_gen), param_df.iloc[0], color='magenta', label='Alpha', alpha=param_fade)
    ax2.plot(np.arange(num_gen), param_df.iloc[1], color='green', label='Tao', alpha=param_fade)
    ax2.plot(np.arange(num_gen), param_df.iloc[2], color='yellow', label='Forward', alpha=param_fade)
    ax2.plot(np.arange(num_gen), param_df.iloc[3], color='cyan', label='CA Trigger', alpha=param_fade)
    ax2.plot(np.arange(num_gen), param_df.iloc[4], color='purple', label='Hysterisis', alpha=param_fade)
    ax2.plot(np.arange(num_gen), param_df.iloc[5], color='black', label='Wait Time', alpha=param_fade)

    # ------------------------------------------#
    # ax2.plot(np.arange(num_gen), best_param_df.iloc[0], color='magenta', linestyle='--')
    # ax2.plot(np.arange(num_gen), best_param_df.iloc[1], color='green', linestyle='--')
    # ax2.plot(np.arange(num_gen), best_param_df.iloc[2], color='yellow', linestyle='--')
    # ax2.plot(np.arange(num_gen), best_param_df.iloc[3], color='cyan', linestyle='--')
    # ------------------------------------------#
    # ax2.plot(np.arange(num_gen), np.linalg.norm(param_df.iloc[0] - best_param_df.iloc[0]), color='green', label='Alpha', alpha=param_fade)
    # ax2.plot(np.arange(num_gen), np.linalg.norm(param_df.iloc[0] - best_param_df.iloc[1]), color='magenta', label='Tao', alpha=param_fade)
    # ax2.plot(np.arange(num_gen), np.linalg.norm(param_df.iloc[0] -  best_param_df.iloc[2]), color='yellow', label='Forward', alpha=param_fade)
    # ax2.plot(np.arange(num_gen), np.linalg.norm(param_df.iloc[0] - best_param_df.iloc[3]), color='cyan', label='Hysterisis', alpha=param_fade)
    # ------------------------------------------#
    ax.plot(np.arange(num_gen), generation_best, color='red', label='Best Particle')
    ax.plot(np.arange(num_gen), generation_mean, color='blue', label='PSO Average')
    #ax.plot(np.arange(num_gen-1), generation_mean[1:] - generation_best[1:], color='green', label='Distance from Best')
    bottom = generation_mean - generation_std
    bottom[bottom<0] = 0
    ax.fill_between(np.arange(num_gen), bottom, generation_mean + generation_std, where=(generation_mean + generation_std)>0, color='blue', alpha=0.3)
    #ax2.plot(np.arange(num_gen), generation_std, color='green', label='Standard Deviation')
    #plt.ylim([0, 5])
    plt.title('PSO Evaluation')
    ax.legend(fancybox=True, shadow=True)
    ax2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
         fancybox=True, shadow=True, ncol=4)
    plt.savefig(rootdir + 'figure.png')
    
    plt.show()

######################################### SCATTER PLOT VERSION PSO FITNESS ################################

#3CHANGE COLORS
def psoFitnessScatter():
    plt.style.use('seaborn-talk')
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax2 = ax.twinx()
    generation_mean = fitness_df.mean(axis=0)
    generation_std = fitness_df.std(axis=0, ddof=0)
    for i in range(len(generation_std)):
        if generation_std[i] < 0:
            generation_std[i] = 0
    #print(generation_std)
    generation_best = fitness_df.min(axis=0)
    #print(generation_best)
    best = float('inf')
    for i in range(len(generation_best)):
        if generation_best[i] < best:
            print(best, i)
            best = generation_best[i]
        else:
            generation_best[i] = best
    for i in range(num_particles):
        ax.scatter(np.arange(num_gen), fitness_df.iloc[i], color='green', s=15)
    for i in range(len(incorrect_list_y)):
        ax.scatter(incorrect_list_x[i], fitness_df.iloc[incorrect_list_y[i], incorrect_list_x[i]], color='red', s=15)
    ax.plot(np.arange(num_gen), generation_best, color='red', label='Best Particle')
    ax2.plot(np.arange(num_gen), std_gen, label='Standard Deviation')
    bottom = generation_mean - std_gen
    bottom[bottom<0] = 0
    ax.fill_between(np.arange(num_gen), bottom, generation_mean + std_gen, where=(generation_mean + std_gen)>0, color='blue', alpha=0.3)
    ax.plot(np.arange(num_gen), generation_mean, color='blue', label='PSO Average')
    ax.grid(True, linestyle='--', axis='both', color='black')
    plt.title('PSO Performance')
    plt.legend()
    plt.show()

########################################## CREATES BELIEF STD ###########################################
def createSTD():
    averages['mean'] = averages.mean(axis=1)
    averages['std'] = averages.std(axis=1, ddof=0)
    averages.to_csv(baselinedir + '/means.csv')
    plt.plot(np.arange(averages.shape[0]), (averages.loc[:, 'mean']).to_list(), color='dodgerblue', label='Simulation Average')
    plt.fill_between(np.arange(averages.shape[0]),
    (averages.loc[:, 'mean']) - (averages.loc[:, 'std']), 
    (averages.loc[:, 'mean']) + (averages.loc[:, 'std']), color='lightskyblue', alpha=0.3, label='One Standard Deviation')
    #plt.axhline(y=0.5, color='r', linestyle='--')

    plt.xlabel('Simulation Time')
    plt.ylabel('Robot Belief')
    plt.title('Linear Fitness Baseline')
    plt.savefig(baselinedir + '/FB_95.png')
    plt.ylim([0, 0.05])
    plt.legend()
    plt.show()


################################## READS IN FITNESS FILES ############################################
def readFitness():
    global best_param
    global std_gen
    global incorrect_list
    best_particle = 1000000
    median_average = []
    best_path = ''
    text = ''
    for i in range(num_gen):
        particle_fit_temp = []
        incorrect_temp = []
        std_temp = []
        particle_param_temp = np.zeros(particle_dim)
        gen = rootdir + "Generation_" + str(i)
        #print(gen)
        for j in range(num_particles):
            time_total = 0
            prob_path = gen + "/prob_" + str(j) + ".txt"
            #Read in parameters
            with open(prob_path) as f:
                probIn = f.read().splitlines()
            probIn = np.asarray(probIn, dtype=np.float64)
            for l in range(particle_dim):
                probIn[l] = (probIn[l] - param_min[l]) / (param_max[l] - param_min[l])
                
            particle_param_temp = np.add(probIn, particle_param_temp)

            for k in range(num_noise):
                text = gen + "/local_fitness_" + str(j) + "_" + str(k) + ".txt"
            #print(text)
                with open(text) as f:
                    fit = f.read().splitlines()
                if (float(fit[0]) < incorrect_fitness):
                    print(text)
                if (float(fit[0]) == incorrect_fitness) and (len(incorrect_temp) == 0):
                    incorrect_list_x.append(i)
                    incorrect_list_y.append(j)
                if (float(fit[0]) < crash_fitness):
                    std_temp.append(float(fit[0]))
                    median_average.append(float(fit[0]))
                    time_total = float(fit[0]) + time_total
                else:
                    print(text)
            noise_average = float(time_total)/num_noise
            if (noise_average < best_particle):
                best_particle = noise_average
                best_path = prob_path
                best_param = probIn
            particle_fit_temp.append(statistics.median(median_average))
            #particle_fit_temp.append(noise_average)
        #print(particle_fit_temp)

        best_param_df[str(i)] = best_param
        param_df[str(i)] = np.divide(particle_param_temp, num_particles)
        #print(particle_fit_temp)
        std_gen.append(statistics.pstdev(std_temp))
        fitness_df[str(i)] = particle_fit_temp
    print("Best Particle: ", best_path)
    fitness_df.to_csv(rootdir + 'means.csv')
    #print(fitness_df)
    # print(param_df)
    # print(best_particle)
    # print(best_path)

############################### READS IN BASELINE FILES #####################################################
def readBaseline():
    for run in range(100):
        posData = []
        probData = []
        posFile = baselinedir + '/Run' + str(run) + '/runPos.csv'
        posData = pd.read_csv(posFile, names=pos_column_names)

        probFile = baselinedir + '/Run' + str(run) + '/runProb.csv'
        probData = pd.read_csv(probFile, names=prob_column_names)
        probData['mean'] = probData.mean(axis=1)
        currentAvgRun = (pd.DataFrame({str(run): (probData.loc[:, 'mean']).to_list()}))
        #print(currentAvgRun.reset_index)
        averages = pd.concat([averages, currentAvgRun], axis=1)
        averages.fillna(method='ffill', inplace=True)


        xPos = []
        yPos = []
        xIndex = 0
        yIndex = 1
        for i in range(n_robots):
            xPos = np.append(xPos, (posData.loc[:, pos_column_names[xIndex]]).to_list(), axis=0)
            yPos = np.append(yPos, (posData.loc[:, pos_column_names[yIndex]]).to_list(), axis=0)
            xIndex = xIndex + 2
            yIndex = yIndex + 2

readFitness()
# print(param_df.iloc[0])
# print(best_param_df.iloc[0])
# print(np.linalg.norm(param_df.iloc[0] - best_param_df.iloc[0]))
# psoFitness()
psoFitnessScatter()
