"""vibration_controller controller."""

from cgitb import reset
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
MAX_TIME = 1500 #unit is in seconds, 2700 is around 45 minutes.
WALL_TIME = 600
#2700 45 min good?
seedIn = 0
baseline = 0
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

print(os.name)
print(platform.system())

fill_ratio = os.getenv("FILL_RATIO")
if (fill_ratio is None):
    fill_ratio = 0.70
print("Supervisor Fill Ratio: ", fill_ratio)

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
    print("Using Supervisor Seed: ", seedIn)
    random.seed(seedIn)

def evaluateFitness(dec_time, last_belief):
    # Exp Fitness Function
    # if (float(fill_ratio) > 0.5):
    #     if (last_belief < 0.01):
    #         sign = -1
    #     else:
    #         print("Robot: " + str(i) + " incorrect decision")
    #         sign = 1
    # else:
    #     if (last_belief > 0.99):
    #         sign = -1
    #     else:
    #         print("Robot: " + str(i) + " incorrect decision")
    #         sign = 1
    # return math.exp(((MAX_TIME * 1.66667e-5)- (dec_time*1.66667e-5))*(sign))

    #Linear Fitness Function
    if (float(fill_ratio) > 0.5):
        if (last_belief < 0.5):
            return dec_time
        else: 
            print("Punished with max time")   
            return dec_time + MAX_TIME
    else:
        if (last_belief > 0.5):
            return dec_time
        else: 
            print("Punished with max time")   
            return dec_time + MAX_TIME

# Writes to the fitness file for the current iteration of particle
def cleanup(time_arr, fitness):
    global seedIn

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

        np.savetxt(decname, time_arr, delimiter=',')
 
    else:
        fitOut = sum(fitness)
        if (fitOut > MAX_TIME*nRobot):
            fitOut = (MAX_TIME*nRobot) + (100 * nRobot)
        print("Fitness of particle: ", fitOut)

        # USED ONLY FOR PSO LAUNCH

        value = os.getenv("WB_WORKING_DIR")
        if (value is not None):
            os.chdir(value)
            with open(value + "/local_fitness.txt", 'w') as f:
                f.write(str(fitOut))
                f.write('\n')
        else:
            with open("local_fitness.txt", 'w') as f:
                f.write(str(fitOut))
                f.write('\n')
        

        #Write the fitness file into the local dir only when number of runs are done
        if (value is not None):
            print("Wrote file: " +  value + "/local_fitness")
        else:
            print("wrote file: local_fitness")

    print("Ceaning up simulation")
    #supervisor.simulationSetMode(supervisor.SIMULATION_MODE_PAUSE)
    supervisor.simulationQuit(0)

def check_robbot_bound(xPos, yPos, me_index):
    global reset_flag
    me_pos = [xPos, yPos]
    for j in range(nRobot):
        if (me_index != j):
            other_pos = [trans_value_array[j][2], trans_value_array[j][0]]
            if (math.dist(me_pos, other_pos) < 0.025):
            # if (math.dist(me_pos, other_pos) < 0.00006):
                # print(math.dist(me_pos, other_pos))
                # print(me_pos, other_pos)
                # print(me_index, j)
                print("RESET POSITIONS")
                reset_flag = 1
                #randomizePosition()
            
            

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
    init_data = '0.500000-'
    data_array[i].setSFString(init_data) #Init custom data to required format

sim_time = supervisor.getTime()
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

        for i in range(nRobot):
            trans_value_array[i] = trans_field_array[i].getSFVec3f()
            # Save position data
            robot_x = trans_value_array[i][2]
            robot_y = trans_value_array[i][0]
            rowPosData.append(robot_x)
            rowPosData.append(robot_y)
            currentData = data_array[i].getSFString()
            belief = currentData[0:7]
            rowProbData.append(float(belief))
            check_robbot_bound(robot_x, robot_y, i)

            if (currentData[8] != '-'):
                if (fitness[i] == 0):
                    fitness[i] = fitness[i] + evaluateFitness(float(currentData[8:]), float(belief))
                dec_time[i] = currentData[8:]
                if (dec_time[i] != float(currentData[8:])):
                    fitness[i] = fitness[i] + evaluateFitness(float(currentData[8:]), float(belief))
                    dec_time[i] = currentData[8:]

        csvProbData.append(rowProbData)
        csvPosData.append(rowPosData)
        control_count = control_count + 1



        if (supervisor.getTime() - sim_time > MAX_TIME) or (time.time()-start_time > WALL_TIME):
            #if the robots have not decided then assigned 15 min to decision times.
            for k in range(nRobot):
                if dec_time[k] == 0:
                    print("Robot did not make decision in time!")
                    dec_time[k] = supervisor.getTime()
                    fitness[i] = fitness[i] + supervisor.getTime()
            print("Decision Times: ", dec_time)
            cleanup(dec_time, fitness)
                