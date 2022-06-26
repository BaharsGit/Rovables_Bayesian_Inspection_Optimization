#!/bin/sh

# MODIFIED FOR NOISE RESISTANT PSO
NB_NOISE_RES_EVALS=0

# Get the current AWS job indexes
MY_ID=$((AWS_BATCH_JOB_NODE_INDEX))
MAIN_ID=$((AWS_BATCH_JOB_MAIN_NODE_INDEX))

echo "This node index =" $MY_ID
echo "Main node index =" $MAIN_ID

# Get the number of nodes/particles from started AWS job
NB_NODES=$((AWS_BATCH_JOB_NUM_NODES))
NB_PARTICLES=$(($NB_NODES-1))

echo "Number of particles =" $NB_PARTICLES

cd /usr/local/efs/demo/jobfiles
#cd /usr/local/efs/pso_self-assembly_aws/jobfiles

if [ $MY_ID -eq $MAIN_ID ]; then
  # Run PSO Python script on main node
  echo "Running PSO script"
  # MODIFIED FOR NOISE RESISTANT PSO
  python3 -u PSO_tocluster.py -n $NB_PARTICLES $NB_NOISE_RES_EVALS

else
  # Run particle evaluation on other nodes
  echo "Waiting for next particle evaluation"
  GEN_ID=0
  INDIVID_ID=$(($MY_ID-1))

  RUN_DIR=$(ls -td */| head -1)
  cd $RUN_DIR
  
  while true 
  do
    if [ -f "Generation_${GEN_ID}/prob_${INDIVID_ID}.txt" ]; then
      # Start one local Webots instance
      echo "Starting a Webots instance for particle evaluation"
      # MODIFIED FOR NOISE RESISTANT PSO
      INSTANCE_ID=$((NB_NOISE_RES_EVALS))
      while [ INSTANCE_ID -ge 0 ]
      do 
        INSTANCE_ID=$(($INSTANCE_ID -1))
        bash ../job_lily_parallel.sh $GEN_ID $INDIVID_ID $INSTANCE_ID
      done
      ((GEN_ID++))
    fi
  done
fi