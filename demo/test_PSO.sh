#This shell script tests changes in PSO implementation
GEN_ID=0
PARTICLE_ID=1
INSTANCE_ID=2

WB_TIMEOUT=45

# DEPENDS ON YOUR WORKING MACHINE
cd /home/darren/Documents/DARS/NoiseResistance/Rovables_Bayesian_Inspection_Optimization/demo/jobfiles

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

python3 -u ../python_code/simSetupPSO.py -s $INSTANCE_ID -p $JOB_BASE_DIR 

WEBWORLD="../worlds/bayes_pso_${INSTANCE_ID}.wbt"

echo "WEBOTS DIR: ${WEBWORLD}"

cp ${INPUT_DIR}/prob_${PARTICLE_ID}.txt $WB_WORKING_DIR/prob.txt

export WB_WORKING_DIR=$JOB_BASE_DIR
export NOISE_SEED=$INSTANCE_ID

timeout $WB_TIMEOUT xvfb-run webots --batch --mode=fast --stdout --stderr --no-rendering $WEBWORLD
