"""vibration_controller controller."""

#from tracemalloc import startF
from controller import Supervisor
import os
import csv
import math
import random
import numpy as np
from decimal import Decimal
# MODIFIED FOR AWS LAUNCH
import time
import sys

# MODIFIED FOR AWS LAUNCH, MAX_TIME IS IN SECONDS, FROM PREVIOUS EXPERIMENTS 140 SECONDS IS ROUGHLY ENOUGH
MAX_TIME = 900
run = 0
n_run = 5
nRobot = 4
boxSize = 16
imageDim = 128
fillRatio = 0.55
p_high = 0.9
p_low = 0.1
minD = 0.15
settlingTime = 0
initialPos = []
csvProbData = []
csvPosData = []
parameters = []
#PSO
seedPtr = os.getenv("NOISE_SEED")
if (seedPtr is not None):
    print("Supervisr seed: " + seedPtr)
    random.seed(seedPtr)
else:
    random.seed(time.time())
#BASELINE
#seedIn = str(sys.argv[1])
# print("Using Run: ", seedIn)
boxData = []
accuracy = []
dec_time = np.zeros(nRobot)
dec_hold = np.zeros(nRobot)
coverage_arr = []
fitnessData = np.zeros(3) # Decision Time | Coverage | Accuracy
start_time = time.time()
sim_time = 0
control_count = 0
newReset = 0

value = os.getenv("WB_WORKING_DIR")
if (value is not None):
    os.chdir(value)
    with open(value + "/prob.txt") as f:
        parameters = f.read().splitlines()
else:
    with open("prob.txt") as f:
        parameters = f.read().splitlines()

#print(parameters)
tao = 1500
holdTime = float(parameters[3])
print("Supervisr Hold Time: " + str(holdTime))
sqArea = boxSize * boxSize
possibleX = list(range(0, imageDim, boxSize))
possibleY = list(range(0, imageDim, boxSize))
grid = np.zeros((len(possibleY), len(possibleX)))

fitnessFile = "local_fitness.txt"
inputFile = "prob.txt"

defArray = ["rov_0", "rov_1", "rov_2", "rov_3"]

rov_node_array = np.empty(nRobot, dtype=object)
trans_field_array = np.empty(nRobot, dtype=object)
data_array = np.empty(nRobot, dtype=object)
trans_value_array = np.empty(nRobot, dtype=object)
color_array = np.empty(nRobot, dtype=object)

# --------------------------------------------------------------
def checkDecision(data):
    pSum = 0
    for p in data:
        if (p > p_low and p < p_high):
            return 0
        else:
            pSum = pSum + p
    
    if (pSum <= 4*0.1 or pSum >= 4*0.9):
        return 1
    else:
        return 0

# Writes to the fitness file for the current iteration of particle
def cleanup():
    #print("Fitness: ", supervisor.getTime())
    # filenameProb = "Data/" + "Temp" + seedIn + "/" + "runProb.csv"
    # filenamePos = "Data/" + "Temp" + seedIn + "/" + "runPos.csv"

    # writing to csv file
    # with open(filenameProb, 'w') as csvfile:
    #     # creating a csv writer object
    #     csvwriter = csv.writer(csvfile)

    #     #Write the header
    #     #csvwriter.writerow(defArray)

    #     # writing the data rows``
    #     csvwriter.writerows(csvProbData)

    # with open(filenamePos, 'w') as csvfile:
    #     # creating a csv writer object
    #     csvwriter = csv.writer(csvfile)

    #     #Write the header
    #     #csvwriter.writerow(defArray)

    #     # writing the data rows
    #     csvwriter.writerows(csvPosData)

    # if (fillRatio > 0.50):
    #     run_dec = int(all(i < 0.5 for i in rowProbData))
    # else:
    #     run_dec = int(all(i > 0.5 for i in rowProbData))
    # print("Run Correct: ", run_dec)
    # _, counts = np.unique(grid, return_counts=True)
    # coverage_arr.append(counts[1] / (imageDim * imageDim))
    # accuracy.append(run_dec)

    # _, counts = np.unique(grid, return_counts=True)
    # fitnessData[0] = sum(dec_time) / n_run
    # fitnessData[1] = sum(coverage_arr) / n_run
    # fitnessData[2] = sum(accuracy) / n_run

    fitness = sum(dec_time)/nRobot
    print("Fitness of particle: ", fitness)

    # USED ONLY FOR PSO LAUNCH
    if (value is not None):
        os.chdir(value)
        with open(value + "/local_fitness.txt", 'w') as f:
            f.write(str(fitness))
            f.write('\n')
            # for line in fitnessData:
            #     f.write(str(line))
            #     f.write('\n')
    else:
        with open("local_fitness.txt", 'w') as f:
            f.write(str(fitness))
            f.write('\n')
            # for line in fitnessData:
            #     f.write(str(line))
            #     f.write('\n')
    

    #Write the fitness file into the local dir only when number of runs are done
    print("Cleaning up Simulation")
    if (value is not None):
        print("Wrote file: " +  value + "/local_fitness")
    else:
        print("wrote file: local_fitness")
    supervisor.simulationQuit(0)

def reset():
    global run
    global start_time
    global sim_time
    global boxData
    global grid
    global control_count
    global newReset

    if (fillRatio > 0.50):
        run_dec = int(all(i < 0.5 for i in rowProbData))

    else:
        run_dec = int(all(i > 0.5 for i in rowProbData))
    #print("Run Correct: ", run_dec)
    _, counts = np.unique(grid, return_counts=True)
    coverage_arr.append(counts[1] / (imageDim * imageDim))
    #dec_time.append(supervisor.getTime())
    accuracy.append(run_dec)

    #Restart only the rovable controller
    for rov in rov_node_array:
        rov.restartController()

    initialPos = []
    csvProbData = []
    csvPosData = []
    boxData = []
    control_count = 0
    grid = np.zeros((len(possibleY), len(possibleX)))

    start_time = time.time()
    sim_time = supervisor.getTime()
    run = run + 1
    print("Running Noise Resistance Iteration Number: ", run)
    supervisor.simulationReset()
    newReset = 1
    supervisor.simulationSetMode(supervisor.SIMULATION_MODE_FAST)

def get_pos(xPos, yPos):
    ix = int(int(xPos*imageDim)/boxSize)
    iy = int(int(yPos*imageDim)/boxSize)
    #print(ix, iy)
    grid[ix-1][iy-1] = 1

def randomizePosition():
    posX = []
    posY = []
    for i in range(nRobot):
        while(1):
            x = random.uniform(0.05,0.95)
            y = random.uniform(0.05,0.95)
            if ((x not in posX) and (y not in posY)):
                posX.append(x)
                posY.append(y)
                break
        initialPos.append([posX[i], 0.023, posY[i]])
    for i in range(nRobot):
        INITIAL = [random.uniform(0.05,0.95), 0.32, random.uniform(0.05,0.95)]
        trans_field_array[i].setSFVec3f(INITIAL)
        trans_field_array[i].setSFVec3f(initialPos[i])

# --------------------------------------------------------------------

# create the Robot instance.
supervisor = Supervisor()

# get the time step of the current world.
timestep = int(supervisor.getBasicTimeStep())

for i in range(nRobot):
    rov_node_array[i] = supervisor.getFromDef(defArray[i])
    trans_field_array[i] = rov_node_array[i].getField("translation")
    trans_value_array[i] = trans_field_array[i].getSFVec3f()
    data_array[i] = rov_node_array[i].getField("customData")
    init_data = '00000.000000'
    #print(init_data)
    data_array[i].setSFString(init_data) #Init custom data to required format

randomizePosition()

# MODIFIED FOR AWS LAUNCH
# Get the current time
start_time = time.time()
sim_time = supervisor.getTime()
supervisor.simulationSetMode(supervisor.SIMULATION_MODE_FAST)

while supervisor.step(timestep) != -1:

    if (newReset):
        randomizePosition()
        newReset = 0
    else:
        #print("----------------------------------------------------------")
        rowProbData = []
        rowPosData = []

        for i in range(nRobot):
            trans_value_array[i] = trans_field_array[i].getSFVec3f()
            rowPosData.append(trans_value_array[i][2])
            rowPosData.append(trans_value_array[i][0])
            if (control_count % tao == 0):
                get_pos(trans_value_array[i][2], trans_value_array[i][0])
            currentData = data_array[i].getSFString()
            remaining = currentData[1:]
            probability = currentData[4:11]
            rowProbData.append(float(probability))
            #newString = color_array[i] + remaining
            # print("Current Data: ", currentData)
            # print("Removed Color: ", remaining)
            # print("Probability: ", probability)
            #print("New String: ", newString)
            #data_array[i].setSFString(newString)

        csvProbData.append(rowProbData)
        csvPosData.append(rowPosData)
        control_count = control_count + 1

        #print(rowProbData)

        #Check if there is a time for all robots
        #if np.all((dec_time != 0)):
        #    print("Decision Times: ", dec_time)
        #    cleanup()


        #Logic for marking time down for each robots decision
        if(supervisor.getTime() - sim_time > 30):
            for k in range(nRobot):
                if (rowProbData[k] > 0.99 or rowProbData[k] < 0.01) and (supervisor.getTime() - dec_hold[k] >= holdTime) and (dec_hold[k] != 0) and (dec_time[k] == 0):
                    #print(supervisor.getTime() - dec_hold[k])
                    if (rowProbData[k] > 0.5):
                        dec_time[k] = supervisor.getTime() + 500
                        print("Robot: " + str(k) + " Penalized with 500 for incorrect evaluation. Finished with time: " + str(dec_time[k]))
                    else:
                        dec_time[k] = supervisor.getTime()
                        print("Robot: " + str(k) + " Finished with time: " + str(dec_time[k]))

                elif (rowProbData[k] < 0.99 and rowProbData[k] > 0.01):
                    dec_hold[k] = supervisor.getTime()
                    


        # # MODIFIED FOR AWS LAUNCH
        # if (supervisor.getTime() > endTime):
        #   cleanup()
        
        #If robots did not make decision after 15 minutes then make them worse case. 
        if (time.time()-start_time > MAX_TIME):
            for k in range(nRobot):
                if dec_time[k] == 0:
                    dec_time[k] = supervisor.getTime()
            print("Decision Times: ", dec_time)
            cleanup()

# MODIFIED FOR AWS LAUNCH
# Enter here exit cleanup code.
# cleanup()
