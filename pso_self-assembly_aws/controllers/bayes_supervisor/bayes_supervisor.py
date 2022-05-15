"""vibration_controller controller."""

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor

# List out all python /cPP libraries
from controller import Supervisor
import csv
import random
import numpy as np
from decimal import Decimal
# MODIFIED FOR AWS LAUNCH
import time
import sys

# MODIFIED FOR AWS LAUNCH, MAX_TIME IS IN SECONDS, FROM PREVIOUS EXPERIMENTS 140 SECONDS IS ROUGHLY ENOUGH
MAX_TIME = 30

nRobot = 4
boxSize = 3
imageDim = 128
minD = 0.15
endTime = 180
settlingTime = 0
endTic = 100
initialPos = []
csvProbData = []
csvPosData = []
seedIn = str(sys.argv[1])

boxData = []
file = open("boundary/boxrect_" + seedIn + ".csv")
csvreader = csv.reader(file)
for row in csvreader:
    boxData.append(row)

def cleanup():
    supervisor.simulationSetMode(supervisor.SIMULATION_MODE_PAUSE)
    supervisor.simulationReset()

    for rov in rov_node_array:
        rov.restartController()
    
    filenameProb = "Data/" + "Temp" + seedIn + "/" + "runProb.csv"
    filenamePos = "Data/" + "Temp" + seedIn + "/" + "runPos.csv"

    # writing to csv file
    with open(filenameProb, 'w') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)

        #Write the header
        #csvwriter.writerow(defArray)

        # writing the data rows
        csvwriter.writerows(csvProbData)

    with open(filenamePos, 'w') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)

        #Write the header
        #csvwriter.writerow(defArray)

        # writing the data rows
        csvwriter.writerows(csvPosData)

    print("Cleaning up Simulation")
    supervisor.simulationQuit(0)


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


def get_color(xPos, yPos):
    for coord in boxData:
        # Data is stored in (x, y)
        if ((xPos >= int(coord[0])/imageDim) and (xPos <= (((int(coord[0]) + boxSize - 1)/imageDim))) and (yPos >= int(coord[1])/imageDim) and (yPos <= (((int(coord[1]) + boxSize - 1)/imageDim)))):
            return 1
    return 0


# create the Robot instance.
supervisor = Supervisor()

# get the time step of the current world.
timestep = int(supervisor.getBasicTimeStep())

defArray = ["rov_0", "rov_1", "rov_2", "rov_3"]

rov_node_array = np.empty(nRobot, dtype=object)
trans_field_array = np.empty(nRobot, dtype=object)
data_array = np.empty(nRobot, dtype=object)
trans_value_array = np.empty(nRobot, dtype=object)
color_array = np.empty(nRobot, dtype=object)

#randomizePosition()

# MODIFIED FOR AWS LAUNCH
# Get the current time
start_time = time.time()

for i in range(nRobot):
    rov_node_array[i] = supervisor.getFromDef(defArray[i])
    trans_field_array[i] = rov_node_array[i].getField("translation")
    # INITIAL = [random.uniform(0.05,0.95), 0.023, random.uniform(0.05,0.95)]
    # trans_field_array[i].setSFVec3f(INITIAL)
    #trans_field_array[i].setSFVec3f(initialPos[i])
    data_array[i] = rov_node_array[i].getField("customData")
    data_array[i].setSFString('0000.000000') #Init custom data to required format

while supervisor.step(timestep) != -1:
    rowProbData = []
    rowPosData = []

    for i in range(nRobot):
        trans_value_array[i] = trans_field_array[i].getSFVec3f()
        rowPosData.append(trans_value_array[i][2])
        rowPosData.append(trans_value_array[i][0])
        color_array[i] = str(get_color(trans_value_array[i][2], trans_value_array[i][0]))
        #print(data_array[i].getSFString())
        remaining = (data_array[i].getSFString())[1:]
        probability = remaining[2:8]
        #if probability: #Checks if the string is blank.
        rowProbData.append(float(probability))
        newString = color_array[i] + remaining
        data_array[i].setSFString(newString)

    csvProbData.append(rowProbData)
    csvPosData.append(rowPosData)

    #print(rowProbData)

    if(supervisor.getTime() > 80):
        if ((sum(rowProbData) > 3.9) or (sum(rowProbData) < 0.1)) and settlingTime <= endTic:
            settlingTime = settlingTime + 1
        elif ((sum(rowProbData) > 3.9) or (sum(rowProbData) < 0.1)) and settlingTime > endTic:
            cleanup()
        else:
            settlingTime = 0


    # MODIFIED FOR AWS LAUNCH
    #if (supervisor.getTime() > endTime):
    #   cleanup()
    if (time.time()-start_time > MAX_TIME):
       #supervisor.simulationQuit(0)
        cleanup()

# MODIFIED FOR AWS LAUNCH
# Enter here exit cleanup code.
# cleanup()
