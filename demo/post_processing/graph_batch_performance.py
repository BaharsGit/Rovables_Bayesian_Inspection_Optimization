import csv
import numpy as np
import seaborn as sns
from scipy import stats, integrate
import matplotlib.pyplot as plt
from matplotlib import image
import pandas
from scipy.stats import gaussian_kde
import os

#Simulation constants
n_robots = 4
savePlots = 1
pic_dim=128
square_size=8
squares_per_side=int(pic_dim/square_size)
arena_squares = np.empty([squares_per_side, squares_per_side])
distance_per_square = 1/squares_per_side


#Data structures used to graph and store data
num_batch = 100 # This dictates the number of batch launches used.
fitness_run = np.empty(num_batch) #Describes the fitness of each batch launch
reset_run = np.empty(num_batch) #Describes the number of times the robots reset at each batch launch
pos_x_run = np.empty((num_batch, n_robots), object) #Describes the positions at each run: Position log of Robot 2 in Run 7 is pos_x_run[7, 2]
pos_y_run = np.empty((num_batch, n_robots), object) #Describes the positions at each run
belief_run = np.empty((num_batch, n_robots), object) #Describes the belief at each run
cov_count = np.zeros((squares_per_side, squares_per_side))
obs_run = np.empty((num_batch, 2), object) #Describes which positions were observed per run
cov_avg = []
cov_std = []
x_total = [] #Describes the total x positions over all bacth runs
y_total = [] #Describes the total y positions over all batch runs
prob_column_names = [] #Format for describing the robots
pos_column_names = [] #Format for describing the robots
averages = pandas.DataFrame()
pos_column_names.append('time_step')
pos_run = []
home_dir = os.getcwd() + "/../.."
folderName = "Log_x0"

for i in range(n_robots):
    prob_column_names.append('rov_{}'.format(i))
    pos_column_names.append('rov_{}_x'.format(i))
    pos_column_names.append('rov_{}_y'.format(i))

def cov_belief(cov_count, cov_avg, cov_std, belief_avg, belief_std):

    fig=plt.figure()
    ax=fig.add_subplot(211, label="1")
    ax2=fig.add_subplot(211, label="2", frame_on=False)
    h = fig.add_subplot(212, label="3", projection='3d')

    ax.plot(np.arange(len(cov_avg)), cov_avg, color="C0")
    bottom = np.subtract(cov_avg, cov_std)
    bottom[bottom<0] = 0
    ax.fill_between(np.arange(len(cov_avg)), bottom, np.add(cov_avg, cov_std), color='C0', alpha=0.3)
    ax.set_xlabel("Observations", color="C0")
    ax.set_ylabel("Coverage", color="C0")
    ax.set_ylim(0,1)
    ax.tick_params(axis='x', colors="C0")
    ax.tick_params(axis='y', colors="C0")

    ax2.plot(np.arange(len(belief_avg)), belief_avg, color="C1")
    bottom = np.subtract(belief_avg, belief_std)
    bottom[bottom<0] = 0
    ax2.fill_between(np.arange(len(belief_avg)), bottom, np.add(belief_avg, belief_std), color='C1', alpha=0.3)
    ax2.xaxis.tick_top()
    ax2.yaxis.tick_right()
    ax2.set_ylim(0,1)
    ax2.set_xlabel('Simulation Time', color="C1") 
    ax2.set_ylabel('Belief', color="C1")       
    ax2.xaxis.set_label_position('top') 
    ax2.yaxis.set_label_position('right') 
    ax2.tick_params(axis='x', colors="C1")
    ax2.tick_params(axis='y', colors="C1")

    # Using this corresponding post: https://stackoverflow.com/questions/14061061/how-can-i-render-3d-histograms-in-python
    data_array = np.array(cov_count)
    #
    # Create an X-Y mesh of the same dimension as the 2D data. You can
    # think of this as the floor of the plot.
    #
    x_data, y_data = np.meshgrid(np.arange(data_array.shape[1]),
                                np.arange(data_array.shape[0]) )
    #
    # Flatten out the arrays so that they may be passed to "ax.bar3d".
    # Basically, ax.bar3d expects three one-dimensional arrays:
    # x_data, y_data, z_data. The following call boils down to picking
    # one entry from each array and plotting a bar to from
    # (x_data[i], y_data[i], 0) to (x_data[i], y_data[i], z_data[i]).
    #
    x_data = x_data.flatten()
    y_data = y_data.flatten()
    z_data = data_array.flatten()
    h.bar3d(x_data,
            y_data,
            np.zeros(len(z_data)),
            1, 1, z_data )
    # h.hist2d(x_data, y_data, cmap=plt.cm.jet)
    plt.show()

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

print(home_dir)


def read_data(fitness_run, reset_run, pos_x_run, pos_y_run, belief_run, obs_run, cov_count, cov_avg, cov_std):
    #Iterate through and save data into corresponding arrays
    swarm_bel_avg = pandas.DataFrame() #I believe it is more efficient when storing in a dataframe 
    for run in range(num_batch):
        posData = []
        posFile = home_dir + '/../' + folderName + '/Run' + str(run) + '/runPos.csv'
        beliefFile = home_dir + '/../' + folderName + '/Run' + str(run) + '/runProb.csv'
        obsFile = home_dir + '/../' + folderName + '/Run' + str(run) + '/observation_log.txt'
        posData = pandas.read_csv(posFile, names=pos_column_names)
        beliefData = pandas.read_csv(beliefFile, names=prob_column_names)
        obsData = pandas.read_csv(obsFile, names=["x", "y"])
        for robot in range(n_robots):
            pos_x_run[run, robot] = posData['rov_{}_x'.format(i)].values.tolist()
            pos_y_run[run, robot] = posData['rov_{}_y'.format(i)].values.tolist()
            belief_run[run, robot] = beliefData['rov_{}'.format(i)].values.tolist()
        
        obs_run[run, 0] = obsData["x"]
        obs_run[run, 1] = obsData["y"]

        decTimeFile = home_dir + '/../' + folderName + '/Run' + str(run) + '/decTime.txt'
        with open(decTimeFile) as f:
            lines = f.read().splitlines()
        fitness_run[run] = float(lines[4])
        reset_run[run] = float(lines[5])
        pos_run.append(posData)

        swarm_bel_avg[str(run)] = beliefData.mean(axis=1)
    
    #Belief average and standard deviation
    belief_avg = swarm_bel_avg.mean(axis=1)
    belief_std = swarm_bel_avg.std(axis=1)

    #Store the arena coverage

    for time in range(1, len(obs_run[0, 0]), 1):
        cov = 0
        std_arr = np.empty(num_batch)
        # bel = 0
        for run in range(num_batch):
            #Place observations into binnings based on tiles
            cov_t = (stats.binned_statistic_2d(obs_run[run, 0][:time], obs_run[run, 1][:time],
                    values=None,statistic='count',bins=[np.arange(0,1+distance_per_square,distance_per_square),
                        np.arange(0,1+distance_per_square,distance_per_square)],expand_binnumbers='True')).statistic
            #Convert counts into binary values
            cov_count = np.add(cov_count, cov_t)
            cov_bin = np.where(cov_t > 0, 1, 0)
            #Calculate Average coverage
            cov = cov + (np.sum(cov_bin)/(squares_per_side * squares_per_side))
            if ((np.sum(cov_bin)/(squares_per_side * squares_per_side)) < 1) and (time > len(obs_run[0, 0])*0.95):
                print("Run: ", run)
                print(cov_bin)
            std_arr[run] = (np.sum(cov_bin)/(squares_per_side * squares_per_side))

        cov_avg.append(cov/num_batch)
        cov_std.append(np.std(std_arr))

    cov_avg = np.asarray(cov_avg)
    cov_std = np.asarray(cov_std)
    belief_avg = np.asarray(belief_avg)
    belief_std = np.asarray(belief_std)

    return fitness_run, reset_run, pos_x_run, pos_y_run, belief_run, belief_avg, belief_std, obs_run, np.divide(cov_count,num_batch), cov_avg, cov_std


fitness_run, reset_run, pos_x_run, pos_y_run, belief_run, belief_avg, belief_std, obs_run, cov_count, cov_avg, cov_std = read_data(fitness_run, reset_run, pos_x_run, pos_y_run, belief_run, obs_run, cov_count, cov_avg, cov_std)
# print(cov_count)
cov_belief(cov_count, cov_avg, cov_std, belief_avg, belief_std)