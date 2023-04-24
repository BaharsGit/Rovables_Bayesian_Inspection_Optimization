#!/bin/bash

#
# File: job_lily_parallel.sh shell script       
# Date: 17 March 2017     
# Description: This shell script was based on cluster job file job_lily_parallel.sub, 
#              it runs on AWS (particle) nodes, it launches Webots to evaluate the corresponding particle
# Author: Bahar Haghighat 
# Modifications: by Bahar Haghighat, 13 June 2022, cleaned up non-AWS stuff left from local cluster launch
#
 
# The first input variable to the shell script is the GEN_ID, the second one is the PARTICLE_ID
GEN_ID=$1 
PARTICLE_ID=$2
# MODIFIED FOR NOISE RESISTANT PSO
INSTANCE_ID=$3
NUM_ROBOTS=$4
TEST_FUNC_VALUE=$5
DYNAMIC_ENV=$6
ENV_UB=$7
ENV_LB=$8
RUN_TEST_FUNC=$9

line=$((INSTANCE_ID + 1))


#FILL_RATIO=$(sed -n ${line}p /usr/local/efs/demo/fill_array.txt)
FILL_RATIO=$(sed -n ${line}p $(pwd)/../../fill_array.txt)
echo "Using Fill Ratio " ${FILL_RATIO}


# Setting the worst case fitness value, in case the launch doesn't go well, the worst case fitness value is considered as default
# Should be set to worst fitness attainable by the robots within the simulation time allowed by the supervisor 
WORST_FITNESS=100000 

# Kill webots after WB_TIMEOUT seconds
WB_TIMEOUT=900

 
# N_RUNS can be used for noise resistant evaluation of a particle
# N_RUNS is number of evaluations of this particle by this shell script
N_RUNS=1 


# Set the input directory (relative to the current working directory)
INPUT_DIR=Generation_${GEN_ID}
echo "job_lily_parallel.sh input directory is " ${INPUT_DIR}


# Set the output directory to put results (relative to the current working directory)
OUTPUT_DIR=Generation_${GEN_ID}
echo "job_lily_parallel.sh output directory is " ${OUTPUT_DIR}


# Set the job base directory, the Webots working directory
# pwd is acronym for print working directory (pwd), returns current directory

# MODIFIED FOR NOISE RESISTANT PSO
if [ $INSTANCE_ID -ge 0 ]
then
   JOB_BASE_DIR=$(pwd)/tmp/job${GEN_ID}_${PARTICLE_ID}_${INSTANCE_ID}

else 
   JOB_BASE_DIR=$(pwd)/tmp/job${GEN_ID}_${PARTICLE_ID}

fi
 
# Create the working directory for Webots, where Webots can write its stuff
if [ ! -d $JOB_BASE_DIR ]

then

   echo "(`date`) Create job base directory for the Webots instance of this job_lily_parallel.sh script as $JOB_BASE_DIR"
   mkdir -p $JOB_BASE_DIR

fi

# Set Webots working directory, where Webots can write its stuff
export WB_WORKING_DIR=$JOB_BASE_DIR
export NOISE_SEED=$INSTANCE_ID
export FILL_RATIO=$FILL_RATIO


# if [ $RUN_TEST_FUNC -eq "1" ] 
# then
echo "Generating world and arena files..."
python3 -u $(pwd)/../../python_code/simSetupPSO.py -pid $PARTICLE_ID -iid $INSTANCE_ID -fr $FILL_RATIO -p $JOB_BASE_DIR -r $NUM_ROBOTS -d $DYNAMIC_ENV -dub $ENV_UB -dlb $ENV_LB 
# fi
echo "(`date`) Performing a total of $N_RUNS runs for particle $PARTICLE_ID"

# PATH : This line defines the path to the Webots world to be launched, each instance will open a unique world file. 
WEBWORLD="$(pwd)/../../worlds/bayes_pso_${PARTICLE_ID}_${INSTANCE_ID}.wbt"  
 
# if Webots crashes after its launch, or fails to create local_fitness.txt, the script will do a number of follow-up trials
TRIAL_COUNT=1

for (( RUN_ID=1; RUN_ID<=$N_RUNS; RUN_ID++ )) 

   do

      # copy the input parameters from the Generation_${GEN_ID} directory to Webots working directory 
      cp ${INPUT_DIR}/prob_${PARTICLE_ID}.txt $WB_WORKING_DIR/prob.txt 
      
      # echo "(`date`) Launching Webots (run $RUN_ID) of particle $PARTICLE_ID"
      
      # launch webots
      # logs are redirected to webots_log.txt file
      echo $RUN_TEST_FUNC
      if [ $RUN_TEST_FUNC = "1" ] 
      then
         echo "Running Test Function"
         echo $TEST_FUNC_VALUE
         echo $TEST_FUNC_VALUE > $JOB_BASE_DIR/local_fitness.txt
         
      else
         echo "Running file $WEBWORLD"
         #time timeout $WB_TIMEOUT xvfb-run webots --batch --mode=fast --stdout --stderr --no-rendering $WEBWORLD &> $WB_WORKING_DIR/webots_log.txt 
         time timeout $WB_TIMEOUT xvfb-run -a webots --batch --mode=fast --stdout --stderr --no-rendering $WEBWORLD &> $WB_WORKING_DIR/webots_log.txt 
      fi

      # waiting just a while before copying the output
      sleep 1


      # checking whether run was successful
      # the local_fitness.txt is written by the supervisor in Webots
      if [ -e $WB_WORKING_DIR/local_fitness.txt ] 
      then

         echo "(`date`) Run successfully completed, local_fitness.txt was created under $WB_WORKING_DIR/ \n"
         # echo "(`date`) Run $RUN_ID successfully completed"
         #rm $WB_WORKING_DIR/ack.txt

      else

         echo "(`date`) Run failed, local_fitness.txt was not created under $WB_WORKING_DIR/\n"
         # echo "(`date`) Run $RUN_ID failed, cleaning up, and running again"
         ((TRIAL_COUNT--))
         # ToDo: perform cleanup of unwanted files

         if [ $TRIAL_COUNT -gt 0 ]
         then

         	# performing the run again
         	((RUN_ID--))
            # launch webots
            # logs are redirected to webots_log.txt file
            # timeout $WB_TIMEOUT xvfb-run webots --batch --mode=fast --stdout --stderr --no-rendering $WEBWORLD &> $WB_WORKING_DIR/webots_log.txt

         else 

           echo "(`date`) RUN got stuck, auxilary fitness file created with worst fitness $WORST_FITNESS"
   	     echo ${WORST_FITNESS} >> $WB_WORKING_DIR/local_fitness.txt
   	     #rm $WB_WORKING_DIR$/ack.txt

         fi

      fi
    
      sleep 1

   done


# Create a desired final output directory
# OUTPUT_DIR=Generation_${GEN_ID}
# if [ ! -d $OUTPUT_DIR ]
# then
# 	echo "(`date`) Create output directory $OUTPUT_DIR"
# 	mkdir $OUTPUT_DIR
# fi


# Move results to the final output directory

# MODIFIED FOR NOISE RESISTANT PSO
if [ $INSTANCE_ID -ge 0 ]
then
   mv $WB_WORKING_DIR/local_fitness.txt ${OUTPUT_DIR}/local_fitness_${PARTICLE_ID}_${INSTANCE_ID}.txt
   mv $WB_WORKING_DIR/webots_log.txt ${OUTPUT_DIR}/webots_log_${PARTICLE_ID}_${INSTANCE_ID}.txt
   mv $WB_WORKING_DIR/fill_log.txt ${OUTPUT_DIR}/arena_log_${PARTICLE_ID}_${INSTANCE_ID}.txt
   # mv $WB_WORKING_DIR/arena*.txt ${OUTPUT_DIR}/arena_log_${PARTICLE_ID}_${INSTANCE_ID}.txt
else 
   mv $WB_WORKING_DIR/local_fitness.txt ${OUTPUT_DIR}/local_fitness_${PARTICLE_ID}.txt

fi


# Remove job base directory, the Webots working directory
rm -r $JOB_BASE_DIR
#rm $WEBWORLD

# MODIFIED FOR NOISE RESISTANT PSO
if [ $INSTANCE_ID -ge 0 ]
then
   echo "(`date`) Job ${GEN_ID}_${PARTICLE_ID} completed by instance $INSTANCE_ID of particle $PARTICLE_ID"

else 
   echo "(`date`) Job ${GEN_ID}_${PARTICLE_ID} completed by particle $PARTICLE_ID"

fi
