
# Code heavily sourced from Johannes Boghaert's Masters Thesis:
# "Decentralized Collective Decision-Making Algorithms in Simulated Soft-Bodied Robot Swarms for 3D Surface Inspection in Space"

import math
import shutil
import numpy as np
import random 
from PIL import Image, ImageDraw

class WorldGenerator():
    """
    Generates the .wbt folder based an input seed.

    Inputs:
        - world_seed 
        - robot_seed
        - robot_number
    Output:
        - A single .wbt file that is specific to the given seed.
    """

    def __init__(self, world_seed=0, robot_seed=0, robot_number=4, path=None):
        self.world_seed = world_seed
        self.robot_seed = robot_seed
        self.robot_number = robot_number
        self.path = path

        #This will store the intial positions of the robots.
        self.initialX = [] 
        self.initialY = []

        random.seed(self.robot_seed)

    def checkCoord(x, y, array):
      #Iterates through 
      for coord in array:
          if ((coord[0] == x) & (coord[1] == y)):
              return 0
      
      return 1

    def createArena(self):

      fill = []
      with open('/usr/local/efs/demo/fill_array.txt') as fillfile:
        for line in fillfile:
          fill.append(float(line.rstrip()))

      picDim = 128
      fillRatio = fill[self.world_seed]

      print("Generating Arena with Fill Ratio: ", fillRatio)

      random.seed(self.world_seed) 

      sqSize = 8
      picArea = picDim * picDim
      sqArea = sqSize * sqSize
      fillCount = math.ceil((fillRatio * picArea) / sqArea)
      startArray = np.zeros((fillCount,2)) #Defines bottom left of white square
      possibleX = list(range(0, picDim, sqSize))
      possibleY = list(range(0, picDim, sqSize))
      i = 0

      while i < fillCount:
          rX = random.randint(0, len(possibleX)-1)
          rY = random.randint(0, len(possibleY)-1)

          if (self.checkCoord(possibleX[rX], possibleY[rY], startArray)):
              startArray[i][0] = possibleX[rX]
              startArray[i][1] = possibleY[rY]
              i = i + 1

      #Save arena file to instance id specific path
      np.savetxt(self.path + '/arena.csv', startArray.astype(int), delimiter=',', fmt='%d')


    def createPos(self):
        for i in range(self.robot_number):
            while(1):
                x = random.uniform(0.05,0.95)
                y = random.uniform(0.05,0.95)
                if ((x not in self.initialX) and (y not in self.initialY)):
                    self.initialX.append(x)
                    self.initialY.append(y)
                    break

    def createTitle(self):
        title = "bayesian_rovables_sim_"
        title += str(self.robot_seed)

        return title

    def createHeader(self, file):
        file.write("""#VRML_SIM R2021b utf8

# Author: Johannes Boghaert, Darren Chiu\n""")

    def createEnv(self, file):
        file.write(
        """
WorldInfo {
  CFM 0.1
  ERP 0.1
  basicTimeStep 8
  coordinateSystem "NUE"
  contactProperties [
    ContactProperties {
      material2 "WheelMat"
    }
  ]
}
Viewpoint {
  orientation -0.37410009861715926 -0.8017314106520007 -0.4661285888985836 2.0110979679680656
  position -0.4573118151367981 1.0734694097374347 0.21413139964469322
}
TexturedBackground {
}
TexturedBackgroundLight {
}
DEF surface Solid {
  translation 0.5 0 0.5
  rotation 0 -0.9999999999999999 0 1.5707953071795862
  children [
    Shape {
      appearance Appearance {
        texture ImageTexture {
        }
      }
      geometry Plane {
      }
    }
  ]
  contactMaterial "Metal"
  boundingObject Plane {
  }
}
Wall {
  translation 0.5 0 -0.015
  size 1 0.05 0.025
}
Wall {
  translation 0.5 0 1.015
  name "wall(1)"
  size 1 0.05 0.025
}
Wall {
  translation 1.015 0 0.5
  rotation 0 1 0 1.5708
  name "wall(2)"
  size 1 0.05 0.025
}
Wall {
  translation -0.015 0 0.5
  rotation 0 1 0 1.5708
  name "wall(3)"
  size 1 0.05 0.025
}\n""")
    
    def createRobots(self, file):
        arg = "\"" + str(self.robot_seed) + "\""
        file.write(
        """Robot {
  name "Bayes Bot Supervisor"
  controller "bayes_supervisor"
  controllerArgs """ + arg + """
  supervisor TRUE
}\n""")

        for i in range(self.robot_number):
            rov_number = str(i)
            file.write(
            """DEF rov_""" + rov_number + """ Rovable {
  translation """ + str(self.initialX[i]) + """ 0.023 """ + str(self.initialY[i]) + """
  rotation 1 0 0 -1.5707953071795862
  name "r""" + rov_number + """"
  controller "bayes_fsm"
  controllerArgs """ + arg + """
  supervisor TRUE
  customData "0001.000000"
}\n""")

    def createWorld(self):
        if (self.path is None):
          file = open(r"../worlds/" + self.createTitle() + ".wbt", 'w')
        else:
          file = open(self.path + self.createTitle() + ".wbt", 'w')
        #Start with Header
        self.createHeader(file)

        #Create the bounding box 
        self.createEnv(file)

        self.createPos()

        #Creates the number of Rovables in a randomized position
        self.createRobots(file)

        print("World Written with Seed: " + str(self.robot_seed))

        file.close()

        self.createArena()