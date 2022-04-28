# PSO for Self-assembling Robots AWS
This repository describes the steps to deploy multiple distributed Webots simulations that communicate with a master node on AWS. The simulation uses PSO to optimize the parameters of self-assembling Lily robots as well as the physics of the fluid in which they float.

## Table of Content

* 1 [Goal](#1-goal)
* 2 [Provided simulation](#2-provided-simulation)
    * 2.1 [Simulation description](#21-simulation-description)<br>
    * 2.2 [File structure](#22-file-structure)<br>
    * 2.3 [Conversion to Webots R2022a](#23-conversion-to-webots-r2022a)<br>
    * 2.4 [New file structure for AWS](#24-new-file-structure-for-aws)<br>
* 3 [Docker container](#3-docker-container)<br>
    * 3.1 [Docker containers](#31-docker-containers)<br>
    * 3.2 [For this project](#32-for-this-project)<br>
* 4 [Amazon account](#4-amazon-account)<br>
* 5 [Global cloud solution](#5-global-cloud-solution)<br>
* 6 [Elastic Container Registry (ECR)](#6-elastic-container-registry-ecr)<br>
    * 6.1 [Description](#61-description)<br>
    * 6.2 [Create repository](#62-create-repository)<br>
        * 6.2.1 [Private repository](#621-private-repository)<br>
        * 6.2.2 [Public repository](#622-public-repository)<br>
    * 6.3 [IAM authorization](#63-iam-authorization)<br>
    * 6.4 [Configure AWS CLI](#64-configure-aws-cli)<br>
    * 6.5 [Upload Docker image](#65-upload-docker-image)<br>
* 7 [Elastic File System (EFS)](#7-elastic-file-system-efs)<br>
    * 7.1. [Description](#71-description)<br>
    * 7.2. [Create a file system](#72-create-a-file-system)<br>
    * 7.3. [Enable NFS in your security group](#73-enable-nfs-in-your-security-group)<br>
    * 7.4. [EC2 Instance](#74-ec2-instance)<br>
    * 7.5. [Transfer files to EFS](#75-transfer-files-to-efs)<br>
    * 7.6. [Important information about EC2 instances](#76-important-information-about-ec2-instances)<br>
* 8 [AWS Batch Service](#8-aws-batch-service)<br>
    * 8.1 [Description](#81-description)<br>
    * 8.2 [Configuration](#82-configuration)<br>
        * 8.2.1 [Compute environment](#821-compute-environment)<br>
        * 8.2.2 [Job queue](#822-job-queue)<br>
        * 8.2.3 [Job definition](#823-job-definition)<br>
* 9 [Run simulations](#9-run-simulations)<br>
* 10 [Results](#10-results)<br>
      
## 1 Goal
The goal of this implementation is to parallelize multiple Webots simulations in a distributed way on a cloud service. The involved simulation, described in the next section, is provided by Harvard University and was originally created on Webots 8.5.4. The first part of this work consists in converting the simulation to Webots R2022b. 

The proposed solution is using Amazon Web Services to deploy and parallelize the provided simulation in the cloud. The work is structured as follows. First, a brief description of the simulation is provided. Next, the modifications made to the files in order to run the simulation on the cloud in Webots R2022b are presented, followed by a description of the different Amazon services involved and how to use them.

## 2 Provided simulation
### 2.1 Simulation description

The simulation involves self-assembling floating Lily robots. There are 15 Lilys in the simulation floating in a cylindrical container filled with water. 

At the beginning of the simulation, the Lilys are randomly teleported into the fluid and a physics plugin is used to simulate fluid motion, moving the robots in a circular fashion in the fluid. When two robots are close to each other and well aligned, they may eventually assemble. After some time, based on some rule, the robots may choose to remove the connection. Their goal is to form a pre-defined shape.
<div align = center>
  
https://user-images.githubusercontent.com/61198661/165769125-ff0583e6-a6bf-4268-8fe8-683adc23bfc5.mp4
  
</div>


A PSO algorithm is coded in Python and runs independently of Webots simulations. The PSO script is responsible for starting multiple Webots instances, running the simulations for some time with the chosen parameters and getting the results to process them.

The goal is to deploy this distributed mechanism in the AWS cloud.

### 2.2 File structure
The original file structure was made to deploy the different Webots instances to clusters of a local server. The structure provided is as follows:

Two scripts, stored in the `jobfiles` directory, allow to deploy multiple Webots instances in a distributed way on a local server.
* A main Python script, named `PSO_tocluster.py`, is used to run the complete PSO algorithm. It performs the particle initialization, update and writing of the final results. Current particles and final results are stored in `Generations` directories. During an iteration, when particles need to be evaluated, it runs the `job_lily_parallel.sub` script once for each instance of Webots to start on the clusters. The script is also responsible for detecting when all instances have successfully completed their work so that the algorithm can continue.
* The `job_lily_parallel.sub` script is coded in bash. It receives the indexes of the current particle to evaluate. The particle values are stored in a `prob.txt` file. This file is moved to a local working folder so that the Webots instance can read input files and produce output files independently from the Python script. `job_lily_parallel.sub` starts Webots, and when the simulation is done, moves the resulting file (named `local_fitness.txt`) back to the `Generations` folders.

The actual simulation is made of the following important files.
* `24Lilies_LaLn.wbt` is the world file. It contains the position of the different elements in the simulation.
* `Lily.proto` is the PROTO file for the floating robot. It contains the structure, as well as the sensor configuration of the Lily.
* There is a physics plugin, `15Lilies.c`, which recreates the fluid motion in Webots. At each timestep, it updates the forces applied on each robot to simulate a circular motion in the cylinder.
* `lily_ack_epm_com_LaLn.c` is the controller of the Lilys. It communicates with neighbour robots and applies rules for the linking/unlinking process.
* Finally, `supervisor_track_LaLn.c` is a supervisor responsible for reading the particle values to apply, for evaluating the fitness of the robot configurations, for writing the results back to .txt files and for quitting the simulation when the final configuration is reached or when the maximal time is reached. 

<div align = center>
  
<img src="https://github.com/cyberbotics/pso_self-assembly_aws/blob/main/docs/images/file_structure_orig.png"/>
  
</div>

### 2.3 Conversion to Webots R2022a

### 2.4 New file structure for AWS

