from tracemalloc import start
from PIL import Image, ImageDraw #Pillow library
import math
import random
import numpy as np
import argparse
import subprocess
import time
import os
import shutil

# Arguments
parser = argparse.ArgumentParser(description="Generates grid for Bayes Bot algorithm")

# For world
parser.add_argument("-fr", "--fill_ratio", required=False, type=float, default="0.55", help="Fill ratio of generated picture and coordinates")
parser.add_argument("-ss", "--square_size", required=False, type=int, default="5", help="Determines the size of generated squares")
parser.add_argument("-sd", "--seed", required=False, type=int, default="16", help="Seed for random generation of map")
parser.add_argument("-rs", "--robot_seed", required=False, type=int, default="0", help="Seed that is used for the robot random walk a placement for this experiment")

args = parser.parse_args()

def checkCoord(x, y, array):
    #Iterates through 
    for coord in array:
        if ((coord[0] == x) & (coord[1] == y)):
            return 0
    
    return 1

saveFile = 1
picDim = 128
fillRatio = 0.55
sqSize = 4 #4 or 8 works best

random.seed(0) 

img = Image.new('1', (picDim, picDim))
picArea = picDim * picDim
sqArea = sqSize * sqSize
fillCount = math.ceil((fillRatio * picArea) / sqArea)
print(fillCount)
startArray = np.zeros((fillCount,2)) #Defines bottom left of white square
possibleX = list(range(0, picDim, sqSize))
possibleY = list(range(0, picDim, sqSize))
i = 0

while i < fillCount-1:
    rX = random.randint(0, len(possibleX)-1)
    rY = random.randint(0, len(possibleY)-1)

    if (checkCoord(possibleX[rX], possibleY[rY], startArray)):
        startArray[i][0] = possibleX[rX]
        startArray[i][1] = possibleY[rY]
        i = i + 1

draw = ImageDraw.Draw(img)
for coord in startArray:
    draw.rectangle((coord[0], coord[1] + (sqSize - 1), coord[0] + (sqSize - 1), coord[1]), fill=1)

img = img.transpose(method=Image.FLIP_TOP_BOTTOM) #Flip to account for axis change in Webots

img.show()
#print("CURRENT DIRECTORY: " + str(os.getcwd()))
#savedFile = "boxrect_" + str(args.robot_seed)
#saveDir = "../worlds/textures/" + "boxrect_" + str(args.robot_seed) + ".png"
#img.save("box8_055.png", quality=100)
np.savetxt(str(sqSize) + "_" + str(fillRatio) + "_" + str(args.robot_seed) + '.csv', startArray.astype(int), delimiter=',', fmt='%d')
