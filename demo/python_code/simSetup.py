import argparse
import subprocess
import time
import os
import shutil
from datetime import datetime
from createWorld import WorldGenerator

from subprocess import Popen, PIPE

from numpy import save

# Arguments
parser = argparse.ArgumentParser(description="Setup and run Bayesian Inspection Simulation")

parser.add_argument("-s", "--seed", required=False, type=int, default="0")

args = parser.parse_args()

# Setup the directories for the simulation
folder = "../Log/" + "Run" + str(args.seed) + "/"
tempDir = "../controllers/bayes_supervisor/Data/Temp" + str(args.seed) + "/"
if not os.path.exists(folder):
    os.makedirs(folder)
if not os.path.exists(tempDir):
    os.makedirs(tempDir)

# #Create World file with randomized positions and walks based on robot seed
# # world_seed not used in this case as the texture is fixed. 
WG = WorldGenerator(world_seed=16, robot_seed=args.seed, robot_number=4)
WG.createWorld()

# #Run the Webots simulation
dir = "../worlds/bayesian_rovables_sim" + "_" + str(args.seed) + ".wbt"
subprocess.call(["webots --mode=fast --minimize --no-rendering --stdout --batch", dir], shell=True)
# #time.sleep(30)

# # MODIFIED FOR AWS LAUNCH, LINES 32-42
proc=subprocess.Popen(["xvfb-run","webots","--mode=realtime","--no-rendering","--batch","--stdout","--stderr", dir])

# Get stdout and stderr messages during simulation
try:
    outs, errs = proc.communicate()
except subprocess.TimeoutExpired:
    proc.kill()
    outs, errs = proc.communicate()

# time.sleep(5)

saveDest = "../controllers/bayes_supervisor/Data/Temp"
for file in os.listdir(tempDir):
    if file.endswith(".txt"):
        print("Decision time file found")
        shutil.move(tempDir + file, folder + file)
    if file.endswith(".csv"):
        print("FILE FOUND")
        shutil.move(tempDir + file, folder + file)
    else: 
        print("NO FILE FOUND")

os.rmdir(tempDir)
