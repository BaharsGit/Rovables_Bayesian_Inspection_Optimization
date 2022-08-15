#This shell script tests changes in PSO implementation
GEN_ID=0
INSTANCE_ID=3
NUM_ROBOTS=4
PARTICLE_ID=2

line=$((INSTANCE_ID + 1))
FILL_RATIO=$(sed -n ${line}p /home/darren/Documents/ICRA_LAUNCH/Rovables_Bayesian_Inspection_Optimization/demo/fill_array.txt)
# FILL_RATIO=$(sed -n ${INSTANCE_ID}p $(pwd)../fill_array.txt)
echo "Using Fill Ratio " ${FILL_RATIO}

WB_TIMEOUT=30

# DEPENDS ON YOUR WORKING MACHINE
cd /home/darren/Documents/ICRA_LAUNCH/Rovables_Bayesian_Inspection_Optimization/demo/jobfiles
# RUN_DIR=$(ls -td */| head -1)
# cd $RUN_DIR

pwd
echo "Running PSO script"

#python3 -u PSO_tocluster.py -n $NB_PARTICLES -e $NB_NOISE_RES_EVALS

# job_lily_parallel.sh
INPUT_DIR=Generation_${GEN_ID}
echo "job_lily_parallel.sh input directory is " ${INPUT_DIR}

JOB_BASE_DIR=$(pwd)/tmp/job${GEN_ID}_${PARTICLE_ID}_${INSTANCE_ID}

echo "JOB BASE DIR: ${JOB_BASE_DIR}"

if [ ! -d $JOB_BASE_DIR ]

then

   echo "(`date`) Create job base directory for the Webots instance of this job_lily_parallel.sh script as $JOB_BASE_DIR"
   mkdir -p $JOB_BASE_DIR

fi


echo "Generating world and arena files..."

python3 -u ../python_code/simSetupPSO.py -pid $PARTICLE_ID -iid $INSTANCE_ID -fr $FILL_RATIO -p $JOB_BASE_DIR -r $NUM_ROBOTS

WEBWORLD= "../worlds/bayes_pso_${PARTICLE_ID}_${INSTANCE_ID}.wbt"

echo "WEBOTS DIR: ${WEBWORLD}"

export WB_WORKING_DIR=$JOB_BASE_DIR
export NOISE_SEED=$INSTANCE_ID
export FILL_RATIO=$FILL_RATIO

sudo cp ${INPUT_DIR}/prob_${PARTICLE_ID}.txt $WB_WORKING_DIR/prob.txt

time timeout $WB_TIMEOUT xvfb-run webots --batch --mode=fast --stdout --stderr --no-rendering $WEBWORLD

# rm -r $JOB_BASE_DIR
# rm ../worlds/bayes_pso_${PARTICLE_ID}_${INSTANCE_ID}.wbt