
# Code heavily sourced from Johannes Boghaert's Masters Thesis:
# "Decentralized Collective Decision-Making Algorithms in Simulated Soft-Bodied Robot Swarms for 3D Surface Inspection in Space"

import math
import shutil
import numpy as np
import random 
import os

class WorldGenerator():
    """
    Generates the .wbt folder based an input seed.

    Inputs:
        - particle_id
        - instance_id
        - robot_number
    Output:
        - A single .wbt file that is specific to the given seed.
    """

    def __init__(self, baseline=0, particle_id=0, instance_id=0, fill_ratio= 0.52, robot_number=4, path=None, dynamic_env=0, env_upper=0.55, env_lower=0.45):
        self.baseline = baseline
        self.particle_id = particle_id
        self.instance_id = instance_id
        self.fill_ratio = fill_ratio
        self.robot_number = robot_number
        self.path = path
        self.dynamic_env = dynamic_env
        self.env_upper = env_upper
        self.env_lower = env_lower

        #This will store the intial positions of the robots.
        self.initialX = [] 
        self.initialY = []

        self.orientation = [[1, 0, 0, -1.57], [0.577, 0.577, 0.577, -2.09], [0, 0.707106, 0.707107, 3.14159], [0.577, -0.577, -0.577, -2.09]]

    def checkCoord(self, x, y, array):
    #Iterates through 
      for coord in array:
        if ((coord[0] == x) & (coord[1] == y)):
            return 0
    
      return 1

    def createArena(self):
      #Do not use dynamic environment
      if (self.dynamic_env == 0):
        picDim = 128

        print("Generating Arena with Fill Ratio: ", self.fill_ratio)

        sqSize = 8
        picArea = picDim * picDim
        sqArea = sqSize * sqSize
        fillCount = math.ceil((self.fill_ratio * picArea) / sqArea)
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
        np.savetxt(self.path + '/arena.txt', startArray.astype(int), delimiter=',', fmt='%d', footer="-1")
      else:
        fill_log = [0.3, 0.4, 0.6, 0.7, 0.8]
        for j in range(0, int(self.dynamic_env), 1):

          picDim = 128
          # fill = np.random.uniform(self.env_lower, self.env_upper)
          # fill_log.append(fill)
          fill = fill_log[j]
          print("Generating Arena with Fill Ratio: ", fill)
          sqSize = 8
          picArea = picDim * picDim
          sqArea = sqSize * sqSize
          fillCount = math.ceil((fill * picArea) / sqArea)
          #print("Number of white squares: ", fillCount)
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
          np.savetxt(self.path + '/fill_log.txt', fill_log, delimiter=',')
          np.savetxt(self.path + '/arena_' + str(j) + '.txt', startArray.astype(int), delimiter=',', fmt='%d', footer="-1")


    def createPos(self):
        for i in range(self.robot_number):
            while(1):
                x = random.uniform(0.05,0.95)
                y = random.uniform(0.05,0.95)
                if ((x not in self.initialX) and (y not in self.initialY)):
                    self.initialX.append(x)
                    self.initialY.append(y)
                    break

    def generateRot(self):
      # angle
      rot = str(round(random.uniform(0.0, 2*math.pi), 2))

      return rot

    def createTitle(self):
        title = "/bayes_pso_"
        title += str(self.particle_id)
        title += "_"
        title += str(self.instance_id)

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
        arg = "\"" + str(self.instance_id) + "\""
        arg2 = "\"" + str(self.dynamic_env) + "\""
        baselineArg = "\"" + str(self.baseline) + "\""
        file.write(
        """Robot {
  name "Bayes Bot Supervisor"
  controller "bayes_supervisor"
  controllerArgs [
    """ + arg + """
    """ + baselineArg + """
  ]
  supervisor TRUE
}\n""")

        for i in range(self.robot_number):
            rov_number = str(i)
            index = np.random.randint(0, 4)
            rotationArg = str(self.orientation[index][0]) + " " + str(self.orientation[index][1]) + " " + str(self.orientation[index][2]) + " " + str(self.orientation[index][3]) 
            file.write(
            """DEF rov_""" + rov_number + """ Rovable {
  translation """ + str(self.initialX[i]) + """ 0.023 """ + str(self.initialY[i]) + """
  rotation """ + rotationArg + """
  name "r""" + rov_number + """"
  controller "bayes_fsm"
  controllerArgs [
    """ + arg + """
    """ + arg2 + """
  ]
  supervisor TRUE
  customData "00.500000-" 
  extensionSlot [
    Receiver {
    }
    Emitter {
    }
  ]
}\n""")

    def createWorld(self):
        random.seed(self.instance_id)
        np.random.seed(self.instance_id)

        file = open(r"../../worlds" + self.createTitle() + ".wbt", 'w')
        #file = open(r"/usr/local/efs/demo/worlds" + self.createTitle() + ".wbt", 'w')
        #file = open(r"/home/darren/Documents/ICRA_LAUNCH/Rovables_Bayesian_Inspection_Optimization/demo/worlds" + self.createTitle() + ".wbt", 'w')
        #Start with Header
        self.createHeader(file)

        #Create the bounding box 
        self.createEnv(file)

        self.createPos()

        #Creates the number of Rovables in a randomized position
        self.createRobots(file)

        print("World Written with Seed: " + str(self.instance_id))

        file.close()

        self.createArena()