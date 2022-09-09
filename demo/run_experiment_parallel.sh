#!/bin/bash

#What this script will do: 
#   1.) Run a Bayesian insepction algorithm simulation on WeBots.
#   2.) Constant world and algorithm parameters. 
#   3.) Runs simSetup.py which will:
#       a.) Create the log folder based on the current seed'
#       b.) Run the simulation. Producing -> runPos.csv and runProb.csv
#       c.) Move the output files into the previously created log folder.

echo Starting script. . . ${BASH_VERSION}

# MODIFIED FOR AWS LAUNCH, LINES 16-20, DEFINE PY_PATH
py_path="/usr/local/efs/demo/python_code"
# UNCOMMENT BELOW TO TEST ON LOCAL MACHINE
#py_path="/home/darren/Documents/ICRA_LAUNCH/Rovables_Bayesian_Inspection_Optimization/demo/python_code"

# Move to path
cd $py_path

echo Compiling Code. . .

cd /usr/local/efs/demo/controllers/bayes_fsm
export WEBOTS_HOME=/usr/local/webots
make clean
make
cd
cd /usr/local/efs/demo/jobfiles

# Get the current AWS job index
line=$((AWS_BATCH_JOB_ARRAY_INDEX + 1))
SEED=$(sed -n ${line}p /usr/local/efs/demo/seed_array.txt)
FILL_RATIO=$(sed -n ${line}p /usr/local/efs/demo/fill_array.txt)
NUM_ROBOTS=4

JOB_BASE_DIR=$(pwd)/tmp/job_${line}
if [ ! -d $JOB_BASE_DIR ]

then

   echo "(`date`) Create job base directory for the Webots instance of this job_lily_parallel.sh script as $JOB_BASE_DIR"
   mkdir -p $JOB_BASE_DIR

fi

export WB_WORKING_DIR=$JOB_BASE_DIR
export FILL_RATIO=$FILL_RATIO

# Run experiment according to the seed and simulation parameters
echo "Running experiment version $SEED"
# MODIFIED FOR AWS LAUNCH, LINES 48, USING PY_PATH
pwd
echo "Using Parameters File: "
cat ../baseline_param.txt
cp ../baseline_param.txt ${JOB_BASE_DIR}/prob.txt

python3 -u simSetupParallel.py -s $SEED -fr $FILL_RATIO -p $JOB_BASE_DIR -r $NUM_ROBOTS #Setup directories and run the simulation