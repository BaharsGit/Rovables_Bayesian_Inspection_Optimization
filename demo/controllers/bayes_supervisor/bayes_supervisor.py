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
MAX_TIME = 2700 #unit is in seconds, corresponds to 2 mintues -- 7200 seconds
#2700 45 min good?
baseline = 0
run = 0
n_run = 5
nRobot = 4
boxSize = 8    
imageDim = 128
p_high = 0.9
p_low = 0.1
minD = 0.15
settlingTime = 0
initialPos = []
csvProbData = []
csvPosData = []
parameters = []
seedPtr = os.getenv("NOISE_SEED")
if (seedPtr is not None):
    #PSO 
    print("Supervisr seed: " + seedPtr)
    random.seed(seedPtr)
else:
    #BASELINE
    seedIn = str(sys.argv[1])
    print("Using Run: ", seedIn)
    random.seed(seedIn)
boxData = []
accuracy = []
dec_time = np.zeros(nRobot)
time_track = np.zeros(nRobot)
dec_hold = np.zeros(nRobot)
coverage_arr = []
fitnessData = np.zeros(3) # Decision Time | Coverage | Accuracy
start_time = time.time()
sim_time = 0
control_count = 0
fitness = np.zeros(nRobot)


print(os.name)
print(platform.system())

value = os.getenv("WB_WORKING_DIR")
fill_ratio = os.getenv("FILL_RATIO")
if (fill_ratio is None):
    fill_ratio = 0.55
print("Supervisor Fill Ratio: ", fill_ratio)

# sqArea = boxSize * boxSize
# possibleX = list(range(0, imageDim, boxSize))
# possibleY = list(range(0, imageDim, boxSize))
# grid = np.zeros((len(possibleY), len(possibleX)))

# fitnessFile = "local_fitness.txt"
# inputFile = "prob.txt"

defArray = ["rov_0", "rov_1", "rov_2", "rov_3"]

rov_node_array = np.empty(nRobot, dtype=object)
trans_field_array = np.empty(nRobot, dtype=object)
rot_field_array = np.empty(nRobot, dtype=object)
data_array = np.empty(nRobot, dtype=object)
trans_value_array = np.empty(nRobot, dtype=object)
color_array = np.empty(nRobot, dtype=object)

# --------------------------------------------------------------
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
        if (last_belief < 0.01):
            return dec_time
        else: 
            print("Punished with max time")   
            return dec_time + MAX_TIME
    else:
        if (last_belief > 0.99):
            return dec_time
        else: 
            print("Punished with max time")   
            return dec_time + MAX_TIME

# def checkDecision(data):
#     pSum = 0
#     for p in data:
#         if (p > p_low and p < p_high):
#             return 0
#         else:
#             pSum = pSum + p
    
#     if (pSum <= 4*0.1 or pSum >= 4*0.9):
#         return 1
#     else:
#         return 0

# Writes to the fitness file for the current iteration of particle
def cleanup(time_arr, fitness):

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
        fitOut = sum(fitness)/nRobot
        print("Fitness of particle: ", fitOut)

        # USED ONLY FOR PSO LAUNCH
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

# def get_pos(xPos, yPos):
#     ix = int(int(xPos*imageDim)/boxSize)
#     iy = int(int(yPos*imageDim)/boxSize)
#     grid[ix-1][iy-1] = 1

def randomizePosition():
    for i in range(nRobot):
        INITIAL = [random.uniform(0.05,0.95), 0.023, random.uniform(0.05,0.95)]
        POSE = [0, 1, 0, random.uniform(0, 2*math.pi)]
        trans_field_array[i].setSFVec3f(INITIAL)
        #rot_field_array[i].setMFVec3f(POSE)

# --------------------------------------------------------------------

# create the Robot instance.
supervisor = Supervisor()

# get the time step of the current world.
timestep = int(supervisor.getBasicTimeStep())

for i in range(nRobot):
    rov_node_array[i] = supervisor.getFromDef(defArray[i])
    trans_field_array[i] = rov_node_array[i].getField("translation")
    rot_field_array[i] = rov_node_array[i].getField("rotation")
    trans_value_array[i] = trans_field_array[i].getSFVec3f()
    data_array[i] = rov_node_array[i].getField("customData")
    init_data = '0.500000-'
    data_array[i].setSFString(init_data) #Init custom data to required format

sim_time = supervisor.getTime()

while supervisor.step(timestep) != -1:
    rowProbData = []
    rowPosData = []

    for i in range(nRobot):
        trans_value_array[i] = trans_field_array[i].getSFVec3f()
        # Save position data 
        rowPosData.append(trans_value_array[i][2])
        rowPosData.append(trans_value_array[i][0])
        currentData = data_array[i].getSFString()
        remaining = currentData[1:]
        probability = currentData[0:7]
        rowProbData.append(float(probability))

        if (currentData[8] != '-'):
            if (fitness[i] == 0):
                fitness[i] = fitness[i] + evaluateFitness(float(currentData[8:]), float(probability))
            dec_time[i] = currentData[8:]
            if (dec_time[i] != float(currentData[8:])):
                # print("ADD")
                # print("Dec Time: ", dec_time[i])
                # print("Current Data: ", currentData[8:])
                fitness[i] = fitness[i] + evaluateFitness(float(currentData[8:]), float(probability))
                dec_time[i] = currentData[8:]

    csvProbData.append(rowProbData)
    csvPosData.append(rowPosData)
    control_count = control_count + 1


    if (supervisor.getTime() - sim_time > MAX_TIME):
        #if the robots have not decided then assigned 15 min to decision times.
        for k in range(nRobot):
            if dec_time[k] == 0:
                dec_time[k] = supervisor.getTime()
                fitness[i] = fitness[i] + evaluateFitness(supervisor.getTime(), float(probability))
        print("Decision Times: ", dec_time)
        cleanup(dec_time, fitness)
                