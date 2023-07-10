import csv
import numpy as np
import seaborn as sns
from scipy import stats, integrate
import matplotlib.pyplot as plt
from matplotlib import image
import pandas
from scipy.stats import gaussian_kde
import os
import time

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
fitness_run_xo = np.empty(num_batch) #Describes the fitness of each batch launch
fitness_run_p = np.empty(num_batch)
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
time_run_p = []
time_run_xo = []
home_dir = os.getcwd() + "/../.."
p_c = 0.5

for i in range(n_robots):
    prob_column_names.append('rov_{}'.format(i))
    pos_column_names.append('rov_{}_x'.format(i))
    pos_column_names.append('rov_{}_y'.format(i))

def belief_distribution(cov_avg, cov_std, belief_avg, belief_std, cov_avg_p, cov_std_p, belief_avg_p, belief_std_p):
    print("xo coverage: ", len(cov_avg))
    print("p coverage average: ", len(cov_avg_p))
    # sns.set_style("ticks")
    fig=plt.figure()
    plt.grid()
    ax=fig.add_subplot(111, label="1")
    ax2=fig.add_subplot(111, label="2", frame_on=False)

    ax.set_xlabel("Observations", color="k")
    ax.set_ylabel("Coverage", color="k")
    ax.set_ylim(0,1.1)
    ax.tick_params(axis='x', colors="k")
    ax.tick_params(axis='y', colors="k")
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')
    ax2.yaxis.tick_right()
    ax2.set_ylim(0,1.1)
    ax2.set_xlabel('Simulation Time Steps', color="k") 
    ax2.set_ylabel('Average Belief', color="k")       
    ax2.xaxis.set_label_position('top') 
    ax2.yaxis.set_label_position('right') 
    ax2.tick_params(axis='x', colors="k")
    ax2.tick_params(axis='y', colors="k")
    ax2.xaxis.tick_bottom()
    ax2.xaxis.set_label_position('bottom') 

    #Coverage data is plotted on ax
    #Belief data is plotted on ax2

    #Plot x0 coverage
    ax.plot(np.arange(len(cov_avg)), cov_avg, color="b")
    bottom = np.subtract(cov_avg, cov_std)
    bottom[bottom<0] = 0
    ax.fill_between(np.arange(len(cov_avg)), bottom, np.add(cov_avg, cov_std), color='b', alpha=0.3)

    #Plot xp coverage
    ax.plot(np.arange(len(cov_avg_p)), cov_avg_p, color="r")
    bottom = np.subtract(cov_avg_p, cov_std_p)
    bottom[bottom<0] = 0
    ax.fill_between(np.arange(len(cov_avg_p)), bottom, np.add(cov_avg_p, cov_std_p), color='r', alpha=0.3)
    
    #Plot x0 belief
    ax2.plot(np.arange(len(belief_avg)), belief_avg, color="b", label='Empirical')
    bottom = np.subtract(belief_avg, belief_std)
    bottom[bottom<0] = 0
    ax2.fill_between(np.arange(len(belief_avg)), bottom, np.add(belief_avg, belief_std), color='b', alpha=0.3)

    #Plot xp belief
    ax2.plot(np.arange(len(belief_avg_p)), belief_avg_p, color="r", label='Optimized')
    bottom = np.subtract(belief_avg_p, belief_std_p)
    bottom[bottom<0] = 0
    ax2.fill_between(np.arange(len(belief_avg_p)), bottom, np.add(belief_avg_p, belief_std_p), color='r', alpha=0.3)

    ax2.axhline(y=p_c, color='k', linestyle='--', alpha=0.5)
    # ax2.axhline(y=1-p_c, color='k', linestyle='--', alpha=0.5)

    ax2.legend()
    plt.show()
    fig.savefig(home_dir + "/../" + folderName + "/cov_belief_distribution.svg", format='svg', dpi='figure')

def cov_belief(cov_count, cov_avg, cov_std, belief_avg, belief_std):
    """
    This function graphs the average belief and coverage of all robots throughout 100 simulation runs.
    """
    fig=plt.figure()
    ax=fig.add_subplot(111, label="1")
    ax2=fig.add_subplot(111, label="2", frame_on=False)
    # h = fig.add_subplot(212, label="3", projection='3d')

    ax.plot(np.arange(len(cov_avg)), cov_avg, color="C0")
    bottom = np.subtract(cov_avg, cov_std)
    bottom[bottom<0] = 0
    ax.fill_between(np.arange(len(cov_avg)), bottom, np.add(cov_avg, cov_std), color='C0', alpha=0.3)
    ax.set_xlabel("Observations", color="C0")
    ax.set_ylabel("Coverage", color="C0")
    ax.set_ylim(0,1)
    ax.tick_params(axis='x', colors="C0")
    ax.tick_params(axis='y', colors="C0")
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top') 

    ax2.plot(np.arange(len(belief_avg)), belief_avg, color="C1")
    bottom = np.subtract(belief_avg, belief_std)
    bottom[bottom<0] = 0
    ax2.fill_between(np.arange(len(belief_avg)), bottom, np.add(belief_avg, belief_std), color='C1', alpha=0.3)
    ax2.axhline(y=p_c, color='r', linestyle='--', alpha=0.5)
    # ax2.axhline(y=1-p_c, color='r', linestyle='--', alpha=0.5)
    ax2.xaxis.tick_top()
    ax2.yaxis.tick_right()
    ax2.set_ylim(0,1)
    ax2.set_xlabel('Average Simulation Time (s)', color="C1") 
    ax2.set_ylabel('Average Belief', color="C1")       
    ax2.xaxis.set_label_position('top') 
    ax2.yaxis.set_label_position('right') 
    ax2.tick_params(axis='x', colors="C1")
    ax2.tick_params(axis='y', colors="C1")
    ax2.xaxis.tick_bottom()
    ax2.xaxis.set_label_position('bottom') 

    plt.show()
    fig.savefig(home_dir + "/../" + folderName + "/cov_belief.png", format='png', dpi='figure')

def hist_coveage(obs_run):
    # fig=plt.figure()
    fig=plt.figure(figsize=(6,6))
    x = []
    y = []

    for run in obs_run:
        x.append(run[0])
        y.append(run[1])
    
    # import plotly.express as px
    # print(x[0])
    # print(y[0])
    observations = pandas.DataFrame({'x_obs': x[0], 'y_obs': y[0]})
    plt.xlim([0,1])
    plt.ylim([0,1])
    # print(observations)
    grid_points = np.arange(0,1+1/(pic_dim/square_size),1/(pic_dim/square_size))
    # df = px.data.tips()
    # fig = px.density_heatmap(df, x="total_bill", y="tip", text_auto=True)
    # fig = px.density_heatmap(df, x=x[0], y=y[0], nbinsx=int(pic_dim/square_size), nbinsy=int(pic_dim/square_size),text_auto=True)
    sns.histplot(observations, x="x_obs", y="y_obs", zorder=0, cbar=True, bins=list(np.arange(0,1+1/(pic_dim/square_size),1/(pic_dim/square_size))))
    # sns.scatterplot(x=x[0], y=y[0], size=0.5,color='black', edgecolors='black', alpha=0.5, legend=False)
    # fig.show()
    
    plt.xticks(grid_points)
    plt.yticks(grid_points)
    plt.gca().tick_params(axis='y', colors='white')
    plt.gca().tick_params(axis='x', colors='white')
    plt.xlabel("Arena X (m)")
    plt.ylabel("Arena Y (m)")
    plt.title("Observation Binnings")

    plt.grid()
    plt.show()


#################################### Gaussian Heat Map #############################
# From this: https://zbigatron.com/generating-heatmaps-from-coordinates/ and https://stackoverflow.com/questions/50091591/plotting-seaborn-heatmap-on-top-of-a-background-picture
def kde_coverage(obs_run):
    fig=plt.figure(figsize=(6,6))
    # sns.set_style("darkgrid", {"grid.color": ".6", "grid.linestyle": ":"})
    grid_points = np.arange(0,1,1/(pic_dim/square_size))
    plt.xticks(grid_points)
    plt.yticks(grid_points)
    plt.gca().tick_params(axis='y', colors='white')
    plt.gca().tick_params(axis='x', colors='white')
    plt.xlim([0,1])
    plt.ylim([0,1])
    plt.title("Observation Heatmap")
    x = []
    y = []
    for run in obs_run:
        x.append(run[0])
        y.append(run[1])
    print("Number of obs: " + str(len(x[0])))
    #bw_adjusted=0.9
    sns.kdeplot(x=x[0], y=y[0], fill=True, zorder=0, cmap=sns.color_palette("magma", as_cmap=True))
    # sns.scatterplot(x=x[0], y=y[0], size=1,color='black', edgecolors='black', alpha=0.5, legend=False)
    plt.grid()
    plt.show()
    fig.savefig(home_dir + "/../" + folderName + "/kde_coverage.svg", format='svg', dpi='figure')

def time_distribution(time_run_one, time_run_two):
    fig, ax = plt.subplots()
    time_average_run_one = []
    time_average_run_two = []

    for run in time_run_one:
        time_average_run_one.append(sum(run) / len(run))

    for run in time_run_two:
        time_average_run_two.append(sum(run) / len(run))

    ax.hist(time_average_run_one, color='lightblue', edgecolor='black', alpha=0.5, label='Empirical Parameters')
    ax.hist(time_average_run_two, color='salmon', edgecolor='black', alpha=0.5, label='Optimized Parameters')
    ax.set_title("Average Swarm Decision Times")
    ax.set_xlabel("Simulation Time (s)")
    ax.legend()
    ax.set_ylabel("Absolute Frequency")
    plt.show()
    fig.savefig(home_dir + "/../" + folderName + "/time_distribution.svg", format='svg', dpi='figure')

def fitness_distribution(fitness_run_one, fitness_run_two):
    fig, ax = plt.subplots()

    ax.hist(fitness_run_one, color='lightblue', edgecolor='black', alpha=0.5, label='Empirical Parameters')
    ax.hist(fitness_run_two, color='salmon', edgecolor='black', alpha=0.5, label='Optimized Parameters')
    ax.set_title("Swarm Fitness Distributions")
    ax.set_xlabel("Fitness")
    ax.legend()
    ax.set_ylabel("Absolute Frequency")
    plt.show()
    fig.savefig(home_dir + "/../" + folderName + "/fitness_distribution.svg", format='svg', dpi='figure')

def single_belief(belief_avg, belief_std):
    fig=plt.figure()
    plt.grid()
    plt.plot(np.arange(len(belief_avg)), belief_avg, color="b", label='Empirical')
    bottom = np.subtract(belief_avg, belief_std)
    bottom[bottom<0] = 0
    plt.fill_between(np.arange(len(belief_avg)), bottom, np.add(belief_avg, belief_std), color='b', alpha=0.3)
    plt.show()

def read_data(folderName, time_run, fitness_run, reset_run, pos_x_run, pos_y_run, belief_run, obs_run, cov_count, cov_avg, cov_std):
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
        
        obs_run[run, 0] = obsData["x"].tolist()
        obs_run[run, 1] = obsData["y"].tolist()

        decTimeFile = home_dir + '/../' + folderName + '/Run' + str(run) + '/decTime.txt'
        with open(decTimeFile) as f:
            lines = f.read().splitlines()
        fitness_run[run] = float(lines[4])
        reset_run[run] = float(lines[5])
        pos_run.append(posData)
        time_run.append([float(i) for i in lines[0:3]])

        swarm_bel_avg[str(run)] = beliefData.mean(axis=1)
    
    swarm_bel_avg.to_csv('swarm_bel_avg.csv')
    #Belief average and standard deviation
    belief_avg = swarm_bel_avg.mean(axis=1)
    belief_std = swarm_bel_avg.std(axis=1)
    # print(belief_avg)
    # print(swarm_bel_avg)

    #Store the arena coverage
    batch_calc = range(num_batch)
    cov_avg = []
    cov_std = []
    for time in range(1, len(obs_run[0, 0]), 1):
        # print(time /len(obs_run[0, 0]) )
        cov = 0
        std_arr = np.empty(num_batch)
        # bel = 0
        for run in batch_calc:
            # print("Calculating Run: ", run)
            #Place observations into binnings based on tiles
            cov_t = (stats.binned_statistic_2d(obs_run[run, 0][:time], obs_run[run, 1][:time],
                    values=None,statistic='count',bins=[np.arange(0,1+distance_per_square,distance_per_square),
                        np.arange(0,1+distance_per_square,distance_per_square)],expand_binnumbers='True')).statistic
            #Convert counts into binary values
            cov_count = np.add(cov_count, cov_t)
            cov_bin = np.where(cov_t > 0, 1, 0)
            #Calculate Average coverage
            cov = cov + (np.sum(cov_bin)/(squares_per_side * squares_per_side))
            # print(cov_count)
            # if ((np.sum(cov_bin)/(squares_per_side * squares_per_side)) < 1) and (time > len(obs_run[0, 0])*0.95):
            #     print("Run: ", run)
            #     print(cov_bin)
            # if (np.sum(cov_bin)/(squares_per_side * squares_per_side) >= 1):
            #     print("Coverage Reached: ", cov)
            #     del batch_calc[run]
            #     break
            std_arr[run] = (np.sum(cov_bin)/(squares_per_side * squares_per_side))

        cov_avg.append(cov/num_batch)
        cov_std.append(np.std(std_arr))

    cov_avg = np.asarray(cov_avg)
    cov_std = np.asarray(cov_std)
    belief_avg = np.asarray(belief_avg)
    belief_std = np.asarray(belief_std)

    return time_run, fitness_run, reset_run, pos_x_run, pos_y_run, belief_run, belief_avg, belief_std, obs_run, np.divide(cov_count,num_batch), cov_avg, cov_std

sns.set_theme(style="white", palette=None)
cmap =sns.color_palette("Blues", as_cmap=True)

folderName = "ICRA_DATA/xo_baseline/Log"
time_run_xo, fitness_run_xo, reset_run, pos_x_run, pos_y_run, belief_run, belief_avg_xo, belief_std_xo, obs_run, cov_count, cov_avg_xo, cov_std_xo = read_data(folderName, time_run_xo, fitness_run_xo, reset_run, pos_x_run, pos_y_run, belief_run, obs_run, cov_count, cov_avg, cov_std)
# folderName = "ICRA_DATA/p_95_baseline/Log"
# time_run_p, fitness_run_p, reset_run, pos_x_run, pos_y_run, belief_run, belief_avg_p, belief_std_p, obs_run, cov_count_p, cov_avg_p, cov_std_p = read_data(folderName, time_run_p, fitness_run_p, reset_run, pos_x_run, pos_y_run, belief_run, obs_run, cov_count, cov_avg, cov_std)

# time_distribution(time_run_xo, time_run_p)
# fitness_distribution(fitness_run_xo, fitness_run_p)
#belief_distribution(cov_avg_xo, cov_std_xo, belief_avg_xo, belief_std_xo, cov_avg_p, cov_std_p, belief_avg_p, belief_std_p)
start = time.time()
cov_belief(cov_count, cov_avg_xo, cov_std_xo, belief_avg_xo, belief_std_xo)
end = time.time()
print(end - start)
# kde_coverage(obs_run)
# hist_coveage(obs_run)

# single_belief(belief_avg_xo, belief_std_xo)