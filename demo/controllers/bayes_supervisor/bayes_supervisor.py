"""vibration_controller controller."""
from controller import Supervisor
import os
import platform
import csv
import math
import random
import numpy as np
from decimal import Decimal
# MODIFIED FOR AWS LAUNCH
import time
import sys

# MODIFIED FOR AWS LAUNCH, MAX_TIME IS IN SECONDS, FROM PREVIOUS EXPERIMENTS 140 SECONDS IS ROUGHLY ENOUGH
MAX_TIME = 3600 #unit is in seconds, 2700 is around 45 minutes.
WALL_TIME = 600
#2700 45 min good?
reset_counter = 0
fill_ratio = 0
seedIn = 0
dynamic_env = int(sys.argv[2])
baseline = int(sys.argv[3])
run = 0
nRobot = 0 # The number of robots is set later
boxSize = 8    
imageDim = 128
p_high = 0.9
p_low = 0.1
minD = 0.15
initialPos = []
csvProbData = []
csvPosData = []
parameters = []
boxData = []
accuracy = []
reset_flag = 0
defArray = []
defIndex = 0
fillIndex = 0


print(os.name)
print(platform.system())
working_dir = os.getenv("WB_WORKING_DIR")


# create the Robot instance.
supervisor = Supervisor()

# get the time step of the current world.
timestep = int(supervisor.getBasicTimeStep())

#Find the number of robots in the simulation
while(1):
    robotDef = "rov_{}".format(defIndex)
    robotObj = supervisor.getFromDef(robotDef)
    if (robotObj is not None):
        nRobot = nRobot + 1
        defArray.append(robotDef)
        defIndex = defIndex + 1
    else:
        print(defArray)
        break

dec_arr = np.zeros(nRobot)
dec_counter = np.zeros(nRobot)
dec_time = np.zeros(nRobot)
time_track = np.zeros(nRobot)
dec_hold = np.zeros(nRobot)
coverage_arr = []
start_time = time.time()
sim_time = 0
control_count = 0
fitness = np.zeros(nRobot)

rov_node_array = np.empty(nRobot, dtype=object)
trans_field_array = np.empty(nRobot, dtype=object)
rot_field_array = np.empty(nRobot, dtype=object)
data_array = np.empty(nRobot, dtype=object)
trans_value_array = np.empty(nRobot, dtype=object)
color_array = np.empty(nRobot, dtype=object)

# --------------------------------------------------------------
def setSeed():
    global seedIn
    seedIn = str(sys.argv[1])
    print("Supervisor: Using Seed, ", seedIn)
    random.seed(seedIn)

def evaluateFitness(dec_time, decision, fill_ratio):

    #Linear Fitness Function; For individual robot decisions
    robot_decision = int(decision)
    current_fill = float(fill_ratio)
    print("Supervisor: Reading Decision,", robot_decision)
    print("Supervisor: Checking for fill ratio,", current_fill)
    if (current_fill > 0.5):
        if (robot_decision == 1):
            print("Supervisor: Correct Decision was made")
            return dec_time
        else: 
            print("Supervisor: Incorrect decision, assigned max time")   
            return MAX_TIME + (100*nRobot)
    else:
        if (robot_decision == 0):
            print("Supervisor: Correct Decision was made")
            return dec_time
        else: 
            print("Supervisor: Incorrect decision, assigned max time")   
            return MAX_TIME + (100*nRobot)

    #Add another fitness evaluation for the swarm as a whole.
    


# Writes to the fitness file for the current iteration of particle
def cleanup(time_arr, fitness):
    global seedIn
    current_fill = float(fill_ratio)

    for k in range(nRobot):
        if (current_fill > 0.5):
            if (int(dec_arr[k]) != 1):
                print("Supervisor: Incorrect final decision")
                fitness[k] = MAX_TIME + (100*nRobot)
                dec_counter[k] = 1
        elif (current_fill < 0.5):
            if (int(dec_arr[k]) != 0):
                print("Supervisor: Incorrect final decision")
                fitness[k] = MAX_TIME + (100*nRobot)
                dec_counter[k] = 1

        if (dec_time[k] == 0) or (currentData[10] == '-'):
            print("Supervisor: Robot " + str(k) + " did not make a decision in time!")
            dec_time[k] = MAX_TIME
            fitness[k] = MAX_TIME + (100*nRobot)
            dec_counter[k] = 1

        fitness[k] = fitness[k] / dec_counter[k] 

    fitOut = sum(fitness)
    print("Supervisor: Final robot fitness array, ", fitness)

    #Used for baseline 
    if (baseline):
        filenameProb = "Data/" + "Temp" + seedIn + "/" + "runProb.csv"
        filenamePos = "Data/" + "Temp" + seedIn + "/" + "runPos.csv"
        decname = "Data/" + "Temp" + seedIn + "/" + "decTime.txt"

        #writing to csv file
        with open(filenameProb, 'w') as csvfile:
            # creating a csv writer object
            csvwriter = csv.writer(csvfile)

            # writing the data rows``
            csvwriter.writerows(csvProbData)

        with open(filenamePos, 'w') as csvfile:
            # creating a csv writer object
            csvwriter = csv.writer(csvfile)

            # writing the data rows
            csvwriter.writerows(csvPosData)
        
        time_arr = np.append(time_arr, fitOut)
        time_arr = np.append(time_arr, reset_counter)
        np.savetxt(decname, time_arr, delimiter=',')
 
    else:

        # USED ONLY FOR PSO LAUNCH

        if (working_dir is not None):
            os.chdir(working_dir)
            with open(working_dir + "/local_fitness.txt", 'w') as f:
                f.write(str(fitOut))
                f.write('\n')
        else:
            with open("local_fitness.txt", 'w') as f:
                f.write(str(fitOut))
                f.write('\n')
        

        #Write the fitness file into the local dir only when number of runs are done
        if (working_dir is not None):
            print("Supervisor: wrote file " +  working_dir + "/local_fitness")
        else:
            print("wrote file: local_fitness")

    print("Supervisor: cleaning up simulation")
    #supervisor.simulationSetMode(supervisor.SIMULATION_MODE_PAUSE)
    supervisor.simulationQuit(0)

def check_robot_bound(xPos, yPos, me_index):
    global reset_flag
    global reset_counter
    me_pos = [xPos, yPos]
    for j in range(nRobot):
        if (me_index != j):
            other_pos = [trans_value_array[j][2], trans_value_array[j][0]]
            if (math.dist(me_pos, other_pos) < 0.01):
                reset_counter = reset_counter + 1
                print("Supervisor: RESET POSITIONS")
                reset_flag = 1
            
            

def randomizePosition():
    initialX = []
    initialY = []
    for i in range(nRobot):
            while(1):
                x = random.uniform(0.05,0.95)
                y = random.uniform(0.05,0.95)
                if ((x not in initialX) and (y not in initialY)):
                    initialX.append(x)
                    initialY.append(y)
                    break

    for i in range(nRobot):
        INITIAL = [initialX[i], 0.025, initialY[i]]
        POSE = [0, 1, 0, random.uniform(0, 2*math.pi)]
        trans_field_array[i].setSFVec3f(INITIAL)
        #rot_field_array[i].setMFVec3f(POSE)

# --------------------------------------------------------------------

for i in range(nRobot):
    rov_node_array[i] = supervisor.getFromDef(defArray[i])
    trans_field_array[i] = rov_node_array[i].getField("translation")
    rot_field_array[i] = rov_node_array[i].getField("rotation")
    trans_value_array[i] = trans_field_array[i].getSFVec3f()
    data_array[i] = rov_node_array[i].getField("customData")

sim_time = supervisor.getTime()

with open(working_dir + '/fill_log.txt') as file:
    input = [line.rstrip() for line in file]
fill_array = [float(i) for i in input]
print("Supervisor: Fill Array, ", fill_array)
print("Supervisor: Fill Index, ", fillIndex)
fill_ratio = fill_array[fillIndex]
print("Supervisor: Initial fill ratio, ", fill_ratio)

setSeed()

while supervisor.step(timestep) != -1:

    if reset_flag:
        randomizePosition()
        supervisor.simulationResetPhysics()
        supervisor.simulationSetMode(supervisor.SIMULATION_MODE_FAST)
        reset_flag = 0
    else:
        rowProbData = []
        rowPosData = []
        rowPosData.append(supervisor.getTime())
        for i in range(nRobot):
            trans_value_array[i] = trans_field_array[i].getSFVec3f()
            # Save position data
            robot_x = trans_value_array[i][2]
            robot_y = trans_value_array[i][0]
            rowPosData.append(robot_x)
            rowPosData.append(robot_y)
            currentData = data_array[i].getSFString()
            belief = currentData[2:9]
            rowProbData.append(float(belief))
            dec_arr[i] = int(currentData[1])
            check_robot_bound(robot_x, robot_y, i)
            
            #Check the robots current environment, change if needed. 
            fillIndex = int(currentData[0])
            fill_ratio = fill_array[fillIndex]

            if (currentData[10] != '-'):
                # print("Current decision time: ", float(currentData[9:]))

                #First time fitness evaluation
                if (fitness[i] == 0):
                    fitness[i] = evaluateFitness(float(currentData[10:]), dec_arr[i], fill_ratio)
                    print("Supervisor: Initial decision", str(fitness[i]))
                    dec_time[i] = float(currentData[10:])
                    print("Supervisor: Decision time set as, ", dec_time[i])
                    dec_counter[i] = dec_counter[i] + 1

                # Evaluate fitness to new time. 
                elif (dec_time[i] != float(currentData[10:])):
                    # print("Old decision time: ", dec_time[i])
                    # print("New decision time: ", currentData)
                    fitness[i] = fitness[i] + evaluateFitness(float(currentData[10:]), dec_arr[i], fill_ratio)
                    dec_time[i] = float(currentData[10:])
                    print("Supervisor: Updated Robot Fitness, ", fitness)
                    dec_counter[i] = dec_counter[i] + 1

            # if (fillIndex != int(currentData[0])):
            #     fillIndex = int(currentData[0])
            #     print("Supervisor: Using fill index, ", fillIndex)
                
        # print("Supervisor: supervisor fill index, ", fillIndex)
        # print("Supervisor: robot fill index, ", currentData[0])
        # if (fillIndex != int(currentData[0])):
        #         fillIndex = int(currentData[0])
        #         print("Supervisor: Using Fill Index, ", fillIndex)
        #         fill_ratio = fill_array[fillIndex]
        #         print("Supervisor: Changing fill ratio to, ", fill_ratio)
        
        csvProbData.append(rowProbData)
        csvPosData.append(rowPosData)
        control_count = control_count + 1



        if (supervisor.getTime() - sim_time > MAX_TIME) or (time.time()-start_time > WALL_TIME):
            print("Supervisor: Simulation ending. . . cleaning up")
            #if the robots have not decided then assigned 15 min to decision times.
            # for k in range(nRobot):
            #     if dec_time[k] == 0:
            #         print("Supervisor: Robot " + str(k) + " did not make a decision in time!")
            #         dec_time[k] = supervisor.getTime()
            #         fitness[k] = supervisor.getTime()
            #         dec_counter[k] = 1
            #     elif (dec_time[i] != float(currentData[10:])):
            #         print("Supervisor: Final evaluation of Robot " + str(k))
            #         fitness[k] = evaluateFitness(float(currentData[10:]), float(belief))
            #     # else:
            #     #     print("Supervisor: Final evaluation of Robot " + str(k))
            #     #     fitness[k] = evaluateFitness(float(currentData[9:]), float(belief))
            #     # The final fitness is the average of fitnesses over all the decisions made.

            cleanup(dec_time, fitness)
                