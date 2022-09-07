#!/bin/bash

#What this script will do: 
#   1.) Run a Bayesian insepction algorithm simulation on WeBots.
#   2.) Constant world and algorithm parameters. 
#   3.) Runs simSetup.py which will:
#       a.) Create the log folder based on the current seed'
#       b.) Run the simulation. Producing -> runPos.csv and runProb.csv
#       c.) Move the output files into the previously created log folder.

# Ensure the path is exactly the same as model code. Within the Webots and external scripts. 

# MODIFIED FOR AWS LAUNCH, LINES 16-20, DEFINE PY_PATH
py_path="/usr/local/efs/demo/python_code"

# Move to path
cd $py_path

# Fix Parameters and world -> variations in algorithm runs
echo Starting script. . . ${BASH_VERSION}
# Get the current AWS job index
line=$((AWS_BATCH_JOB_ARRAY_INDEX + 1))
seed=$(sed -n ${line}p /usr/local/efs/demo/seed_array.txt)
fill=$(sed -n ${line}p /usr/local/efs/demo/fill_array.txt)

JOB_BASE_DIR=$(pwd)/tmp/job_${line}
if [ ! -d $JOB_BASE_DIR ]

then

   echo "(`date`) Create job base directory for the Webots instance of this job_lily_parallel.sh script as $JOB_BASE_DIR"
   mkdir -p $JOB_BASE_DIR

fi

export WB_WORKING_DIR=$JOB_BASE_DIR
export FILL_RATIO=$fill

#python3 -u imCreateRect.py -fr $fill -ss $square_size  -sd $mapSeed -rs $seed 

#No longer using as seed data is "pipelined" into map generation script
#echo $seed > /usr/local/efs/demo/controllers/bayes_bot_controller/seed.txt
#echo $seed > /usr/local/efs/demo/controllers/bayes_supervisor/seed.txt

# Run experiment according to the seed and simulation parameters
echo "Running experiment version $seed"
# MODIFIED FOR AWS LAUNCH, LINES 48, USING PY_PATH
python3 -u simSetupParallel.py -s $seed -f $fill #Setup directories and run the simulation