
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
def fitness_evaluation(iteration, particle, instance = 0):
    filename = run_dir + "Generation_%d/local_fitness_%d.txt" % (iteration, particle)
    # os.makedirs(os.path.dirname(filename), exist_ok=True)
    # with open( filename, mode='w') as filemy:
    #	filemy.write("1\n")
    with open(filename, mode='r') as f:
        fitness = f.readline().strip()
    if len(fitness) == 0:
        fitness = -1
        print("PSO_tocluster.py: Generation_" + str(iteration) + "/local_fitness_" + str(particle) + ".txt file is empty \n")
    else:
        fitness = float(fitness)
    # Simple Fitness Function
    #return (0-fitness)
    # Complex Fitness Function
    # 150*(average accuracy) + 100*(average coverage) - (average decision time)
    #fitness_res = (175*fitness[2] + 100*fitness[1] - fitness[0])
    fitness_res = float(fitness)
    print("Particle: ", iteration, particle)
    print("Fitness Result: ", fitness_res)
    return fitness_res


# --- MAIN ---------------------------------------------------------------------+

class Particle:
    def __init__(self,x,bounds):
        self.position_i = []  # particle position
        self.velocity_i = []  # particle velocity
        self.pos_best_i = []  # best position individual
        self.fit_best_i = -1  # best fitness individual
        self.fit_i = -1  # fitness individual

        for i in range(0, num_dimensions):
            self.velocity_i.append(random.uniform(-bounds[1], bounds[1]))
            self.position_i.append(x[i])

            # evaluate current fitness

    def evaluate(self, costFunc, iteration, particle, instance = 0):
        success = 1
        fitness = costFunc(iteration, particle, instance)
        if fitness == -1:
            success = 0
        else:
            self.fit_i = fitness
            success = 1
            if self.fit_i < self.fit_best_i or self.fit_best_i == -1:
                self.pos_best_i = self.position_i
                self.fit_best_i = self.fit_i


            # check to see if the current position is an individual best
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


class PSO():
    def __init__(self, x0, costFunc, bounds, num_particles, maxiter, noise_resistance):
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

            while num_evaluated_particles < num_particles:
                # wait for all jobs to be finished
                particle = pending_particles[0]
  
                if noise_resistance == 0:
                    file_path = run_dir + "Generation_%d/local_fitness_%d.txt" % (iteration, particle)
                    if os.path.exists(file_path):
                        success = swarm[particle].evaluate(costFunc, iteration, particle)
                        print("PSO_tocluster.py: evaluating Generation_" + str(iteration) + "/local_fitness_" + str(particle) + ".txt \n")
                        if success == 0:
                            print("PSO_tocluster.py: Generation_" + str(iteration) + "/local_fitness_" + str(particle) + ".txt file is empty \n")
                            #launch_webots(iteration, particle)
                        else:
                            num_evaluated_particles += 1
                            print("PSO_tocluster.py: remove individual particle " + str(particle) + "from the list of unevaluated particles \n")
                            # print(pending_particles)
                            pending_particles.remove(particle)
                else:
                    file_path = run_dir + "Generation_%d/local_fitness_%d_%d.txt" % (iteration, particle, instance)
                    if os.path.exists(file_path):
                        success = swarm[particle].evaluate(costFunc, iteration, particle, instance)
                        print("PSO_tocluster.py: evaluating Generation_" + str(iteration) + "/local_fitness_" + str(particle) + ".txt \n")
                        if success == 0:
                            print("PSO_tocluster.py: Generation_" + str(iteration) + "/local_fitness_" + str(particle) + ".txt file is empty \n")
                            #launch_webots(iteration, particle)
                        else:
                            num_evaluated_particles += 1
                            print("PSO_tocluster.py: remove individual particle " + str(particle) + "from the list of unevaluated particles \n")
                            # print(pending_particles)
                            pending_particles.remove(particle)


            # read the local fitnesss of each individual particle
            # determine if current particle is the best (globally)
            for particle in range(0, num_particles):
                if swarm[particle].fit_i < fit_best_g or fit_best_g == -1:
                    pos_best_g = list(swarm[particle].position_i)
                    fit_best_g = float(swarm[particle].fit_i)

            # cycle through swarm and update velocities and position
            for particle in range(0,num_particles):
                swarm[particle].update_velocity(pos_best_g)
                swarm[particle].update_position(bounds)


            results = run_dir + "Generation_%d/Parameters.txt" %(iteration)
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
parser.add_argument("-n", "--nb_particles", required=False, type=int, default="15", help="number of particles for PSO")
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
# Positive Feedback (Binary) | Credibility Thresdhold | Close Distance | Random Walk Forward | Random Walk Backward
bounds = [0,1,0,1,10,90,10,250,10,100]  # input bounds [(x1_min,x1_max, x2_min, x2_max, . . .)]
num_dimensions = 5 # Dimension of particle
x0=[0.4,0.5,30,250,100] # Initial particle position
# ------------------------------------------------------------------------------+
startTime=datetime.now() 
PSO(x0, fitness_evaluation, bounds, num_particles=args.nb_particles, maxiter=30)
print (datetime.now()-startTime)
duration = run_dir + "Final_Results/time_performance.txt"
os.makedirs(os.path.dirname(duration), exist_ok=True)
with open(duration, mode='w') as myfil:
    myfil.write(str(datetime.now()-startTime))

# --- END ----------------------------------------------------------------------+
