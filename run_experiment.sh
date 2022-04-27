#!/bin/sh

# Get the current AWS job indexes
MY_ID=$((AWS_BATCH_JOB_NODE_INDEX))
MAIN_ID=$((AWS_BATCH_JOB_MAIN_NODE_INDEX))

echo "This node index =" $MY_ID
echo "Main node index =" $MAIN_ID

# Get the number of nodes/particles from started AWS job
NB_NODES=$((AWS_BATCH_JOB_NUM_NODES))
NB_PARTICLES=$(($NB_NODES-1))

echo "Number of particles =" $NB_PARTICLES

cd /usr/local/efs/pso_self-assembly_aws/jobfiles

if [ $MY_ID -eq $MAIN_ID ]; then
  # Run PSO Python script on main node
  echo "Running PSO script"
  python3 -u PSO_tocluster.py -n $NB_PARTICLES

else
  # Run particle evaluation on other nodes
  echo "Waiting for next particle evaluation"
  GEN_ID=0
  INDIVID_ID=$(($MY_ID-1))

  while true 
  do
    if [ -f "Generation_${GEN_ID}/prob_${INDIVID_ID}.txt" ]; then
      # Start one local Webots instance
      echo "Starting a Webots instance for particle evaluation"
      bash job_lily_parallel.sh $GEN_ID $INDIVID_ID
      ((GEN_ID++))
    fi
  done
fi