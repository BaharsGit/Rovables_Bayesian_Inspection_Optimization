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
num_noise = 3
num_gen = 30
n_robots = 4
prob_column_names = []
pos_column_names = []
averages = pd.DataFrame()

for i in range(n_robots):
    prob_column_names.append('rov_{}'.format(i))
    pos_column_names.append('rov_{}_x'.format(i))
    pos_column_names.append('rov_{}_y'.format(i))

fitness_df = pd.DataFrame()
savePlots = 0
rootdir = '/Users/darrenchiu/Documents/DARS/Run_4/'
#rootdir = '/home/darren/Documents/DARS/Run_1/'
baselinedir = '/home/darren/Documents/DARS/baseline_800TAO/'

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
    generation_mean = fitness_df.mean(axis=0)
    generation_std = fitness_df.std(axis=0, ddof=0)
    generation_best = fitness_df.min(axis=0)
    print(generation_std)
    plt.xlabel('Generation')
    plt.ylabel('Decision Time')
    plt.plot(np.arange(num_gen), generation_best, color='darkgreen', label='Best')
    plt.plot(np.arange(num_gen), generation_mean, color='red', label='PSO Average')
    #plt.fill_between(np.arange(num_gen), generation_mean - generation_std, generation_mean + generation_std, color='lightcoral', alpha=0.3)
    plt.plot(np.arange(num_gen), generation_std, color='blue', label='PSO STD')
    plt.title('PSO Performance')
    plt.legend()
    plt.show()

########################################## CREATES BELIEF STD ###########################################
def createSTD():
    averages['mean'] = averages.mean(axis=1)
    averages['std'] = averages.std(axis=1, ddof=0)
    averages.to_csv('means.csv')
    plt.plot(np.arange(averages.shape[0]), (averages.loc[:, 'mean']).to_list(), color='dodgerblue', label='Simulation Average')
    plt.fill_between(np.arange(averages.shape[0]),
    (averages.loc[:, 'mean']) - (averages.loc[:, 'std']), 
    (averages.loc[:, 'mean']) + (averages.loc[:, 'std']), color='lightskyblue', alpha=0.3, label='One Standard Deviation')
    plt.axhline(y=0.5, color='r', linestyle='--')
    plt.xlabel('Simulation Time')
    plt.ylabel('Robot Belief')
    plt.title('Credibility Threshold = 0.95')
    plt.savefig(baselinedir + '/FB_95.png')

################################## READS IN FITNESS FILES ############################################
for i in range(num_gen):
    particle_fit_temp = []
    gen = rootdir + "Generation_" + str(i)
    #print(gen)
    for j in range(num_particles):
        for k in range(num_noise):
            text = gen + "/local_fitness_" + str(j) + "_" + str(k) + ".txt"
            #print(text)
            with open(text) as f:
                fit = f.read().splitlines()
                #print(float(fit[0]))
                particle_fit_temp.append(float(fit[0]))
    #print(particle_fit_temp)
    fitness_df[str(i)] = particle_fit_temp

############################### READS IN BASELINE FILES #####################################################
# for run in range(100):
#     posData = []
#     probData = []
#     posFile = baselinedir + '/Run' + str(run) + '/runPos.csv'
#     posData = pd.read_csv(posFile, names=pos_column_names)

#     probFile = baselinedir + '/Run' + str(run) + '/runProb.csv'
#     probData = pd.read_csv(probFile, names=prob_column_names)
#     probData['mean'] = probData.mean(axis=1)
#     currentAvgRun = (pd.DataFrame({str(run): (probData.loc[:, 'mean']).to_list()}))
#     #print(currentAvgRun.reset_index)
#     averages = pd.concat([averages, currentAvgRun], axis=1)
#     averages.fillna(method='ffill', inplace=True)


#     xPos = []
#     yPos = []
#     xIndex = 0
#     yIndex = 1
#     for i in range(n_robots):
#         xPos = np.append(xPos, (posData.loc[:, pos_column_names[xIndex]]).to_list(), axis=0)
#         yPos = np.append(yPos, (posData.loc[:, pos_column_names[yIndex]]).to_list(), axis=0)
#         xIndex = xIndex + 2
#         yIndex = yIndex + 2

#averages = averages[:-10]
#averages = averages.dropna(axis = 0, how = 'all')
#averages = averages.dropna()
psoFitness()
# print(averages)
# createSTD()
# plt.legend()
# plt.show()