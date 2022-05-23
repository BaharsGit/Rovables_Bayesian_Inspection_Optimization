"""vibration_controller controller."""

from tracemalloc import start
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

#SUPERVISOR ARGUMENTS READ THROUGH TXT FILE
# ADD IN NOISE PER PARTICLE, FIND FUNCTION TO REVERT WORLD THROUGH SUPERVISOR

# MODIFIED FOR AWS LAUNCH, MAX_TIME IS IN SECONDS, FROM PREVIOUS EXPERIMENTS 140 SECONDS IS ROUGHLY ENOUGH
MAX_TIME = 120
run = 0
n_run = 2
nRobot = 4
boxSize = 4
imageDim = 128
fillRatio = 1.0
p_high = 0.9
p_low = 0.1
minD = 0.15
endTime = 180
settlingTime = 0
endTic = 100
initialPos = []
csvProbData = []
csvPosData = []
parameters = []
seedIn = 0
boxData = []
accuracy = []
dec_time = []
coverage_arr = []
fitnessData = np.zeros(3) # Decision Time | Coverage | Accuracy
start_time = time.time()
sim_time = 0

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
    for p in data:
        if (p > p_low and p < p_high):
            continue
    return 1

def checkCoord(x, y, array):
    #Iterates through 
    for coord in array:
        if ((coord[0] == x) and (coord[1] == y)):
            return 0
    return 1

def genArena():
    random.seed(seedIn) 
    # random.seed(16)

    #img = Image.new('1', (imageDim, imageDim))
    picArea = imageDim * imageDim
    sqArea = boxSize * boxSize
    fillCount = math.ceil((fillRatio * picArea) / sqArea)
    startArray = np.zeros((fillCount,2)) #Defines bottom left of white square
    possibleX = list(range(0, imageDim, boxSize))
    possibleY = list(range(0, imageDim, boxSize))
    
    i = 0
    print("Generating Arena with Fill Ratio: ", fillRatio)
    while i < fillCount-1:
        rX = random.randint(0, len(possibleX)-1)
        rY = random.randint(0, len(possibleY)-1)
        
        if (checkCoord(possibleX[rX], possibleY[rY], startArray)):
            startArray[i][0] = possibleX[rX]
            startArray[i][1] = possibleY[rY]
            i = i + 1
    return startArray, np.zeros((len(possibleY), len(possibleX)))

# Writes to the fitness file for the current iteration of particle
def cleanup():
    supervisor.simulationSetMode(supervisor.SIMULATION_MODE_PAUSE)
    supervisor.simulationReset()

#     #filenameProb = "Data/" + "Temp" + seedIn + "/" + "runProb.csv"
#    # filenamePos = "Data/" + "Temp" + seedIn + "/" + "runPos.csv"

    _, counts = np.unique(grid, return_counts=True)
    fitnessData[0] = sum(dec_time) / n_run
    fitnessData[1] = sum(coverage_arr) / n_run
    fitnessData[2] = sum(accuracy) / n_run

    #Write the fitness file into the local dir only when number of runs are done
    with open(fitnessFile, 'w') as f:
        for line in fitnessData:
            f.write(str(line))
            f.write('\n')
    print("Cleaning up Simulation")
    supervisor.simulationQuit(0)

def reset():
    global run
    global start_time
    global sim_time
    global boxData
    global grid

    if (fillRatio > 0.50):
        run_dec = int(all(i < 0.5 for i in rowProbData))
    else:
        run_dec = int(all(i >= 0.5 for i in rowProbData))
    _, counts = np.unique(grid, return_counts=True)
    coverage_arr.append(counts[1] / (imageDim * imageDim))
    dec_time.append(supervisor.getTime())
    accuracy.append(run_dec)

    #Restart only the rovable controller
    for rov in rov_node_array:
        rov.restartController()

    initialPos = []
    csvProbData = []
    csvPosData = []
    boxData = []

    start_time = time.time()
    sim_time = supervisor.getTime()
    run = run + 1
    print("Running Iteration Number: ")
    print(run)
    randomizePosition()
    #boxData, grid = genArena()
    supervisor.simulationSetMode(supervisor.SIMULATION_MODE_FAST)

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
        INITIAL = [random.uniform(0.05,0.95), 0.023, random.uniform(0.05,0.95)]
        trans_field_array[i].setSFVec3f(INITIAL)
        trans_field_array[i].setSFVec3f(initialPos[i])


def get_color(xPos, yPos):
    for coord in boxData:
        # Data is stored in (x, y)
        if ((xPos >= int(coord[0])/imageDim) and (xPos <= ((int(coord[0]) + boxSize)/imageDim)) and (yPos >= int(coord[1])/imageDim) and (yPos <= ((int(coord[1]) + boxSize)/imageDim))):
            ix = int(int(coord[0])/boxSize)
            iy = int(int(coord[1])/boxSize)
            grid[ix][iy] = 1
            return 1 #Returns 1 if the current robot is on a white square
    print(xPos, yPos)
    return 0

def setParam():
    #Read in parameters used for algorithm
    with open(inputFile) as f:
        parameters = f.readlines()

    print(parameters)
# --------------------------------------------------------------------

# file = open("boundary/boxrect_" + seedIn + ".csv")
# csvreader = csv.reader(file)
# for row in csvreader:
#     boxData.append(row)

# create the Robot instance.
supervisor = Supervisor()

# get the time step of the current world.
timestep = int(supervisor.getBasicTimeStep())
boxData, grid = genArena()


for i in range(nRobot):
    rov_node_array[i] = supervisor.getFromDef(defArray[i])
    trans_field_array[i] = rov_node_array[i].getField("translation")
    trans_value_array[i] = trans_field_array[i].getSFVec3f()
    data_array[i] = rov_node_array[i].getField("customData")
    init_c = str(get_color(trans_value_array[i][2], trans_value_array[i][0]))
    init_data = init_c + '000.000000'
    print(init_data)
    data_array[i].setSFString(init_data) #Init custom data to required format

#randomizePosition()

# MODIFIED FOR AWS LAUNCH
# Get the current time
start_time = time.time()
sim_time = supervisor.getTime()

while supervisor.step(timestep) != -1:
    rowProbData = []
    rowPosData = []

    for i in range(nRobot):
        trans_value_array[i] = trans_field_array[i].getSFVec3f()
        rowPosData.append(trans_value_array[i][2])
        rowPosData.append(trans_value_array[i][0])
        color_array[i] = str(get_color(trans_value_array[i][2], trans_value_array[i][0]))
        currentData = data_array[i].getSFString()
        remaining = currentData[1:]
        probability = currentData[3:11]
        rowProbData.append(float(probability))
        newString = color_array[i] + remaining
        # print("Current Data: ", currentData)
        # print("Removed Color: ", remaining)
        # print("Probability: ", probability)
        # print("New String: ", newString)
        data_array[i].setSFString(newString)

    csvProbData.append(rowProbData)
    csvPosData.append(rowPosData)

    #print(rowProbData)

    # if(supervisor.getTime() - sim_time > 30):
    #     if (checkDecision(rowProbData)) and settlingTime <= endTic:
    #         settlingTime = settlingTime + 1
    #     elif (checkDecision(rowProbData)) and settlingTime > endTic:
    #         if run < n_run-1:
    #             reset()
    #         else:
    #             cleanup()
    #     else:
    #         settlingTime = 0


    # # MODIFIED FOR AWS LAUNCH
    # # if (supervisor.getTime() > endTime):
    # #   cleanup()
    # if (time.time()-start_time > MAX_TIME):
    #    #supervisor.simulationQuit(0)
    #     if run < n_run-1:
    #        reset()
    #     else:
    #        cleanup()

# MODIFIED FOR AWS LAUNCH
# Enter here exit cleanup code.
# cleanup()
