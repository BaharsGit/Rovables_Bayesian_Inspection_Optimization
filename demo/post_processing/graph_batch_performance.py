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
# baseline_folder_names = ["nofb_empirical", "nofb_optimized", "fb_empirical","fb_optimized"]
baseline_folder_names = ["dynamic_empirical", "dynamic_10noise", "dynamic_15noise"]
# fill_ratios = [0.40, 0.48, 0.52, 0.60]
# fill_ratios = [0.52]
fill_ratios = [6040]
num_baseline = len(baseline_folder_names)
fitness_batch = np.empty([num_baseline, len(fill_ratios), num_batch]) #Describes the fitness of each batch launch
fitness_run = np.empty(num_batch)
belief_batch = np.empty([num_baseline, len(fill_ratios), num_batch, 4])

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
home_dir = os.getcwd()
p_c = 0.95

for i in range(n_robots):
    prob_column_names.append('rov_{}'.format(i))
    pos_column_names.append('rov_{}_x'.format(i))
    pos_column_names.append('rov_{}_y'.format(i))

def belief_distribution(cov_avg, cov_std, belief_avg, belief_std):
    csfont = {'fontname':'Times New Roman'}
    sns.set_palette("pastel")
    # sns.set_style("ticks")
    fig=plt.figure()
    # ax_cov=fig.add_subplot(111, label="1")
    ax_belief=fig.add_subplot(111)

    # ax_cov.set_xlabel("Observations", color="k")
    # ax_cov.set_ylabel("Coverage", color="k")
    # ax_cov.set_ylim(0,1.1)
    # ax_cov.tick_params(axis='x', colors="k")
    # ax_cov.tick_params(axis='y', colors="k")
    # ax_cov.xaxis.tick_top()
    # ax_cov.xaxis.set_label_position('top')
    # ax_belief.yaxis.tick_right()
    ax_belief.set_xlabel('Simulation Time Steps') 
    ax_belief.set_ylabel('Average Belief')       
    # ax_belief.xaxis.set_label_position('top') 
    # ax_belief.yaxis.set_label_position('right') 
    # ax_belief.tick_params(axis='x', colors="k")
    # ax_belief.tick_params(axis='y', colors="k")
    # ax_belief.xaxis.tick_bottom()
    # ax_belief.xaxis.set_label_position('bottom') 

    #Coverage data is plotted on ax
    #Belief data is plotted on ax2

    # for i in range(len(cov_avg)):
    #     #Plot x0 coverage
    #     print(cov_avg[i])
    #     sns.lineplot(cov_avg[i], ax=ax_cov, label=baseline_folder_names[i])
    #     bottom = np.subtract(cov_avg[i], cov_std[i])
    #     bottom[bottom<0] = 0
    #     # ax_cov.fill_between(np.arange(len(cov_avg[i])), bottom, np.add(cov_avg[i], cov_std[i]), alpha=0.3)

    for i in range(num_baseline):
        print(len(belief_avg[i]))
        #Plot x0 belief
        sns.lineplot(belief_avg[i], ax=ax_belief, label=baseline_folder_names[i])
        bottom = np.subtract(belief_avg[i], belief_std[i])
        bottom[bottom<0] = 0
        ax_belief.fill_between(np.arange(len(belief_avg[i])), bottom, np.add(belief_avg[i], belief_std[i]), alpha=0.4)

    # ax_belief.axhline(y=p_c, color='k', linestyle='--', alpha=0.5)
    # ax_belief.axhline(y=1-p_c, color='k', linestyle='--', alpha=0.5)
    sns.despine(bottom=True, left=True)
    plt.grid()
    ax_belief.set_title("Average Swarm Beliefs for Dynamic Fill Ratio",**csfont)
    ax_belief.legend()
    plt.show()
    
    fig.savefig(home_dir + "/../../" + folderName + "/cov_belief_distribution.png", format='png', dpi='figure')

def scatter_fitness(fitness_runs):
    sns.set_palette("pastel")
    sns.set_style({'axes.facecolor':'white', 'grid.color': '.8', 'font.family':'Times New Roman'})
    fig, ax_list = plt.subplots(nrows=1, ncols=num_baseline, sharey=True)
    i = 0
    titles = ["40%", "48%", "52%", "60%"]
    for ax in ax_list:
        j=1
        print(fitness_runs[i])
        # ax.boxplot(fitness_runs[i], positions=[0,1,2,3], showcaps=False, showfliers = False)
        data = []
        for baseline_type in fitness_runs:
            # sns.violinplot(x=j, y=baseline_type[i], ax=ax)
            data.append(baseline_type[i])
            sns.scatterplot(x=np.random.uniform(j-0.2,j+0.2,len(baseline_type[i])), y=baseline_type[i], ax=ax, s=18)
            j=j+1
        ax.boxplot(data, showfliers=False, medianprops = dict(color = "purple", linewidth = 1.5))
        ax.set_title('Fill Ratio: ' + titles[i])
        ax.set_xticks([])
        ax.grid()
        ax.set_ylim(0, 17000)
        plt.grid()
        # ax.set_xticklabels(baseline_folder_names, rotation=45)

        # plt.xticks(range(len(t11)), t11, size='small')

        i=i+1
    # fig.legend(baseline_folder_names, loc='lower right', bbox_to_anchor=(1,-0.1), ncol=len(labels), bbox_transform=fig.transFigure)
    fig.legend(baseline_folder_names, ncol=len(baseline_folder_names), loc='lower center')
    sns.despine(bottom=True, left=True)
    plt.show()

    fig.savefig(home_dir + "/../../" + folderName + "/box_scatter_error.svg", format='svg', dpi='figure', bbox_inches='tight')
def binned_scatter_fitness(fitness_runs):
    """
    Iterate through fitness_runs a n*m array where n is the number of baselines and m is the number of different fill ratios. 
    """
    fig = plt.figure(figsize=(14,8))

    fills = np.array([0.4, 0.48, 0.52, 0.6])
    colors = ["red", "blue", "orange", "green"]
    ax_scatter = fig.add_subplot(111)
    ax_scatter.set_title("Fitness Distributions")
    ax_scatter.set_xlabel("Fill Ratio")
    ax_scatter.set_ylabel("Fitness")
    ax_scatter.set_ylim(0, 20000)

    for i in range(len(fitness_runs)):
        fit_mean = []
        fit_err = []
        fit_sum = []

        for fill in fitness_runs[i]:
            fit_mean.append(np.mean(fill))
            fit_err.append(np.std(fill))
            fit_sum.append(np.mean(fill))
        
        print("Average fitnesses: ", fit_mean)
        print("Avg + Std: ", fit_sum)
        # ax_scatter.errorbar(fills, fit_sum, yerr=fit_err, c=colors[i], fmt="o", alpha=0.3, label=baseline_folder_names[i])
        # ax_scatter.boxplot(x=fit_mean, positions=fills, patch_artist = True, boxprops = dict(facecolor = colors[i]), labels=baseline_folder_names[i])
        sns.scatterplot(x=fills, y=fit_sum, c=colors[i], marker='s', label=baseline_folder_names[i], ax=ax_scatter)
    ax_scatter.grid()
    ax_scatter.set_xticks([0.38, 0.4, 0.48, 0.52, 0.6, 0.68])
    ax_scatter.legend()

    sns.despine(bottom=True, left=True)
    plt.show()
    fig.savefig(home_dir + "/../../" + folderName + "/scatter_error.svg", format='svg', dpi='figure')

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

def fitness_distribution(fitness_runs):
    csfont = {'fontname':'Times New Roman'}
    sns.set_palette("pastel")

    fig, (ax_bar_1, ax_bar_2) = plt.subplots(1, 2, figsize=(7, 5))
    fig_dyn, (dyn_bar) = plt.subplots(1, 1, figsize=(7, 6))
    fills = np.array([0.4, 0.48, 0.52, 0.6])
    colors = ["red", "blue", "orange", "green"]
    i = 0
    # for run in fitness_runs:
    #     sns.histplot(run[1], ax=ax_bar_1, binwidth=1000, label=baseline_folder_names[i])
    #     i = i + 1
    # for run in fitness_runs[2:]:
    #     sns.histplot(run[1], ax=ax_bar_2, binwidth=1000, label=baseline_folder_names[i])
        # i = i + 1
    graph_data = []        
    hist, bins = np.histogram(fitness_runs[0][0])
    logbins = np.logspace(np.log10(bins[0]),np.log10(bins[-1]),len(bins))
    for run in fitness_runs:
        graph_data.append(run[0])   
        sns.histplot(run[0], bins=logbins, ax=dyn_bar, edgecolor='k', linewidth=1.5, label=baseline_folder_names[i], alpha=0.4)
        i = i + 1

    # sns.histplot(graph_data, bins=logbins, ax=dyn_bar, multiple="stack")
    # sns.histplot(graph_data, ax=dyn_bar)

    # ax.hist(fitness_run_one, color='lightblue', edgecolor='black', alpha=0.5, label='Empirical Parameters')
    # ax.hist(fitness_run_two, color='salmon', edgecolor='black', alpha=0.5, label='Optimized Parameters')
    fig.suptitle("Swarm Fitness Distributions for Dynamic Fill Ratio",**csfont)
    fig.supylabel('Frequency')
    fig.supxlabel('Simulation Evaluations, $e$')
    dyn_bar.set_title("Swarm Fitness Distributions for Dynamic Fill Ratio")
    fig_dyn.supylabel('Frequency')
    fig_dyn.supxlabel('Simulation Evaluations, $e$')
    # ax_fit_bar.set_xlabel("Fitness")
    # ax_fit_bar.set_ylabel("Absolute Frequency")
    ax_bar_1.set(ylabel=None)
    ax_bar_2.set(ylabel=None)
    dyn_bar.set(ylabel=None)
    ax_bar_1.legend()
    ax_bar_2.legend()
    dyn_bar.legend()
    # dyn_bar.legend(labels=baseline_folder_names)
    plt.xscale('log')
    # plt.yticks(np.arange(0, num_batch, 10))
    plt.grid()
    sns.despine(bottom=True, left=True)
    plt.show()
    fig_dyn.savefig(home_dir + "/../../" + folderName + "/evaluation_distribution_dynamic.svg", format='svg', dpi='figure')
    fig.savefig(home_dir + "/../../" + folderName + "/evaluation_distribution_static.svg", format='svg', dpi='figure')

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
        posFile = home_dir + '/../../' + folderName + '/Run' + str(run) + '/runPos.csv'
        beliefFile = home_dir + '/../../' + folderName + '/Run' + str(run) + '/runProb.csv'
        # obsFile = home_dir + '/../../' + folderName + '/Run' + str(run) + '/observation_log.txt'
        posData = pandas.read_csv(posFile, names=pos_column_names)
        beliefData = pandas.read_csv(beliefFile, names=prob_column_names)
        # obsData = pandas.read_csv(obsFile, names=["x", "y"])
        for robot in range(n_robots):
            pos_x_run[run, robot] = posData['rov_{}_x'.format(i)].values.tolist()
            pos_y_run[run, robot] = posData['rov_{}_y'.format(i)].values.tolist()
            belief_run[run, robot] = beliefData['rov_{}'.format(i)].values.tolist()
        
        # obs_run[run, 0] = obsData["x"].tolist()
        # obs_run[run, 1] = obsData["y"].tolist()

        decTimeFile = home_dir + '/../../' + folderName + '/Run' + str(run) + '/decTime.txt'
        with open(decTimeFile) as f:
            lines = f.read().splitlines()
        fitness_run[run] = float(lines[4])
        reset_run[run] = float(lines[5])
        pos_run.append(posData)
        time_run.append([float(i) for i in lines[0:3]])

        swarm_bel_avg[str(run)] = beliefData.mean(axis=1)
    
    # swarm_bel_avg.to_csv('swarm_bel_avg.csv')
    #Belief average and standard deviation
    belief_avg = swarm_bel_avg.mean(axis=1)
    belief_std = swarm_bel_avg.std(axis=1)
    # print(belief_avg)
    # print(swarm_bel_avg)

    #Store the arena coverage
    batch_calc = range(num_batch)
    # cov_avg = []
    # cov_std = []
    # for time in range(1, len(obs_run[0, 0]), 1):
    #     # print(time /len(obs_run[0, 0]) )
    #     cov = 0
    #     std_arr = np.empty(num_batch)
    #     # bel = 0
    #     for run in batch_calc:
    #         # print("Calculating Run: ", run)
    #         #Place observations into binnings based on tiles
    #         cov_t = (stats.binned_statistic_2d(obs_run[run, 0][:time], obs_run[run, 1][:time],
    #                 values=None,statistic='count',bins=[np.arange(0,1+distance_per_square,distance_per_square),
    #                     np.arange(0,1+distance_per_square,distance_per_square)],expand_binnumbers='True')).statistic
    #         #Convert counts into binary values
    #         cov_count = np.add(cov_count, cov_t)
    #         cov_bin = np.where(cov_t > 0, 1, 0)
    #         #Calculate Average coverage
    #         cov = cov + (np.sum(cov_bin)/(squares_per_side * squares_per_side))
    #         # print(cov_count)
    #         # if ((np.sum(cov_bin)/(squares_per_side * squares_per_side)) < 1) and (time > len(obs_run[0, 0])*0.95):
    #         #     print("Run: ", run)
    #         #     print(cov_bin)
    #         # if (np.sum(cov_bin)/(squares_per_side * squares_per_side) >= 1):
    #         #     print("Coverage Reached: ", cov)
    #         #     del batch_calc[run]
    #         #     break
    #         std_arr[run] = (np.sum(cov_bin)/(squares_per_side * squares_per_side))

    #     cov_avg.append(cov/num_batch)
    #     cov_std.append(np.std(std_arr))

    cov_avg = np.asarray(cov_avg)
    cov_std = np.asarray(cov_std)
    belief_avg = np.asarray(belief_avg)
    belief_std = np.asarray(belief_std)

    return time_run, fitness_run, reset_run, pos_x_run, pos_y_run, belief_run, belief_avg, belief_std, obs_run, np.divide(cov_count,num_batch), cov_avg, cov_std


sns.set_style({'axes.facecolor':'white', 'grid.color': '.8', 'font.family':'Times New Roman'})
# sns.set_theme(style='white', palette=None)
np.set_printoptions(suppress=True)
plt.rcParams.update({'font.size': 14})
cmap =sns.color_palette("Blues", as_cmap=True)
print(home_dir)

belief_batch_avg = []
belief_batch_std = []
cov_batch_std = []
cov_batch_avg = []
for i in range(num_baseline):
    for j in range(len(fill_ratios)):
        # folderName = "paper_data/baseline/" + baseline_folder_names[i] + "/"  + str(int(100*fill_ratios[j])) + "/Log"
        folderName = "paper_data/baseline/" + baseline_folder_names[i] + "/6040"  + "/Log"
        data_out = read_data(folderName, time_run_xo, fitness_run, reset_run, pos_x_run, pos_y_run, belief_run, obs_run, cov_count, cov_avg, cov_std)
        fitness_batch[i, j] = data_out[1]
        belief_batch_avg.append(data_out[6])
        belief_batch_std.append(data_out[7])
        cov_batch_std.append(data_out[10])
        cov_batch_avg.append(data_out[11])

# print(fitness_batch)
# folderName = "paper_data/baseline/fb_optimized/48/Log"
# time_run_p, fitness_run_48, reset_run, pos_x_run, pos_y_run, belief_run, belief_avg_p, belief_std_p, obs_run, cov_count_p, cov_avg_p, cov_std_p = read_data(folderName, time_run_p, fitness_run_48, reset_run, pos_x_run, pos_y_run, belief_run, obs_run, cov_count, cov_avg, cov_std)
# folderName = "paper_data/baseline/fb_optimized/52/Log"
# time_run_xo, fitness_run_52, reset_run, pos_x_run, pos_y_run, belief_run, belief_avg_xo, belief_std_xo, obs_run, cov_count, cov_avg_xo, cov_std_xo = read_data(folderName, time_run_xo, fitness_run_52, reset_run, pos_x_run, pos_y_run, belief_run, obs_run, cov_count, cov_avg, cov_std)
# folderName = "paper_data/baseline/fb_optimized/60/Log"
# time_run_p, fitness_run_60, reset_run, pos_x_run, pos_y_run, belief_run, belief_avg_p, belief_std_p, obs_run, cov_count_p, cov_avg_p, cov_std_p = read_data(folderName, time_run_p, fitness_run_60, reset_run, pos_x_run, pos_y_run, belief_run, obs_run, cov_count, cov_avg, cov_std)
# time_distribution(time_run_xo, time_run_p)
# fitness_distribution(fitness_batch)
# print("Average fitness for Baseline 1: ", np.mean(fitness_run_xo))
# print("Average fitness for Baseline 2: ", np.mean(fitness_run_p))
# belief_distribution(cov_batch_avg, cov_batch_std, belief_batch_avg, belief_batch_std)
# cov_belief(cov_count, cov_avg_xo, cov_std_xo, belief_avg_xo, belief_std_xo)
# end = time.time()
# print(end - start)
# binned_scatter_fitness(fitness_batch)
fitness_distribution(fitness_batch)
# kde_coverage(obs_run)
# hist_coveage(obs_run)

# single_belief(belief_avg_xo, belief_std_xo)