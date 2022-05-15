
## MESH SCRIPT -> associate between nodes of 2D surface and 3D mesh. Take a look at Meshing software. 
from tracemalloc import start
from PIL import Image, ImageDraw #Pillow library
import math
import random
import numpy as np

genMethod = "flat"


def checkCoord(x, y, array):
    #Iterates through 
    for coord in array:
        if ((coord[0] == x) & (coord[1] == y)):
            return 0
    
    return 1


saveFile = 1
picDim = 128
fillRatio = 0.1
a = 0
b = 25

img = Image.new('1', (picDim, picDim))
sqSize = 4
picArea = picDim * picDim
sqArea = sqSize * sqSize
fillCount = math.ceil((fillRatio * picArea) / sqArea)
startArray = np.zeros((fillCount,2)) #Defines bottom left of white square
possibleX = list(range(0, picDim, sqSize))
possibleY = list(range(0, picDim, sqSize))
i = 0
print(possibleX)

# Generate coordinates of white squares.
# while i < fillCount:
#     rX = random.randint(0, len(possibleX)-1)
#     rY = random.randint(0, len(possibleY)-1)

#     if (checkCoord(possibleX[rX], possibleY[rY], startArray)):
#         startArray[i][0] = possibleX[rX]
#         startArray[i][1] = possibleY[rY]
#         i = i + 1

draw = ImageDraw.Draw(img)


# for coord in startArray:
#     draw.rectangle((coord[0], coord[1] + (sqSize - 1), coord[0] + (sqSize - 1), coord[1]), fill=1, outline=1)

draw.rectangle((0, 5, 5, 0), fill=1, outline=1)
draw.rectangle((123, 128, 128, 123), fill=1, outline=1)

img = img.transpose(method=Image.FLIP_TOP_BOTTOM) #Flip to account for axis change in Webots

img.show()
img.save('worlds/textures/test_cyl.png', quality=100)
np.savetxt('controllers/bayes_supervisor/box.csv', startArray.astype(int), delimiter=',', fmt='%d')