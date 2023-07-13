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

parser.add_argument("-s", "--seed", required=True, type=int, default="0")
parser.add_argument("-fr", "--fill_ratio", required=True, type=float, default="0.52")
parser.add_argument("-p", "--path", required=True)
parser.add_argument("-r", "--num_robots", required=True, type=int, default="4")
parser.add_argument("-d", "--dynamic_env", required=True, type=int, default="1")
parser.add_argument("-dub", "--env_upper", required=True, type=float, default="0.55")
parser.add_argument("-dlb", "--env_lower", required=True, type=float, default="0.45")

args = parser.parse_args()

# Setup the directories for the simulation
folder = "../Log/" + "Run" + str(args.seed) + "/"
tempDir = "../controllers/bayes_supervisor/Data/Temp" + str(args.seed) + "/"
tempDirObs = "../controllers/bayes_fsm/Data/Temp" + str(args.seed) + "/"
if not os.path.exists(folder):
    os.makedirs(folder)

if not os.path.exists(tempDir):
    os.makedirs(tempDir)

if not os.path.exists(tempDirObs):
    os.makedirs(tempDirObs)

# #Create World file with randomized positions and walks based on robot seed
# # world_seed not used in this case as the texture is fixed. 
WG = WorldGenerator(baseline=1, particle_id=args.seed, instance_id=args.seed, fill_ratio=args.fill_ratio, robot_number=args.num_robots, path=args.path, dynamic_env=args.dynamic_env, env_upper=args.env_upper, env_lower=args.env_lower)
WG.createWorld()

# #Run the Webots simulation
dir = "../worlds/bayes_pso" + "_" + str(args.seed) + "_" + str(args.seed) + ".wbt"
# subprocess.call(["webots --mode=fast --minimize --no-rendering --stdout --batch", dir], shell=True)
# #time.sleep(30)

# # MODIFIED FOR AWS LAUNCH, LINES 32-42
proc=subprocess.Popen(["xvfb-run", "-a", "webots","--mode=fast","--no-rendering","--batch","--stdout","--stderr", dir])

# Get stdout and stderr messages during simulation
try:
    outs, errs = proc.communicate()
except subprocess.TimeoutExpired:
    proc.kill()
    outs, errs = proc.communicate()

# time.sleep(5)

for file in os.listdir(tempDir):
    if file.endswith(".txt"):
        print("File Found: ", file)
        shutil.move(tempDir + file, folder + file)
    elif file.endswith(".csv"):
        print("File Found: ", file)
        shutil.move(tempDir + file, folder + file)
    else:
        print(file)
        print("NO FILE FOUND")
for file in os.listdir(args.path):
    if file.endswith(".txt"):
        print("Found file: ", file)
        shutil.move(str(args.path) + "/" + file, folder + file)
for file in os.listdir(tempDirObs):
    if file.endswith(".txt"):
        print("Found file: ", file)
        shutil.move(tempDirObs + file, folder + file)

os.rmdir(tempDir)
