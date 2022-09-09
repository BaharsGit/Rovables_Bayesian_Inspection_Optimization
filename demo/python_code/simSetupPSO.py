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

parser.add_argument("-pid", "--particle_id", required=True, type=int, default="0")
parser.add_argument("-iid", "--instance_id", required=True, type=int, default="0")
parser.add_argument("-fr", "--fill_ratio", required=True, type=float, default="0.52")
parser.add_argument("-p", "--path", required=True)
parser.add_argument("-r", "--num_robots", required=True, type=int, default="4")


args = parser.parse_args()

# #Create World file with randomized positions and walks based on robot seed
# World seed defines the randomization for the world generation: Robot Positions
# Robot seed defines the seed used in controller for random walks
# Path defines where the files are saved.
WG = WorldGenerator(particle_id=args.particle_id, instance_id=args.instance_id, fill_ratio=args.fill_ratio, robot_number=args.num_robots, path=args.path)

WG.createWorld()

