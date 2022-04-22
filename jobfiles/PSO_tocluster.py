# --- IMPORT DEPENDENCIES ------------------------------------------------------+

from __future__ import division
import random
import os
import subprocess
import time
import os.path
from datetime import datetime
import statistics
#import sys
#import fileinput

# --- COST FUNCTION ------------------------------------------------------------+

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
def fitness_evaluation(i, j):
    filename = "Generation_%d/local_fitness_%d.txt" % (i, j)
    # os.makedirs(os.path.dirname(filename), exist_ok=True)
    # with open( filename, mode='w') as filemy:
    #	filemy.write("1\n")
    with open(filename, mode='r') as f:
        fitness = f.readline().strip()
    if len(fitness) == 0:
        fitness = -1
        print('File is empty \n')
    else:
        fitness = float(fitness)
    return fitness


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

    def evaluate(self, costFunc, i, j):
        success = 1
        fitnes = costFunc(i, j)
        if fitnes == -1:
            success = 0
        else:
            self.fit_i = fitnes
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
        for i in range(0, num_dimensions):
            self.position_i[i] = self.position_i[i] + self.velocity_i[i]

            # adjust maximum position if necessary
            if self.position_i[i] > bounds[1]:
                self.position_i[i] = bounds[1]

            # adjust minimum position if neseccary
            if self.position_i[i] < bounds[0]:
                self.position_i[i] = bounds[0]

            # adjust maximum velocity if necessary
            if self.velocity_i[i] > 0.15*(bounds[1]-bounds[0]):
                self.velocity_i[i] = 0.15*(bounds[1]-bounds[0])

            # adjust minimum position if neseccary
            if self.velocity_i[i] < -0.15*(bounds[1]-bounds[0]):
                self.velocity_i[i] = -0.15*(bounds[1]-bounds[0])


class PSO():
    def __init__(self, x0, costFunc, bounds, num_particles, maxiter):
        global num_dimensions

        fit_best_g = -1  # best global fitness
        pos_best_g = []  # best position

        # establish the swarm
        swarm = []
        swarm.append(Particle(x0,bounds))

        for i in range(1, num_particles):
            x=[]
            for j in range(0,num_dimensions):
                x.append(random.uniform(bounds[0],bounds[1]))
            
            swarm.append(Particle(x,bounds))
        print("This is the number of particles in swarm: \n")
        print(len(swarm))

        # begin optimization loop
        i = 0
        ii = 0
        while i < maxiter:
            particles_fit = []
            # cycle through particles in swarm and evaluate fitness
            for j in range(0, num_particles):
                filename = "Generation_%d/prob_%d.txt" % (i, j)
                print("Launching the new Generation")
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, mode='w') as myfile:
                    myfile.write('\n'.join(str(p_w) for p_w in swarm[j].position_i))
                launch_webots(i, j)

            #debug
            #outs = ''
            #end debug
            ok = 0
            not_evaluated = list(range(0, num_particles))
 #           print(not_evaluated)
            while ok < num_particles:
                jobs = subprocess.Popen(['qstat'], stdout=subprocess.PIPE, shell=True)
                outs, errs = jobs.communicate()
                # wait till all jobs are done
                while len(outs) != 0:
                    time.sleep(1)
                    jobs = subprocess.Popen(['qstat'], stdout=subprocess.PIPE, shell=True)
                    outs, errs = jobs.communicate()
                    ii += 1
                    if ii > 60:
                        #print(outs)
                        print("\nwaiting for qstat to be empty, current time is:")
                        print (datetime.now())
                        print("number of jobs remaining is:")
                        print(len(outs))
                        ii = 0

                print("jobs done: \n ")
                # check if all jobs are done successfully, relaunch the ones who are not successful

                for kk in range (0,len(not_evaluated)):                    
                    j=not_evaluated[0]
			
                    file_path = "Generation_%d/local_fitness_%d.txt" % (i, j)
                    print(file_path)
                    if not os.path.exists(file_path):
                        print("path does not exist \n")
                        #launch_webots(i, j)
                    else:
                        success = swarm[j].evaluate(costFunc, i, j)
                        print("evaluating \n")
                        if success == 0:
                            print("local_fitness.txt does not exist")
                            #launch_webots(i, j)
                        else:
                            ok += 1
                            print("remove individ  "+str(not_evaluated))
                           # print(not_evaluated)
                            not_evaluated.remove(j)

            # read the local fitnesss of each individual
            # determine if current particle is the best (globally)
            for j in range(0, num_particles):
                if swarm[j].fit_i < fit_best_g or fit_best_g == -1:
                    pos_best_g = list(swarm[j].position_i)
                    fit_best_g = float(swarm[j].fit_i)

                    # cycle through swarm and update velocities and position
            for j in range(0,num_particles):
                swarm[j].update_velocity(pos_best_g)
                swarm[j].update_position(bounds)


            results = "Generation_%d/Parameters.txt" %(i)
            os.makedirs(os.path.dirname(results), exist_ok=True)
            with open(results, mode='w') as myfile2:
                for j in range(0, num_particles):
                    myfile2.write(str(str(i)+'\t'+ str(j) + '\n'+'\t'.join(str(e) for e in swarm[j].velocity_i) + '\n' + '\t'.join(str(ee) for ee in swarm[j].pos_best_i) + '\n'+str(swarm[j].fit_best_i)+'\n'))
                    particles_fit.append(swarm[j].fit_best_i)
            # write back to the files
            fileresults = "Final_Results/best_results.txt"
            os.makedirs(os.path.dirname(fileresults), exist_ok=True)
            with open(fileresults, mode='a') as myfile:
                myfile.write(str(str(i) + '\t'+'\t'.join(str(e) for e in pos_best_g) + '\t' + str(fit_best_g) + '\n'))


            # write back to the files
            fileresults = "Final_Results/average_results.txt"
            os.makedirs(os.path.dirname(fileresults), exist_ok=True)
            with open(fileresults, mode='a') as myfile:
                myfile.write(str(statistics.mean(particles_fit)) + '\t'+str(statistics.stdev(particles_fit))+'\n')

            # print("next iter")
            i += 1

        # print final results
        print('FINAL:')
        print(pos_best_g)
        print(fit_best_g)




if __name__ == "__PSO__":
    main()

# --- RUN ----------------------------------------------------------------------+

# initial=[5,5]               # initial starting location [x1,x2...]
bounds = [0,0.5]  # input bounds [(x1_min,x1_max)]
num_dimensions = 3
x0=[0.01,0.005,0.000025]
startTime=datetime.now()
PSO(x0, fitness_evaluation, bounds, num_particles=15, maxiter=30)
print (datetime.now()-startTime)
duration = "Final_Results/time_performance.txt"
os.makedirs(os.path.dirname(duration), exist_ok=True)
with open(duration, mode='w') as myfil:
    myfil.write(str(datetime.now()-startTime))

# --- END ----------------------------------------------------------------------+
