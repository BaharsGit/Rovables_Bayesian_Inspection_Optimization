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

parser.add_argument("-s", "--instance_id", required=True, type=int, default="0")
parser.add_argument("-p", "--path", required=True)

args = parser.parse_args()

# #Create World file with randomized positions and walks based on robot seed
# World seed defines the randomization for the world generation: Robot Positions
# Robot seed defines the seed used in controller for random walks
# Path defines where the files are saved.
WG = WorldGenerator(world_seed=args.instance_id, robot_seed=args.instance_id, robot_number=4, path=args.path)

WG.createWorld()

