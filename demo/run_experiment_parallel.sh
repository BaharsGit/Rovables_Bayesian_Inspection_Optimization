#!/bin/bash

#What this script will do: 
#   1.) Run a Bayesian insepction algorithm simulation on WeBots.
#   2.) Constant world and algorithm parameters. 
#   3.) Runs simSetup.py which will:
#       a.) Create the log folder based on the current seed'
#       b.) Run the simulation. Producing -> runPos.csv and runProb.csv
#       c.) Move the output files into the previously created log folder.
echo Starting script. . . ${BASH_VERSION}
home_path="$(pwd)/efs/demo"
# home_path="$(pwd)"
cd $home_path # Used for correct path in batch launch on AWS. Disable if using on local test.

# MODIFIED FOR AWS LAUNCH, LINES 16-20, DEFINE PY_PATH
py_path="${home_path}/python_code"

# UNCOMMENT BELOW TO TEST ON LOCAL MACHINE
#py_path="/home/darren/Documents/ICRA_LAUNCH/Rovables_Bayesian_Inspection_Optimization/demo/python_code"

echo Compiling Code. . .
cd ${home_path}/controllers/bayes_fsm
export WEBOTS_HOME=/usr/local/webots
make clean
make


# Move to home path
cd $home_path

# Get the current AWS job index
line=$((AWS_BATCH_JOB_ARRAY_INDEX + 1))
# line=${i} Used this in a for loop for local test.
SEED=$(sed -n ${line}p ${home_path}/seed_array.txt)
FILL_RATIO=$(sed -n ${line}p ${home_path}/fill_array.txt)
NUM_ROBOTS=4

JOB_BASE_DIR=${home_path}/tmp/job_${line}
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
cat ${home_path}/baseline_param.txt
cp ${home_path}/baseline_param.txt ${JOB_BASE_DIR}/prob.txt

cd ${home_path}/python_code
python3 -u simSetupParallel.py -s $SEED -fr $FILL_RATIO -p $JOB_BASE_DIR -r $NUM_ROBOTS #Setup directories and run the simulation
cd ${home_path}