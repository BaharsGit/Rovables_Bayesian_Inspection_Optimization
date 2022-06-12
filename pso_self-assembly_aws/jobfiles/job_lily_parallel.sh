#!/bin/bash
#$ -N lily
#$ -S /bin/bash
#$ -cwd
#$ -j y
##$ -m eas
#$ -t 1-1
##$ -p -512

echo $(pwd)
GEN_ID=$1 
INDIVID_ID=$2
# GEN_ID=0
# INDIVID_ID=1
WORST_FITNESS=43200

WB_TIMEOUT=30           # Kill webots after WB_TIMEOUT seconds
#WB_TIMEOUT=15           # Kill webots after WB_TIMEOUT seconds
 
N_RUNS=1 #number of runs to be done

WEBWORLD="../worlds/bayes_pso.wbt"

# set the input directory (relative to the working directory)
INPUT_DIR=Generation_${GEN_ID}
echo ${INPUT_DIR}


# Output directory to put results
OUTPUT_DIR=Generation_${GEN_ID}
echo ${OUTPUT_DIR}

# set the job base directory 
JOB_BASE_DIR=$(pwd)/tmp/job${GEN_ID}_${INDIVID_ID}
echo ${JOB_BASE_DIR}

# create the working directory

if [ ! -d $JOB_BASE_DIR ]

then

   echo "(`date`) Create base directory $JOB_BASE_DIR"

   mkdir -p $JOB_BASE_DIR

fi

 
# set the home directory locally so that Webots writes its log files there (dirty hack)

#export HOME=$JOB_BASE_DIR

# set the home directory locally so that Webots writes its stuff there
#export HOME=/home/${USER}
export WB_WORKING_DIR=$JOB_BASE_DIR

echo "(`date`) Performing $N_RUNS runs for the following parameters:"

 
# perform the runs
TRIAL_COUNTER=1

for (( RUN_ID=1; RUN_ID<=$N_RUNS; RUN_ID++ )) 

do

   #export WB_WORKING_DIR=${JOB_BASE_DIR}

 

   # create the directory for this run

   #mkdir $WB_WORKING_DIR

   # copy the input parameters

   cp ${INPUT_DIR}/prob_${INDIVID_ID}.txt $WB_WORKING_DIR/prob.txt
   #echo $WB_WORKING_DIR/prob.txt
   
   

   echo "(`date`) Launching webots (run $RUN_ID)"

   
   # launch webots
   timeout $WB_TIMEOUT  xvfb-run webots --batch --mode=fast --stdout --stderr --no-rendering $WEBWORLD &> $WB_WORKING_DIR/webots_log.txt # logs are redirected to a txt file
 

   # waiting just a while before copying the output

   sleep 1

 

   # checking whether run was successful

   if [ -e $WB_WORKING_DIR/local_fitness.txt ] 

   then

      echo "(`date`) Run $RUN_ID successfully completed"

      rm $WB_WORKING_DIR/ack.txt

   else

      echo "(`date`) Run $RUN_ID failed, cleaning up, and running again"

      ((TRIAL_COUNTER--))

      if [ $TRIAL_COUNTER -gt 0 ]

      then

      	# performing the run again

      	((RUN_ID--))

      else 

        echo "(`date`) RUN got stuck, auxilary fitness file created"

	echo ${WORST_FITNESS} >> $WB_WORKING_DIR/local_fitness.txt

	rm $WB_WORKING_DIR$/ack.txt

      fi

   fi

 

   sleep 1

done

 

#  # create the output directory
if [ ! -d $OUTPUT_DIR ]
then
	echo "(`date`) Create output directory $OUTPUT_DIR"
	mkdir $OUTPUT_DIR
fi
# move results to output dir

#mv $WB_WORKING_DIR/global_best_fitness.txt $OUTPUT_DIR/global_best_fitness_${INDIVID_ID}.txt
#mv $WB_WORKING_DIR/global_best_prob.txt $OUTPUT_DIR/global_best_prob_${INDIVID_ID}.txt
#mv $WB_WORKING_DIR/local_best_prob.txt $OUTPUT_DIR/local_best_prob_${INDIVID_ID}.txt
mv $WB_WORKING_DIR/local_fitness.txt ${OUTPUT_DIR}/local_fitness_${INDIVID_ID}.txt
#mv $WB_WORKING_DIR/prob.txt $OUTPUT_DIR/prob_${INDIVID_ID}.txt
#mv $WB_WORKING_DIR/prob_w.txt $OUTPUT_DIR/prob_w_${INDIVID_ID}.txt
#mv $WB_WORKING_DIR/rate_log.txt $OUTPUT_DIR/rate_log_${INDIVID_ID}.txt
#mv $WB_WORKING_DIR/repeat_counter.txt $OUTPUT_DIR/repeat_counter_${INDIVID_ID}.txt
#mv $WB_WORKING_DIR/run_counter.txt $OUTPUT_DIR/run_counter_${INDIVID_ID}.txt
#mv $WB_WORKING_DIR/ttime.txt $OUTPUT_DIR/ttime_${INDIVID_ID}.txt

# remove job base directory
rm -r $JOB_BASE_DIR
echo "(`date`) Job ${GEN_ID}_${INDIVID_ID} completed"
