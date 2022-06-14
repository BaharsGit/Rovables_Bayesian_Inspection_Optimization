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


# Setting the worst case fitness value, in case the launch doesn't go well, the worst case fitness value is considered as default
WORST_FITNESS=43200


# Kill webots after WB_TIMEOUT seconds
WB_TIMEOUT=7200  

 
# N_RUNS can be used for noise resistant evaluation of a particle
# N_RUNS is number of evaluations of this particle by this shell script
N_RUNS=1 


# PATH : This line defines the path to the Webots world to be launched, should be modified for a different world name
#WEBWORLD="../../worlds/24Lilies_LaLn.wbt"
WEBWORLD="../../worlds/bayes_pso.wbt"


# Set the input directory (relative to the current working directory)
INPUT_DIR=Generation_${GEN_ID}
echo "job_lily_parallel.sh input directory is " ${INPUT_DIR}


# Set the output directory to put results (relative to the current working directory)
OUTPUT_DIR=Generation_${GEN_ID}
echo "job_lily_parallel.sh output directory is " ${OUTPUT_DIR}


# Set the job base directory, the Webots working directory
# pwd is acronym for print working directory (pwd), returns current directory
JOB_BASE_DIR=$(pwd)/tmp/job${GEN_ID}_${PARTICLE_ID}
 

# Create the working directory for Webots, where Webots can write its stuff
if [ ! -d $JOB_BASE_DIR ]

then

   echo "(`date`) Create job base directory for the Webots instance of this job_lily_parallel.sh script as $JOB_BASE_DIR"
   mkdir -p $JOB_BASE_DIR

fi

# Set Webots working directory, where Webots can write its stuff
export WB_WORKING_DIR=$JOB_BASE_DIR


echo "(`date`) Performing a total of $N_RUNS runs for particle $PARTICLE_ID"
 
# if Webots crashes after its launch, or fails to create local_fitness.txt, the script will do a number of follow-up trials
TRIAL_COUNT=1

for (( RUN_ID=1; RUN_ID<=$N_RUNS; RUN_ID++ )) 

   do

      # copy the input parameters from the Generation_${GEN_ID} directory to Webots working directory 
      cp ${INPUT_DIR}/prob_${PARTICLE_ID}.txt $WB_WORKING_DIR/prob.txt 
      
      echo "(`date`) Launching Webots (run $RUN_ID) of particle $PARTICLE_ID"
      
      # launch webots
      # logs are redirected to webots_log.txt file
      # timeout $WB_TIMEOUT xvfb-run webots --batch --mode=fast --stdout --stderr --no-rendering $WEBWORLD &> $WB_WORKING_DIR/webots_log.txt 
      timeout $WB_TIMEOUT xvfb-run webots --batch --mode=fast --stdout --stderr --no-rendering $WEBWORLD
    

      # waiting just a while before copying the output
      sleep 1


      # checking whether run was successful
      # the local_fitness.txt is written by the supervisor in Webots
      if [ -e $WB_WORKING_DIR/local_fitness.txt ] 
      then

         echo "(`date`) Run $RUN_ID successfully completed"
         #rm $WB_WORKING_DIR/ack.txt

      else

         echo "(`date`) Run $RUN_ID failed, cleaning up, and running again"
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

           echo "(`date`) RUN got stuck, auxilary fitness file created"
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

#mv $WB_WORKING_DIR/global_best_fitness.txt $OUTPUT_DIR/global_best_fitness_${PARTICLE_ID}.txt
#mv $WB_WORKING_DIR/global_best_prob.txt $OUTPUT_DIR/global_best_prob_${PARTICLE_ID}.txt
#mv $WB_WORKING_DIR/local_best_prob.txt $OUTPUT_DIR/local_best_prob_${PARTICLE_ID}.txt

mv $WB_WORKING_DIR/local_fitness.txt ${OUTPUT_DIR}/local_fitness_${PARTICLE_ID}.txt

#mv $WB_WORKING_DIR/prob.txt $OUTPUT_DIR/prob_${PARTICLE_ID}.txt
#mv $WB_WORKING_DIR/prob_w.txt $OUTPUT_DIR/prob_w_${PARTICLE_ID}.txt
#mv $WB_WORKING_DIR/rate_log.txt $OUTPUT_DIR/rate_log_${PARTICLE_ID}.txt
#mv $WB_WORKING_DIR/repeat_counter.txt $OUTPUT_DIR/repeat_counter_${PARTICLE_ID}.txt
#mv $WB_WORKING_DIR/run_counter.txt $OUTPUT_DIR/run_counter_${PARTICLE_ID}.txt
#mv $WB_WORKING_DIR/ttime.txt $OUTPUT_DIR/ttime_${PARTICLE_ID}.txt



# Remove job base directory, the Webots working directory
rm -r $JOB_BASE_DIR
echo "(`date`) Job ${GEN_ID}_${PARTICLE_ID} completed by particle $PARTICLE_ID on node $($(PARTICLE_ID)+1)"
