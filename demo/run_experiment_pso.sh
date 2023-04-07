#!/bin/sh
#USE LINE 3 FOR RUNNING ON AWS
home_path="$(pwd)/efs/demo"

#USE LINE 6 FOR RUNNING ON LOCAL COMPUTER
#home_path="$(pwd)"

# MODIFIED FOR NOISE RESISTANT PSO
NB_NOISE_RES_EVALS=10
NUM_ROBOTS=4

#Set below variables if resuming a previous run
RESUME=0
RESUME_NB_RUN=0 #Which run number to resume from
RESUME_NB_ITER=8 #Which COMPLETE iteration to resume from

#FLIP TO TEST PSO IN SERIES ON LOCAL OR USE TEST FUNCTION
TEST_PSO=0
TEST_FUNC=0

#RUN DYNAMIC ENVIORNMENT
DYNAMIC_ENV=0
ENV_LB=0.45
ENV_UB=0.55



# Get the current AWS job indexes
MY_ID=$((AWS_BATCH_JOB_NODE_INDEX))
MAIN_ID=$((AWS_BATCH_JOB_MAIN_NODE_INDEX))

echo "This node index =" $MY_ID
echo "Main node index =" $MAIN_ID

# Get the number of nodes/particles from started AWS job
NB_NODES=$((AWS_BATCH_JOB_NUM_NODES))
# MODIFIED FOR NOISE RESISTANT PSO
NB_PARTICLES=$((($NB_NODES-1)/$NB_NOISE_RES_EVALS))

# MODIFIED FOR NOISE RESISTANT PSO
echo "Number of particles =" $NB_PARTICLES
echo "Number of noise resistant evaluations =" $NB_NOISE_RES_EVALS
echo "Number of nodes running Webots instances =" $NB_NODES


#cd /usr/local/efs/demo/jobfiles
cd ${home_path}/jobfiles

# RUN IN SERIES
if [ $TEST_PSO -eq 1 ]
then 
  echo "Running PSO Test"
  cd $(pwd)/../controllers/bayes_fsm
  pwd
  #cd /root/Rovables/Rovables_Bayesian_Inspection_Optimization/demo/controllers/bayes_fsm
  export WEBOTS_HOME=/usr/local/webots
  make clean
  make

  cd $(pwd)/../../jobfiles
  # DEFINE FOR THE TEST RUN
  NUM_ROBOTS=4
  NB_NOISE_RES_EVALS=2
  NB_PARTICLES=5
  echo "Number of particles =" $NB_PARTICLES
  echo "Number of noise resistant evaluations =" $NB_NOISE_RES_EVALS
  echo "Number of nodes running Webots instances =" $NB_NODES
  pwd
  # MODIFIED FOR NOISE RESISTANT PSO
  python3 -u PSO_tocluster.py -r $RESUME -r_run $RESUME_NB_RUN -r_iter $RESUME_NB_ITER -n $NB_PARTICLES -e $NB_NOISE_RES_EVALS -t $TEST_PSO -tf $TEST_FUNC -d $DYNAMIC_ENV -dub $ENV_UB -dlb $ENV_LB
  
# RUN PARALLEL
else 
  if [ $MY_ID -eq $MAIN_ID ]; then
    # Run PSO Python script on main node
    echo "Running PSO script"
    
    # MODIFIED FOR COMPILATION ON AWS INSTANCES TO AVOID NON-COMPATIBLE BINARY WARNING
    cd ${home_path}/controllers/bayes_fsm
    export WEBOTS_HOME=/usr/local/webots
    make clean
    make

    cd ${home_path}/jobfiles

    # MODIFIED FOR NOISE RESISTANT PSO
    python3 -u PSO_tocluster.py -r $RESUME -r_run $RESUME_NB_RUN -r_iter $RESUME_NB_ITER -n $NB_PARTICLES -e $NB_NOISE_RES_EVALS -t $TEST_PSO -tf $TEST_FUNC -d $DYNAMIC_ENV -dub $ENV_UB -dlb $ENV_LB

  else
    # Run particle evaluation on other nodes
    echo "Waiting for next particle evaluation"
    GEN_ID=0
    # Run PSO Python script on main node
    # MODIFIED FOR NOISE RESISTANT PSO
    PARTICLE_ID=$((($MY_ID-1)%$NB_PARTICLES))

    # Pipe ls command into head and print first line
    RUN_DIR=$(ls -td */| head -1)
    echo "Change directory: " $RUN_DIR
    cd $RUN_DIR
    
    while true 
    do
      if [ -f "Generation_${GEN_ID}/prob_${PARTICLE_ID}.txt" ]; then
        # Start one local Webots instance
        # MODIFIED FOR NOISE RESISTANT PSO
        if [ $NB_NOISE_RES_EVALS -gt 0 ]
        then
          INSTANCE_ID=$(((($MY_ID-1)-$PARTICLE_ID)/$NB_PARTICLES))
          echo "Starting a Webots instance for evaluation of instance $INSTANCE_ID of particle $PARTICLE_ID"  
          bash ../job_parallel.sh $GEN_ID $PARTICLE_ID $INSTANCE_ID $NUM_ROBOTS 0 $DYNAMIC_ENV $ENV_UB $ENV_LB
        else
          INSTANCE_ID=-1
          echo "Starting a Webots instance for evaluation of particle" $PARTICLE_ID
          bash ../job_parallel.sh $GEN_ID $PARTICLE_ID $INSTANCE_ID $NUM_ROBOTS 0 $DYNAMIC_ENV $ENV_UB $ENV_LB
        fi
        ((GEN_ID++))
      fi
    done
  fi
fi