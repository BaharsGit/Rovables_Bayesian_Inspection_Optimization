from matplotlib import projections
import numpy as np
import statistics
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D 
from matplotlib.animation import FuncAnimation

psodir = (str(os.getcwd())) + "/../jobfiles/Run_3"
param_min = [10, 10, 20, 10, 5, 10]
param_max = [500, 350, 3000, 90, 100, 250]
worst_case_fitess = 11200
num_particles = 5
num_noise = 5
num_gen = 15
num_robots = 4
particle_dim = 6
std_gen = np.empty(num_gen) #tracks std deviation of particles per generation
avg_gen = np.empty(num_gen) #tracks average of particles per generation
fit_gen = np.empty([num_gen, num_particles]) #tracks fitness of all particles per generation
param_gen = np.empty([num_gen, num_particles, particle_dim]) #tracks the parameters of each particle per generation
best_gen = np.empty(num_gen) #tracks the fitness of the best particle per generation
best_id_gen = np.empty(num_gen) #tracks the index of the best overeal particle per generation

def read_data(std_gen, avg_gen, fit_gen, best_gen, best_id_gen, param_gen):
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
            for l in range(particle_dim):
                probIn[l] = (probIn[l] - param_min[l]) / (param_max[l] - param_min[l])
            param_gen[i, j] = probIn

        best_id_gen[i] = best_id
        best_gen[i] = best_fitness
                
        fit_gen[i] = fitness_temp
        avg_gen[i] = statistics.mean(fit_gen[i])
        std_gen[i] = statistics.stdev(fit_gen[i])

    return avg_gen, std_gen, fit_gen, best_gen, best_id_gen, param_gen

def psoFitnessScatter(std_gen, avg_gen, fit_gen, best_gen):
    plt.plot(avg_gen)
    plt.plot(best_gen, color='red')
    for i in range(num_gen):
        x = [i]*num_particles
        plt.scatter(x, fit_gen[i], color='green', s=25)
    bottom = avg_gen - std_gen
    bottom[bottom<0] = 0
    plt.fill_between(np.arange(num_gen), bottom, avg_gen + std_gen, where=(avg_gen + std_gen)>0, color='blue', alpha=0.3)


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
            axProjection.scatter(param_gen[:frame, j, 0], param_gen[:frame, j, 1], param_gen[:frame, j, 5], s=(param_gen[:frame, j,4]*100), color='black', alpha=0.3, label='Previous Particle Location' if j == 0 else "")           
            axProjection.scatter(param_gen[frame, j, 0], param_gen[frame, j, 1], param_gen[frame, j, 5], s=(param_gen[frame, j,4]*100), color='green', label='Current Particle Location' if j == 0 else "")  
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

    # plt.show()
    ani.save('animation.gif', writer='imagemagick', fps=1)


avg_gen, std_gen, fit_gen, best_gen, best_id_gen, param_gen = read_data(std_gen, avg_gen, fit_gen, best_gen, best_id_gen, param_gen)
#psoFitnessScatter(std_gen, avg_gen, fit_gen, best_gen, num_gen)
animateParameter(0, param_gen, avg_gen, best_gen)

# Add live view of robot decisions side by side.
# Set pause time to zero and check values 