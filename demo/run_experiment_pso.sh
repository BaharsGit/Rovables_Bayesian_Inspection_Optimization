#!/bin/sh

# MODIFIED FOR NOISE RESISTANT PSO
NB_NOISE_RES_EVALS=3
NUM_ROBOTS=4

#FLIP TO TEST PSO IN SERIES ON LOCAL
TEST_PSO=1

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

cd /usr/local/efs/demo/jobfiles
#cd /usr/local/efs/pso_self-assembly_aws/jobfiles

# RUN IN SERIES
if [ $TEST_PSO -eq 1 ]
then 
  echo "Running PSO Test"
  cd /home/darren/Documents/ICRA_LAUNCH/Rovables_Bayesian_Inspection_Optimization/demo/controllers/bayes_fsm
  export WEBOTS_HOME=/usr/local/webots
  make clean
  make
  GEN_ID=0
  INSTANCE_ID=3
  NUM_ROBOTS=4
  PARTICLE_ID=2
  NB_NOISE_RES_EVALS=3
  NB_PARTICLES=5
  echo "Number of particles =" $NB_PARTICLES
  echo "Number of noise resistant evaluations =" $NB_NOISE_RES_EVALS
  echo "Number of nodes running Webots instances =" $NB_NODES
  cd /home/darren/Documents/ICRA_LAUNCH/Rovables_Bayesian_Inspection_Optimization/demo/jobfiles
  pwd
  # MODIFIED FOR NOISE RESISTANT PSO
  python3 -u PSO_tocluster.py -n $NB_PARTICLES -e $NB_NOISE_RES_EVALS -t $TEST_PSO
# RUN PARALLEL
else 
  if [ $MY_ID -eq $MAIN_ID ]; then
    # Run PSO Python script on main node
    echo "Running PSO script"
    
    # MODIFIED FOR COMPILATION ON AWS INSTANCES TO AVOID NON-COMPATIBLE BINARY WARNING
    cd /usr/local/efs/demo/controllers/bayes_fsm
    export WEBOTS_HOME=/usr/local/webots
    make clean
    make
    cd
    cd /usr/local/efs/demo/jobfiles

    # MODIFIED FOR NOISE RESISTANT PSO
    python3 -u PSO_tocluster.py -n $NB_PARTICLES -e $NB_NOISE_RES_EVALS

  else
    # Run particle evaluation on other nodes
    echo "Waiting for next particle evaluation"
    GEN_ID=0
    # Run PSO Python script on main node
    # MODIFIED FOR NOISE RESISTANT PSO
    PARTICLE_ID=$((($MY_ID-1)%$NB_PARTICLES))

    # Pipe ls command into head and print first line
    RUN_DIR=$(ls -td */| head -1)
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
          bash ../job_lily_parallel.sh $GEN_ID $PARTICLE_ID $INSTANCE_ID $NUM_ROBOTS
        else
          INSTANCE_ID=-1
          echo "Starting a Webots instance for evaluation of particle" $PARTICLE_ID
          bash ../job_lily_parallel.sh $GEN_ID $PARTICLE_ID $INSTANCE_ID $NUM_ROBOTS
        fi
        ((GEN_ID++))
      fi
    done
  fi
fi