from matplotlib import projections
import numpy as np
import statistics
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D 
from matplotlib.animation import FuncAnimation
from numpy.linalg import norm

"""
TODO: 
1. Add a standard deviation on location of current generation
3. Add live view of robot decisions side by side.
"""
square_time = 2257.817 #this is in ms
time_step = 8 # this is in ms 
tao_square = square_time / time_step 
time_to_cross_arena = 36125.079475174839899 #ms
step_to_cross_arena = time_to_cross_arena / time_step
###########################################################

psodir = (str(os.getcwd())) + "/../../Run_0"
param_min = [19, tao_square/3, tao_square/3, 5, 0, 10]
param_max = [21, tao_square*3, step_to_cross_arena, 95, step_to_cross_arena, 250]
worst_case_fitess = 11200
num_particles = 10
num_noise = 5
num_gen = 14
num_robots = 4
particle_dim = 6
param_names = ["Alpha", "Tao", "Random Forward", "CA Trigger", "Hysterisis", "Observation Wait Time"]
std_gen = np.empty(num_gen) #tracks std deviation of particles per generation
std_param_gen = np.empty(num_gen) #tracks the std deviation of normalized paramters per generation
avg_gen = np.empty(num_gen) #tracks average of particles per generation
fit_gen = np.empty([num_gen, num_particles]) #tracks fitness of all particles per generation
raw_param_gen = np.empty([num_gen, num_particles, particle_dim]) #tracks the raw parameters of each particle per generation
param_gen = np.empty([num_gen, num_particles, particle_dim]) #tracks the normalized parameters of each particle per generation
best_param_gen = np.empty([num_gen, particle_dim]) #tracks the global best particle parameter per generation
param_avg_gen = np.empty([num_gen, particle_dim]) #tracks the average normalized parameters of each particle per generation
l2_gen = np.empty(num_gen) #tracks the l2 norm from the average swarm and the best particle
best_gen = np.empty(num_gen) #tracks the fitness of the best particle per generation
best_id_gen = np.empty(num_gen) #tracks the index of the best overeal particle per generation

def read_data(std_gen, std_param_gen, avg_gen, fit_gen, best_gen, best_id_gen, raw_param_gen, param_gen, param_avg_gen, best_param_gen, l2_gen):
    """
    This function reads in fitness files from the chosen directory and generates standard deviation and average fitness performance
    to be plotted
    std_gen: An 1xm list storing standard deviation of particles for m iterations
    avg_gen: An 1xm list storing average of noise evaluations of particles for m iterations
    fit_gen: A nxm list storing the n fitness values of each particle for m iterations
    """
    best_fitness = worst_case_fitess
    best_id = 0
    #ITERATIONS
    for i in range(num_gen):
        fitness_temp = np.empty(num_particles)
        param_avg_temp = np.zeros(particle_dim)
        gen = psodir + "/Generation_" + str(i)
        
        #PARTICLES
        for j in range(num_particles):
            noise_list = np.empty(num_noise)
            prob_path = gen + "/prob_" + str(j) + ".txt"

            #NOISE
            for k in range(num_noise):
                text = gen + "/local_fitness_" + str(j) + "_" + str(k) + ".txt"

                #Read fitness from file
                with open(text) as f:
                    fit = f.read().splitlines()

                noise_list[k] = float(fit[0])

            #Holds the particle fitness for this iteration
            particle_fit = statistics.mean(noise_list) + statistics.stdev(noise_list)

            if (particle_fit < best_fitness):
                best_fitness = particle_fit
                best_id = j

            fitness_temp[j] = particle_fit

            with open(prob_path) as f:
                probIn = f.read().splitlines()
            probIn = np.asarray(probIn, dtype=np.float64)
            raw_param_gen[i, j] = probIn
            for l in range(particle_dim):
                if param_max[0] == 0:
                    if (l > 0):
                        probIn[l] = (probIn[l] - param_min[l]) / (param_max[l] - param_min[l])
                else: 
                    probIn[l] = (probIn[l] - param_min[l]) / (param_max[l] - param_min[l])
            param_avg_temp = np.add(probIn, param_avg_temp)
            param_gen[i, j] = probIn



        best_id_gen[i] = best_id
        best_param_gen[i] = param_gen[i, best_id]
        best_gen[i] = best_fitness
        param_avg_gen[i] = np.divide(param_avg_temp, num_particles)
        l2_gen[i] = norm(best_param_gen[i] - param_avg_gen[i])
        fit_gen[i] = fitness_temp
        avg_gen[i] = statistics.mean(fit_gen[i])
        std_gen[i] = statistics.stdev(fit_gen[i])

    return std_gen, std_param_gen, avg_gen, fit_gen, best_gen, best_id_gen, raw_param_gen, param_gen, param_avg_gen, best_param_gen, l2_gen

def psoFitnessScatter(std_gen, avg_gen, fit_gen, best_gen):
    plt.plot(avg_gen, color='blue', label='Average Fitness')
    plt.plot(best_gen, color='red', label='Best Fitness')
    for i in range(num_gen):
        x = [i]*num_particles
        plt.scatter(x, fit_gen[i], color='green', s=25)
        if (i > 0):
            if (best_gen[i] < best_gen[i-1]):
                plt.axvline(x = i, linestyle='--', linewidth=0.5, color = 'k', label = 'Best Particle Found' if i == 0 else "")  
    bottom = avg_gen - std_gen
    bottom[bottom<0] = 0
    plt.fill_between(np.arange(num_gen), bottom, avg_gen + std_gen, where=(avg_gen + std_gen)>0, color='blue', alpha=0.3)
    plt.twinx()
    plt.plot(l2_gen, color='darkorange', label='L2 Norm')
    plt.savefig(psodir + '/graph.png', bbox_inches='tight')
    plt.show()


def animateParameter(l, param_gen, avg_gen, best_gen):
    #[Alpha, Tao, Random Forward, CA Trigger, Hysterisis, Obs Wait Time]

    colors=['blue', 'red', 'green', 'yellow', 'orange']
    fig = plt.figure(figsize=(12, 7))
    axProjection = fig.add_subplot(1,2,1,projection='3d')
    axFitness = fig.add_subplot(1,2,2)
    axProjection.view_init(20, 60)

    def animate(frame):
        axProjection.clear()
        axFitness.clear()
        fig.suptitle('Iteration: {}'.format(frame))

        # axProjection.set_xlim(0, 1)
        # axProjection.set_ylim(0, 1)
        # axProjection.set_zlim(0, 1)
        axProjection.set_xlabel("Alpha Prior")
        axProjection.set_ylabel("Tao")
        axProjection.set_zlabel("Observation Wait Time")
        axFitness.set_ylim(0, 1500)
        # axFitness.set_xlim(0, num_gen)
        axFitness.set_xlabel("Iteration")
        axFitness.set_ylabel("Fitness Value")
        axFitness.yaxis.set_label_position("right")

        for j in range(num_particles):
            #s=(param_gen[:frame, j,4]*100)
            axProjection.scatter(param_gen[:frame, j, 0], param_gen[:frame, j, 1], param_gen[:frame, j, 5], s=25, color='black', alpha=0.3, label='Previous Particle Location' if j == 0 else "")           
            axProjection.scatter(param_gen[frame, j, 0], param_gen[frame, j, 1], param_gen[frame, j, 5], s=25, color='green', label='Current Particle Location' if j == 0 else "")  
            axFitness.plot(avg_gen[:frame], color='blue', label="Average Fitness" if j == 0 else "")
            axFitness.plot(best_gen[:frame], color='red', label='Best Fitness' if j == 0 else "")
            axFitness.plot(std_gen[:frame], linestyle='dashed', label='Standard Dev.' if j == 0 else "", color='purple' )
            for k in range(frame):
                x = [k]*num_particles
                plt.scatter(x, fit_gen[k], color='green', s=10)
            bottom = avg_gen - std_gen
            bottom[bottom<0] = 0
            axFitness.fill_between(np.arange(frame), bottom[:frame], avg_gen[:frame] + std_gen[:frame], where=(avg_gen[:frame] + std_gen[:frame])>0, facecolor='C0', alpha=0.1)
        #axProjection.scatter(param_gen[frame, best_id_gen[frame], 0], param_gen[frame, best_id_gen[frame], 1], param_gen[:frame, best_id_gen[frame], 5], s=(param_gen[:frame, best_id_gen[frame],4]*100), color='red', label='Gloabl Best' if j == 0 else "")
        axFitness.legend()

    # run the animation
    ani = FuncAnimation(fig, animate, frames=num_gen, interval=1000, repeat=True)

    plt.show()
    #ani.save('animation.gif', writer='imagemagick', fps=1)
np.set_printoptions(suppress=True)
std_gen, std_param_gen, avg_gen, fit_gen, best_gen, best_id_gen, raw_param_gen, param_gen, param_avg_gen, best_param_gen, l2_gen = read_data(std_gen, std_param_gen, avg_gen, fit_gen, best_gen, best_id_gen, raw_param_gen, param_gen, param_avg_gen, best_param_gen, l2_gen)
print("Best Particle Found: ", raw_param_gen[num_gen-1, int(best_id_gen[num_gen-1])])
print("Best Particle Found Normalized: ", param_gen[num_gen-1, int(best_id_gen[num_gen-1])])
print("Fitness: ", fit_gen[num_gen-1, int(best_id_gen[num_gen-1])])
psoFitnessScatter(std_gen, avg_gen, fit_gen, best_gen)
#animateParameter(0, param_gen, avg_gen, best_gen)
# 
