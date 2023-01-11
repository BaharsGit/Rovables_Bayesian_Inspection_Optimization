
#
# File: PSO_tocluster.py python script       
# Date: 17 March 2017     
# Description: This python script was written for cluster job file job_lily_parallel.sub, 
#              it runs on AWS (particle) nodes, it launches Webots to evaluate the corresponding particle
# Author: Bahar Haghighat 
# Modifications: by Bahar Haghighat, 13 June 2022, cleaned up non-AWS stuff left from local cluster launch
#


# --- IMPORT DEPENDENCIES ------------------------------------------------------+

from __future__ import division
import random
import os
import subprocess
import time
import os.path
from datetime import datetime
import statistics
import argparse
import numpy as np
import math
#import sys
#import fileinput

# --- COST FUNCTION, OBSOLETE ------------------------------------------------------------+

# launch webots to evaluate the fitness to optimize
def launch_webots(i, j):
    #print("Running Webots")
    cmd = 'qsub job_lily_parallel.sub %d %d' % (i, j)
    print(cmd)
    #cmd2 = 'webots_8_5_0 --minimize --mode=fast --stderr ../worlds/24Lilies_LaLn.wbt '

    # debug
    #filename = "Generation_%d/local_fitness_%d.txt" % (i, j)
    #os.makedirs(os.path.dirname(filename), exist_ok=True)
    #with open(filename, mode='w') as filemy:
    #    filemy.write(str(j)+"\n")
    # debug

    # calling the process to happen with outputting the error
    proc=subprocess.Popen([cmd],shell=True)
    
    try:
        outss, errss=proc.communicate(timeout=7200)
    except TimeoutExpired:
        proc.kill()
        outss,errss=proc.communicate()


# ---- Read fitness files-------------------------------------------------------+
# MODIFIED FOR NOISE RESISTANT PSO
def fitness_evaluation(iteration, particle, instance = -1):
    if instance == -1:
        filename = run_dir + "Generation_%d/local_fitness_%d.txt" % (iteration, particle)
    else:
        filename = run_dir + "Generation_%d/local_fitness_%d_%d.txt" % (iteration, particle, instance)
    # os.makedirs(os.path.dirname(filename), exist_ok=True)
    # with open( filename, mode='w') as filemy:
    #	filemy.write("1\n")
    with open(filename, mode='r') as f:
        fitness = f.readline().strip()
    if len(fitness) == 0:
        fitness = WORST_FITNESS
        if instance == -1:
            print("PSO_tocluster.py: Generation_" + str(iteration) + "/local_fitness_" + str(particle) + ".txt file is empty \n")
        else:
            print("PSO_tocluster.py: Generation_" + str(iteration) + "/local_fitness_" + str(particle) + "_" + str(instance) + ".txt file is empty \n")
    else:
        fitness = float(fitness)
    # Simple Fitness Function
    #return (0-fitness)
    # Complex Fitness Function
    # 150*(average accuracy) + 100*(average coverage) - (average decision time)
    #fitness_res = (175*fitness[2] + 100*fitness[1] - fitness[0])
    print("Fitness evaluation for particle " + str(particle) + " in iteration " + str(iteration) + ": \n")
    print("Fitness value read from the file is: ", fitness)
    return fitness

def test_optimization_space(position):
    print("Test Particle has position: ", position)
    #test_fitness = (1/math.pow(position[0],4) + math.pow(position[1],2) + position[3] + 1/math.pow(position[4],2) + 3034) + np.random.normal(0, 750, 1)
    test_fitness = 0
    #Using the Rosenbrock function, where the minimum is X_n = 1
    for i in range(num_dimensions-1):
        test_fitness = test_fitness + 100*math.pow((position[i+1] - math.pow(position[i], 2)), 2) + math.pow((1-position[0]), 2)
    test_fitness = np.random.normal(test_fitness, test_fitness*0.001, 1)
    return test_fitness[0]

# --- MAIN ---------------------------------------------------------------------+

class Particle:
    def __init__(self,x,bounds):
        self.position_i = []  # particle position
        self.velocity_i = []  # particle velocity
        self.pos_best_i = []  # best position individual
        self.fit_best_i = -1  # best fitness individual
        self.fit_i = -1  # fitness individual
        self.fit_array_i = []

        dim_index = 1
        for i in range(0, num_dimensions):
            self.velocity_i.append(random.uniform(-bounds[dim_index], bounds[dim_index]))
            self.position_i.append(x[i])
            dim_index = dim_index + 2

            # evaluate current fitness

    # MODIFIED FOR NOISE RESISTANT PSO
    def evaluate(self, costFunc, iteration, particle, instance = -1, noise_resistance_evals = 0):
        success = 1
        fitness = costFunc(iteration, particle, instance)
        if fitness == -1:
            success = 0
        else:
            if noise_resistance_evals == 0:
                self.fit_i = fitness
            else:
                # self.fit_i += fitness/noise_resistance_evals
                self.fit_array_i.append(fitness)

                #Find STD and Mean when the array is full
                if (len(self.fit_array_i) == noise_resistance_evals):
                    self.fit_i = statistics.stdev(self.fit_array_i) + statistics.mean(self.fit_array_i)
                    
                    # check to see if the current position is an individual best
                    if ((self.fit_i < self.fit_best_i) or (self.fit_best_i == -1)):
                        print("Particle: " + str(particle) + " found new personal best: " + str(self.fit_i) + " against: " + str(self.fit_best_i))
                        self.pos_best_i = self.position_i
                        self.fit_best_i = self.fit_i
                    print("Particle: " + str(particle) + " Evaluated to be fitness: " + str(self.fit_i))
                    
                    # Must reset array after each iteration.
                    self.fit_array_i = []
            success = 1
            

        return success

    # update new particle velocity
    def update_velocity(self, pos_best_g):
        PSO_W = -0.1832 # PSO Parameters
        PSO_PW = 0.5287
        PSO_NW = 3.1913

        for i in range(0, num_dimensions):
            r1 = random.random()
            r2 = random.random()

            vp = PSO_PW * r1 * (self.pos_best_i[i] - self.position_i[i])
            vn = PSO_NW * r2 * (pos_best_g[i] - self.position_i[i])
            self.velocity_i[i] = PSO_W * self.velocity_i[i] + vp + vn

    # update the particle position based off new velocity updates
    def update_position(self, bounds):
        dim_index = 0
        for i in range(0, num_dimensions):
            self.position_i[i] = self.position_i[i] + self.velocity_i[i]

            # adjust maximum position if necessary
            if self.position_i[i] > bounds[dim_index + 1]:
                self.position_i[i] = bounds[dim_index + 1]

            # adjust minimum position if neseccary
            if self.position_i[i] < bounds[dim_index]:
                self.position_i[i] = bounds[dim_index]

            # adjust maximum velocity if necessary
            if self.velocity_i[i] > 0.15*(bounds[dim_index + 1]-bounds[dim_index]):
                self.velocity_i[i] = 0.15*(bounds[dim_index + 1]-bounds[dim_index])

            # adjust minimum position if neseccary
            if self.velocity_i[i] < -0.15*(bounds[dim_index + 1]-bounds[dim_index]):
                self.velocity_i[i] = -0.15*(bounds[dim_index + 1]-bounds[dim_index])

            dim_index = dim_index + 2

# MODIFIED FOR NOISE RESISTANT PSO
class PSO():
    def __init__(self, x0, costFunc, bounds, maxiter, num_particles = 15, noise_resistance_evals = 0):
        global num_dimensions

        fit_best_g = -1  # best global fitness
        pos_best_g = []  # best position

        # establish the swarm
        swarm = []
        swarm.append(Particle(x0,bounds))

        for i in range(1, num_particles):
            rand_init_count = 0
            x=[]
            for j in range(0,num_dimensions):
                #x.append(random.uniform(bounds[0],bounds[1])) MODIFIED FOR BAYES BOT
                if (j == 0):
                    sampled_number = random.uniform(0,bounds[rand_init_count + 1])

                    if (sampled_number < bounds[rand_init_count]):
                        x.append(sampled_number + bounds[rand_init_count])
                    else:
                        x.append(sampled_number)
                else:
                    x.append(random.uniform(bounds[rand_init_count],bounds[rand_init_count + 1])) #includes low excludes high
                rand_init_count = rand_init_count + 2
            
            swarm.append(Particle(x,bounds))
        print("PSO_tocluster.py: This is the number of particles in swarm: " + str(len(swarm)) + "\n")

        # begin optimization loop
        iteration = 0

        while iteration < maxiter:
            particles_fit = []
            # cycle through particles in swarm and evaluate fitness
            for particle in range(0, num_particles):
                filename = run_dir + "Generation_%d/prob_%d.txt" % (iteration, particle)
                print("PSO_tocluster.py: Writing the new Generation " + str(iteration) + " Particle " + str(particle) + " text file: " + "Generation_" + str(iteration) + "/prob_" + str(particle) +".txt")
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, mode='w') as myfile:
                    myfile.write('\n'.join(str(p_w) for p_w in swarm[particle].position_i))

            num_evaluated_particles = 0
            pending_particles = list(range(0, num_particles))

            # MODIFIED FOR NOISE RESISTANT PSO
            instance = noise_resistance_evals -1    
            while num_evaluated_particles < num_particles:
                # wait for all jobs to be finished
                particle = pending_particles[0]
  
                if noise_resistance_evals == 0:
                    file_path = run_dir + "Generation_%d/local_fitness_%d.txt" % (iteration, particle)
                    if os.path.exists(file_path):
                        success = swarm[particle].evaluate(costFunc, iteration, particle)
                        print("PSO_tocluster.py: evaluating Generation_" + str(iteration) + "/local_fitness_" + str(particle) + ".txt \n")
                        if success == 0:
                            print("PSO_tocluster.py: Generation_" + str(iteration) + "/local_fitness_" + str(particle) + ".txt file is empty \n")
                            #launch_webots(iteration, particle)
                        else:
                            print("PSO_tocluster.py: remove individual particle " + str(particle) + " from the list of unevaluated particles \n")
                            # print(pending_particles)
                            pending_particles.remove(particle)
                            num_evaluated_particles += 1

                # MODIFIED FOR NOISE RESISTANT PSO
                else:
                    if (args.test_pso):
                        f = open("outputFile","wb")
                        #Start webots
                        os.system('echo RUNNING TEST')
                        print(os.getcwd())
                        # os.chdir("/home/darren/Documents/ICRA_LAUNCH/Rovables_Bayesian_Inspection_Optimization/demo/jobfiles/Run_0")
                        os.chdir(run_dir)
                        print(iteration, particle, instance)
                        print(os.getcwd())
                        # with open('/tmp/job' + str(iteration) + '_' + str(particle) + '_' + str(instance) + 'local_fitness.txt', 'w') as f:
                        #     f.write(str(test_optimization_space(swarm[particle].position_i)))
                        subprocess.check_call(['.././job_lily_parallel.sh', str(iteration), str(particle), str(instance), '4', str(test_optimization_space(swarm[particle].position_i))], stdout=f)
                        
                        os.chdir("../")
                    
                    file_path = run_dir + "Generation_%d/local_fitness_%d_%d.txt" % (iteration, particle, instance)
                    print(file_path)
                    print(os.getcwd())
                    if os.path.exists(file_path):
                        success = swarm[particle].evaluate(costFunc, iteration, particle, instance, noise_resistance_evals)
                        print("PSO_tocluster.py: evaluating Generation_" + str(iteration) + "/local_fitness_" + str(particle) + "_" + str(instance) + ".txt \n")
                        if success == 0:
                            print("PSO_tocluster.py: Generation_" + str(iteration) + "/local_fitness_" + str(particle) + "_" + str(instance) + ".txt file is empty \n")
                            #launch_webots(iteration, particle)
                        else:
                            print("PSO_tocluster.py: remove instance " + str(instance) + " of individual particle " + str(particle) + " from the list of unevaluated particles \n")
                            instance -= 1
                            if instance == -1:
                                pending_particles.remove(particle)
                                num_evaluated_particles += 1
                                instance = noise_resistance_evals -1

            # read the local fitnesss of each individual particle
            # determine if current particle is the best (globally)
            for particle in range(0, num_particles):
                if (swarm[particle].fit_i < fit_best_g) or (fit_best_g == -1):
                    print("Found best particle at: " + str(particle) + " With fitness: " + str(swarm[particle].fit_i) + " against best fitness: " + str(fit_best_g))
                    pos_best_g = list(swarm[particle].position_i)
                    fit_best_g = float(swarm[particle].fit_i)
                else:
                    print("Did not find best particle at: " + str(particle) + " With fitness: " + str(swarm[particle].fit_i) + " against best fitness: " + str(fit_best_g))
                
            # cycle through swarm and update velocities and position
            for particle in range(0,num_particles):
                swarm[particle].update_velocity(pos_best_g)
                swarm[particle].update_position(bounds)


            results = run_dir + "Generation_%d/Parameters.txt" % (iteration)
            os.makedirs(os.path.dirname(results), exist_ok=True)
            with open(results, mode='w') as myfile2:
                for particle in range(0, num_particles):
                    myfile2.write(str(str(iteration)+'\t'+ str(particle) + '\n'+'\t'.join(str(e) for e in swarm[particle].velocity_i) + '\n' + '\t'.join(str(ee) for ee in swarm[particle].pos_best_i) + '\n'+str(swarm[particle].fit_best_i)+'\n'))
                    particles_fit.append(swarm[particle].fit_best_i)
            # write back to the files
            fileresults = run_dir + "Final_Results/best_results.txt"
            os.makedirs(os.path.dirname(fileresults), exist_ok=True)
            with open(fileresults, mode='a') as myfile:
                myfile.write(str(str(iteration) + '\t'+'\t'.join(str(e) for e in pos_best_g) + '\t' + str(fit_best_g) + '\n'))


            # write back to the files
            fileresults = run_dir + "Final_Results/average_results.txt"
            os.makedirs(os.path.dirname(fileresults), exist_ok=True)
            with open(fileresults, mode='a') as myfile:
                myfile.write(str(statistics.mean(particles_fit)) + '\t'+str(statistics.stdev(particles_fit))+'\n')

            # print("next iter")
            iteration += 1

        # print final results
        print("PSO_tocluster.py: FINAL, the pso_best_g is " + str(pos_best_g) + "and the fit_best_g is " + str(fit_best_g) + " \n")
        #print(pos_best_g)
        #print(fit_best_g)




if __name__ == "__PSO__":
    main()

# argument for number of particles
parser = argparse.ArgumentParser(description='Run PSO to optimize parameters in the context of self-assembling robots')
# MODIFIED FOR NOISE RESISTANT PSO
parser.add_argument("-n", "--nb_particles", required=False, type=int, default="15", help="number of particles for PSO")
parser.add_argument("-e", "--nb_noise_res_evals", required=False, type=int, default="0", help="number of noise resistance evaluations for PSO")
parser.add_argument("-t", "--test_pso", required=False, type=int, default="0", help="Boolean to run PSO in series or parallel")

args = parser.parse_args()
if args.nb_particles < 2:
    parser.error("Minimum number of particles is 2")

# new result directory
run_dirs = [x for x in os.listdir(".") if x.startswith('Run_')]
if len(run_dirs): 
  last_run_id = int(sorted(run_dirs).pop()[4:])
else:
  last_run_id = -1
run_dir = "Run_" + str(last_run_id+1) + "/"
os.mkdir(run_dir)

# --- RUN PSO SETUP ----------------------------------------------------------------------+

# initial=[5,5]               
# initial starting location [x1,x2...]
# input bounds [(x1_min,x1_max)]
PARTICLE_SET = 1
bounds = []
num_dimensions = 6
x0 = []

#TAO NEEDS TO INCLUDE CROSSING ONE SQUARE BOTH UNDER AND OVER 
#TIME STEPS TO CROSS ONE SQUARE
#LB = TIME / NUM
#UB = TIME * NUM
# SET ALPHA TO ZERO, DO NOT INCLUDE 
# SET PAUSE TO ZERO
# RANDOM 
# TAO SHOULD BE EQUAL OR LARGER THAN THE LB OF RANDOM FORWARD, UB SHOULD BE THE SIZE OF THE WHOLE ARENA
# (UB RANDOM FORWARD / LB TAO) * NUM
# RUN PARTICLE 1 AND PARTICLE 3 SET WITH THE PROPER BOUNDS

if (PARTICLE_SET == 1): # SET ONE 
    bounds = [10, 500, 10, 350, 20, 3000, 5, 95, 0, 100, 10, 250]  # input bounds [(x1_min,x1_max, x2_min, x2_max, . . .)]
    x0=[10, 200, 200, 30, 60, 200] #[Alpha, Tao, Random Forward, CA Trigger, Hysterisis, Obs Wait Time]
if (PARTICLE_SET == 2):
    bounds = [10, 500, 10, 350, 20, 3000, 10, 90, 0, 0, 10, 250]  # input bounds [(x1_min,x1_max, x2_min, x2_max, . . .)]
    x0=[10, 200, 200, 30, 0, 15] #[Alpha, Tao, Random Forward, CA Trigger, Hysterisis, Obs Wait Time]
if (PARTICLE_SET == 3):
    bounds = [0, 0, 10, 350, 20, 3000, 10, 90, 5, 100, 0, 2500]  # input bounds [(x1_min,x1_max, x2_min, x2_max, . . .)]
    x0=[10, 200, 200, 30, 60, 15]  #[Alpha, Tao, Random Forward, CA Trigger, Hysterisis, Obs Wait Time]
if (PARTICLE_SET == 4):
    bounds = [0, 0, 10, 350, 20, 3000, 10, 90, 0, 0, 10, 250]  # input bounds [(x1_min,x1_max, x2_min, x2_max, . . .)]
    x0=[10, 200, 200, 30, 0, 15]  #[Alpha, Tao, Random Forward, CA Trigger, Hysterisis, Obs Wait Time]
if (PARTICLE_SET == 5):
    # THIS IS USED WITH THE TEST OPTIMIZATION FUNCTION
    bounds = [0, 10000, 0, 10000, 0, 10000, 0, 10000, 0, 10000, 0, 10000]  # input bounds [(x1_min,x1_max, x2_min, x2_max, . . .)]
    x0=[10, 200, 200, 30, 0, 15] 
random.seed(0)
WORST_FITNESS=100000 
# ------------------------------------------------------------------------------+
startTime=datetime.now() 
# MODIFIED FOR NOISE RESISTANT PSO
PSO(x0, fitness_evaluation, bounds, maxiter=100, num_particles=args.nb_particles, noise_resistance_evals=args.nb_noise_res_evals)
print (datetime.now()-startTime)
duration = run_dir + "Final_Results/time_performance.txt"
os.makedirs(os.path.dirname(duration), exist_ok=True)
with open(duration, mode='w') as myfil:
    myfil.write(str(datetime.now()-startTime))

# --- END ----------------------------------------------------------------------+
