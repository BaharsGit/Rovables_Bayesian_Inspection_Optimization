import csv
import statistics
import numpy as np
#import seaborn as sns
import scipy
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import image
import pandas as pd
import os
import re
from numpy.linalg import norm

crash_fitness = 100000
incorrect_fitness = 11200
num_baseline = 100
num_particles = 10
num_noise = 10
num_gen = 20
num_robots = 4
particle_dim = 6
probIn = []
prob_column_names = []
pos_column_names = []
best_param = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
param_max = [150, 350, 3000, 90, 100, 250]
param_min = [10, 10, 20, 10, 5, 200]
fitness_df = pd.DataFrame()
fitness_df_median = pd.DataFrame()
param_df = pd.DataFrame()
best_param_df = pd.DataFrame()
L2_df = pd.DataFrame()
incorrect_list_x = []
incorrect_list_y = []
incorrect_list_z = []
std_gen = []

for i in range(num_robots):
    prob_column_names.append('rov_{}'.format(i))
    pos_column_names.append('rov_{}_x'.format(i))
    pos_column_names.append('rov_{}_y'.format(i))
    
savePlots = 0

#PSO FITNESS DIRECTORY
#rootdir = '/home/darren/Documents/ICRA_LAUNCH/demo/jobfiles/Run_2/'
# DIRECTOR FOR ALPHA: '/home/dchiu/Documents/ICRA_LAUNCHES/spike_fix/jobfiles/Run_1/'
# DIRECTORY FOR NO ALPHA: '/home/dchiu/Documents/ICRA_LAUNCHES/no_alpha_particle/jobfiles/Run_1/'

psodir = '/home/dchiu/Documents/ICRA_LAUNCHES/no_alpha_particle/jobfiles/Run_1/'

#BASELINE DIRECTORY
baselinedir_median = '/home/dchiu/Documents/ICRA_LAUNCHES/full_particle_median_baseline/Log'
baselinedir_best = '/home/dchiu/Documents/ICRA_LAUNCHES/full_particle_best_baseline/Log'

desc = 'Full Particle Parameters'

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
def createCDF(run, probData):
    plt.figure(2)
    for i in range(num_robots):
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
    
    for i in range(num_robots):
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
        for i in range(num_robots):
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
    plt.savefig(psodir + 'figure.png')
    
    plt.show()
######################################### SCATTER PLOT VERSION PSO FITNESS ################################

def psoFitnessScatter():
    plt.style.use('seaborn-talk')
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax2 = ax.twinx()
    generation_mean = fitness_df.mean(axis=0)
    L2_mean = L2_df.mean(axis=0)
    generation_std = fitness_df.std(axis=0, ddof=0)
    L2_std = L2_df.std(axis=0, ddof=0)
    # for i in range(len(generation_std)):
    #     if generation_std[i] < 0:
    #         generation_std[i] = 0

    # for i in range(len(L2_std)):
    #     if L2_std[i] < 0:
    #         L2_std[i] = 0
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

    #Plot the particles where all evaluations made a decision within time
    for i in range(num_particles):
        ax.scatter(np.arange(num_gen), fitness_df.iloc[i], color='green', s=25)
    
    #Plot all particles with the large fitness values
    ax.scatter(incorrect_list_x, np.diag(fitness_df.iloc[incorrect_list_y, incorrect_list_x]), c=incorrect_list_z, s=25, cmap='Reds')

    #Plot Best Particle
    ax.plot(np.arange(num_gen), generation_best, color='red', label='Best Particle')


    #SECTION FOR MEAN AND STD OF PARTICLE FITNESS
    std_gen = generation_std
    bottom = generation_mean - std_gen
    bottom[bottom<0] = 0
    ax.fill_between(np.arange(num_gen), bottom, generation_mean + std_gen, where=(generation_mean + std_gen)>0, color='blue', alpha=0.3)
    ax.plot(np.arange(num_gen), generation_mean, color='blue', label='PSO Average')

    
    std_gen = L2_std
    bottom = L2_mean - std_gen
    bottom[bottom<0] = 0
    ax2.fill_between(np.arange(num_gen), bottom, L2_mean + std_gen, where=(L2_mean + std_gen)>0, color='green', alpha=0.3)
    ax2.plot(np.arange(num_gen), L2_mean, color='green', label='L2 Norm')

    ax.grid(True, linestyle='--', axis='both', color='black', alpha=0.3)
    #plt.colorbar(label="Bad Fitness Count", orientation="vertical")
    plt.title(desc)
    ax.legend(loc='upper left')
    ax2.legend()
    plt.show()

########################################## CREATES BELIEF STD ###########################################
def createSTD(averages):
    averages['mean'] = averages.mean(axis=1)
    averages['std'] = averages.std(axis=1, ddof=0)
    averages.to_csv(baselinedir + '/means.csv')
    plt.plot(np.arange(averages.shape[0]), (averages.loc[:, 'mean']).to_list(), color='dodgerblue', label='Simulation Average')
    plt.fill_between(np.arange(averages.shape[0]),
    (averages.loc[:, 'mean']) - (averages.loc[:, 'std']), 
    (averages.loc[:, 'mean']) + (averages.loc[:, 'std']), color='lightskyblue', alpha=0.3, label='One Standard Deviation')
    # plt.axhline(y=0.5, color='r', linestyle='--')

    plt.xlabel('Simulation Time')
    plt.ylabel('Robot Belief')
    plt.title('Linear Fitness Baseline')
    plt.savefig(baselinedir + '/' + desc + '_belief' + '.png')
    # plt.ylim([0, 1])
    plt.legend()
    plt.show()

################################## BINNING FOR DECISION TIMES ########################################
def decTimeBins(time_averages_best, time_averages_median):
    bestcolor = 'royalblue'
    mediancolor = 'lightcoral'
    bin_num = 200
    mu_best = np.average(time_averages_best)
    mu_median = np.average(time_averages_median)
    #plt.hist(time_averages, bins=25, density=True, alpha=0.6, color='g')
    # Plot the PDF.
    # xmin, xmax = plt.xlim()
    # x = np.linspace(xmin, xmax, 100)
    # p = scipy.stats.norm.pdf(x, mu, std)
    # plt.plot(x, p, 'k', linewidth=2)
    plt.grid(True, linestyle='--', axis='both', color='black', alpha=0.3)
    title = "Best Particle Average: %.2f, Median Particle Average: %.2f" % (mu_best, mu_median)
    plt.hist(time_averages_best, bins=bin_num, density='True', label='Best Particle', color=bestcolor)
    plt.hist(time_averages_median, bins=bin_num, density='True', label='Median Particle', color=mediancolor)
    plt.title(title)
    plt.xlabel('Average Swarm Decision Times')
    plt.ylabel('Density')
    sns.kdeplot(time_averages_best, bw_method=0.1, color=bestcolor)
    sns.kdeplot(time_averages_median, bw_method=0.1, color=mediancolor)
    plt.legend()
    plt.savefig(baselinedir_best + '/' + desc + '_time'+ '.png')
    plt.savefig(baselinedir_median + '/' + desc + '_time'+ '.png')
    plt.show()
    # plt.show()

################################## READS IN FITNESS FILES ############################################
def readFitness():
    global best_param
    global std_gen
    global incorrect_list
    best_particle = 1000000
    median_average = []
    best_path = ''
    text = ''

    #Iterate through iterations
    for i in range(num_gen):
        fitness_temp = []
        std_temp = []
        L2_temp = []
        param_temp = []
        param_avg_temp = np.zeros(particle_dim)
        gen = psodir + "Generation_" + str(i)
        
        #Iterate through particles
        for j in range(num_particles):
            duplicate_list = []
            bad_count = 0
            time_total = 0
            prob_path = gen + "/prob_" + str(j) + ".txt"

            #Iterate through noise runs
            for k in range(num_noise):
                text = gen + "/local_fitness_" + str(j) + "_" + str(k) + ".txt"

                with open(text) as f:
                    fit = f.read().splitlines()

                if (float(fit[0]) == incorrect_fitness):

                    bad_count = bad_count + 1
                    if (j not in duplicate_list):
                        incorrect_list_x.append(i)
                        incorrect_list_y.append(j)
                        duplicate_list.append(j)

                if (float(fit[0]) < crash_fitness):
                    std_temp.append(float(fit[0]))
                    median_average.append(float(fit[0]))
                    time_total = float(fit[0]) + time_total

            if (bad_count > 0):
                incorrect_list_z.append(bad_count)
            noise_average = float(time_total)/num_noise

            #Read in parameters
            with open(prob_path) as f:
                probIn = f.read().splitlines()
            probIn = np.asarray(probIn, dtype=np.float64)

            #Normalize Particle
            for l in range(particle_dim):
                probIn[l] = (probIn[l] - param_min[l]) / (param_max[l] - param_min[l])

            #Find if the normalized particle is the best
            if (noise_average < best_particle):
                print("Found New Best: ", text)
                best_particle = noise_average
                best_path = prob_path
                best_param = probIn

            param_temp.append(probIn)
            param_avg_temp = np.add(probIn, param_avg_temp)

            #Use median or standard deviation
            fitness_temp.append(statistics.median(median_average))
            #fitness_temp.append(noise_average)

        for l in range(num_particles):
            #Get L2 Norm from current parameters and best parameters
            L2_val = norm(param_temp[l] - best_param)  
            L2_temp.append(L2_val)
        
        #Dataframe that tracks the best parameter
        best_param_df[str(i)] = best_param

        #Dataframe that tracks the average particle parameters
        param_df[str(i)] = np.divide(param_avg_temp, num_particles)

        #Dataframe that tracks the L2 norm from the best particle
        L2_df[str(i)] = L2_temp
        std_gen.append(statistics.pstdev(std_temp))
        fitness_df[str(i)] = fitness_temp

    print("Best Particle: ", best_path)
    fitness_df.to_csv(psodir + 'means.csv')

    print("Median particle: ", statistics.median(fitness_temp))

############################### READS IN BASELINE FILES #####################################################
def readBaseline(baseline_path):
    belief_averages = pd.DataFrame()
    time_averages = np.zeros(num_baseline)

    for run in range(num_baseline):
        posData = []
        probData = []
        decTime = np.zeros(num_robots)
        with open(baseline_path + '/Run' + str(run) + '/decTime.txt') as f:
            decTime = np.asarray(f.read().splitlines(), dtype=np.float32)
        time_averages[run] = np.average(decTime)
        posFile = baseline_path + '/Run' + str(run) + '/runPos.csv'
        posData = pd.read_csv(posFile, names=pos_column_names)
        probFile = baseline_path + '/Run' + str(run) + '/runProb.csv'
        probData = pd.read_csv(probFile, names=prob_column_names)

        probData['mean'] = probData.mean(axis=1)
        currentAvgRun = (pd.DataFrame({str(run): (probData.loc[:, 'mean']).to_list()}))
        #print(currentAvgRun.reset_index)

        belief_averages = pd.concat([belief_averages, currentAvgRun], axis=1)
        belief_averages.fillna(method='ffill', inplace=True)

        xPos = []
        yPos = []
        xIndex = 0
        yIndex = 1
        for i in range(num_robots):
            xPos = np.append(xPos, (posData.loc[:, pos_column_names[xIndex]]).to_list(), axis=0)
            yPos = np.append(yPos, (posData.loc[:, pos_column_names[yIndex]]).to_list(), axis=0)
            xIndex = xIndex + 2
            yIndex = yIndex + 2
        
    
    return belief_averages, time_averages

plt.style.use('seaborn-talk')

#Evaluate parameters from baseline
belief_averages_best, time_averages_best = readBaseline(baselinedir_best)
belief_averages, time_averages_median = readBaseline(baselinedir_median)
#createSTD(belief_averages)
decTimeBins(time_averages_best, time_averages_median)

# ADD PLOT TITLES
#Evaluate PSO Fitness Values
# readFitness()
# psoFitnessScatter()
