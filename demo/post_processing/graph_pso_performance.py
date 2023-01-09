from matplotlib import projections
import numpy as np
import statistics
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D 
from matplotlib.animation import FuncAnimation

psodir = (str(os.getcwd())) + "/demo/jobfiles/Run_3"

worst_case_fitess = 11200
num_particles = 5
num_noise = 5
num_gen = 5
num_robots = 4
particle_dim = 6
std_gen = np.empty(num_gen) #tracks std deviation of particles per generation
avg_gen = np.empty(num_gen) #tracks average of particles per generation
fit_gen = np.empty([num_gen, num_particles]) #tracks fitness of all particles per generation
param_gen = np.empty([num_gen, num_particles, particle_dim]) #tracks the parameters of each particle per generation
best_gen = np.empty(num_gen) #tracks the fitness of the best particle per generation

def read_data(std_gen, avg_gen, fit_gen, best_gen, param_gen):
    """
    This function reads in fitness files from the chosen directory and generates standard deviation and average fitness performance
    to be plotted
    std_gen: An 1xm list storing standard deviation of particles for m iterations
    avg_gen: An 1xm list storing average of noise evaluations of particles for m iterations
    fit_gen: A nxm list storing the n fitness values of each particle for m iterations
    """
    best_fitness = worst_case_fitess
    #ITERATIONS
    for i in range(num_gen):
        fitness_temp = np.empty(num_particles)
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

            fitness_temp[j] = particle_fit

            with open(prob_path) as f:
                probIn = f.read().splitlines()
            probIn = np.asarray(probIn, dtype=np.float64)
            param_gen[i, j] = probIn

        best_gen[i] = best_fitness
                
        fit_gen[i] = fitness_temp
        avg_gen[i] = statistics.mean(fit_gen[i])
        std_gen[i] = statistics.stdev(fit_gen[i])

    return avg_gen, std_gen, fit_gen, best_gen, param_gen

def psoFitnessScatter(std_gen, avg_gen, fit_gen, best_gen):
    plt.plot(avg_gen)
    plt.plot(best_gen, color='red')
    for i in range(num_gen):
        x = [i]*num_particles
        plt.scatter(x, fit_gen[i], color='green', s=25)
    bottom = avg_gen - std_gen
    bottom[bottom<0] = 0
    plt.fill_between(np.arange(num_gen), bottom, avg_gen + std_gen, where=(avg_gen + std_gen)>0, color='blue', alpha=0.3)
    plt.show()


def animateParameter(l, param_gen):
    colors=['blue', 'red', 'green', 'yellow', 'orange']
    fig = plt.figure(figsize=(12, 12))
    ax = fig.add_subplot(projection='3d')

    def animate(i):
        ax.clear()
        ax.set_xlim(10,150)
        ax.set_ylim(10, 350)
        ax.set_zlim(20, 3000)
        for j in range(num_particles):
            ax.scatter(param_gen[i, j, 0], param_gen[i, j, 1], param_gen[i, j, 2], color=colors[j]) 
        ax.set_title('Iteration: {}'.format(i))
    # run the animation
    ani = FuncAnimation(fig, animate, frames=num_gen, interval=1000, repeat=True)

    plt.show()

avg_gen, std_gen, fit_gen, best_gen, param_gen = read_data(std_gen, avg_gen, fit_gen, best_gen, param_gen)
psoFitnessScatter(std_gen, avg_gen, fit_gen, best_gen)

# animateParameter(0, param_gen)