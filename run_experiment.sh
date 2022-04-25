#!/bin/sh

# Get the current AWS job index
# line=$((AWS_BATCH_JOB_ARRAY_INDEX + 1))
# seed=$(sed -n ${line}p /usr/local/efs/demo/seed_array.txt)

# Run experiment according to the seed and simulation parameters
echo "Running Webots instance"
webots --batch --stdout --stderr --mode=fast /usr/local/efs/pso_self-assembly_aws/worlds/24Lilies_LaLn.wbt 
