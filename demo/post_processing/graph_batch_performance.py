import csv
from turtle import pos
import numpy as np
import seaborn as sns
from scipy import stats, integrate
import matplotlib.pyplot as plt
from matplotlib import image
import pandas

import os

n_robots = 4
savePlots = 1
pic_dim=128
square_size=8
squares_per_side=int(pic_dim/square_size)
arena_squares = np.empty([squares_per_side, squares_per_side])
distance_per_square = 1/squares_per_side
fitness_run = []

prob_column_names = []
pos_column_names = []
averages = pandas.DataFrame()
pos_column_names.append('time_step')
pos_run = []

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

# def getCoverage():


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



for i in range(n_robots):
    prob_column_names.append('rov_{}'.format(i))
    pos_column_names.append('rov_{}_x'.format(i))
    pos_column_names.append('rov_{}_y'.format(i))

for run in range(100):

    posData = []
    probData = []
    posFile = 'Log/Run' + str(run) + '/runPos.csv'
    posData = pandas.read_csv(posFile, names=pos_column_names)

    decTimeFile = 'Log/Run' + str(run) + '/decTime.txt'
    with open(decTimeFile) as f:
        lines = f.read().splitlines()
    fitness_run.append(float(lines[4]))
    # pos_run.append(posData)

    # probFile = 'Log/Run' + str(run) + '/runProb.csv'
    # probData = pandas.read_csv(probFile, names=prob_column_names)
    # probData['mean'] = probData.mean(axis=1)
    # currentAvgRun = (pandas.DataFrame({str(run): (probData.loc[:, 'mean']).to_list()}))
    # #print(currentAvgRun.reset_index)
    # averages = pandas.concat([averages, currentAvgRun], axis=1)
    # image = plt.imread('worlds/textures/textrect.png')

    # createGauss(run)
    # createCDF(run)
    # createLine(run)
print(fitness_run)
plt.hist(fitness_run)
plt.show() 