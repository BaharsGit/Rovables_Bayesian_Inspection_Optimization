# PSO for Self-assembling Robots AWS
This repository describes the steps to deploy multiple distributed Webots simulations that communicate with a master node on AWS. The simulation uses PSO to optimize the parameters of self-assembling Lily robots as well as the physics of the fluid in which they float.

## Table of Content

* 1 [Goal](#1-goal)
* 2 [Provided simulation](#2-provided-simulation)
    * 2.1 [Simulation description](#21-simulation-description)<br>
    * 2.2 [File structure](#22-file-structure)<br>
    * 2.3 [Conversion to Webots R2022a](#23-conversion-to-webots-r2022a)<br>
* 3 [Amazon account](#3-amazon-account)<br>
* 4 [Global cloud solution](#4-global-cloud-solution)<br>
    * 4.1 [Diagram](#41-diagram)<br> 
    * 4.2 [New file structure for AWS](#42-new-file-structure-for-aws)<br>
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
The original simulation was running on Webots 8.5.4, which was released early 2017. Therefore, a few modifications must be applied for the project to run on Webots R2022a. The changes are commented directly on the files in the commits of the repository. The following description of changes contains links to the various comments.

| Modification  | Related comments |
| ------------- | ------------- |
| **NUE/RUB conversion to ENU/FLU** <br> Since Webots R2022a the general coordinate system has changed. The world coordinates are now expressed in the ENU system, while robots use the FLU convention for better consistency with other libraries, like ROS for example. A [Python script](https://github.com/cyberbotics/webots/blob/master/scripts/converter/convert_nue_to_enu_rub_to_flu.py) allows to perform an automatic conversion of the worlds and PROTO files. The script is run on the world file `24Lilies_LaLn.wbt` and the PROTO file `Lily.proto` **before** the first launch of Webots R2022a on the project. Connectors and light sensors of the PROTO were not rotated correctly by the script, therefore needing a manual rotation. | [`24Lilies_LaLn.wbt`](https://github.com/cyberbotics/pso_self-assembly_aws/commit/e3eadd9a534fcbf60528d8b2217649929bfa684d#r71881505) <br><br> [`Lily.proto`](https://github.com/cyberbotics/pso_self-assembly_aws/commit/6d31419e7ae15d255b3758ddea045ef61d7126e8#r71882582)  |
| **Robot teleportation** <br> `supervisor_track_LaLn` teleports the robots to a random initial configuration before each run. Because of the new coordinate system, Y and Z axis must be switched when setting the new position of each robot.  | [`supervisor_track_LaLn`](https://github.com/cyberbotics/pso_self-assembly_aws/commit/9b76090af9b1793b1250c4b631654bbe3fea94bf#r71880041) |
| **Physics plugin** <br> The new coordinate system has a large impact on the physics plugin, because it is mainly applying forces along the different axis. The velocity of the fluid at each coordinate of the cylinder is stored in a text file. This text file is not modified. Instead, the coordinates are read in a transposed manner to keep the same representation as before, but simply used in the new coordinate system. This conversion also impacts the discrete cells representation and the access to the velocity table in getFlowVelocity(). Finally, in computeDrag() and computeDrag_randn(), the Y and Z axis of the faces are swapped. The faces order in the code is not the same as before, but the forces are still applied correctly everywhere and the final behavior is exactly the same. | [`15Lilies`](https://github.com/cyberbotics/pso_self-assembly_aws/commit/b058b90f2307f7aae7d616e40a12fb2445197b88) |
| **Supervisor node is deprecated** <br> The Supervisor node doesn't exist anymore. It has been replaced by a Supervisor field in the Robot field. Multiple files must be updated to this new feature. | [`24Lilies_LaLn.wbt`](https://github.com/cyberbotics/pso_self-assembly_aws/commit/e3eadd9a534fcbf60528d8b2217649929bfa684d#r71881566)<br><br>[`Lily.proto`](https://github.com/cyberbotics/pso_self-assembly_aws/commit/6d31419e7ae15d255b3758ddea045ef61d7126e8#r71882440)<br>[`Lily.proto`](https://github.com/cyberbotics/pso_self-assembly_aws/commit/6d31419e7ae15d255b3758ddea045ef61d7126e8#r71882460) |
| **data field is now customData** <br> The data field has been renamed customData. Lilys are affected by this change. | [`lily_ack_epm_com_LaLn`](https://github.com/cyberbotics/pso_self-assembly_aws/commit/e3eadd9a534fcbf60528d8b2217649929bfa684d#r71881566) <br><br> [`Lily.proto`](https://github.com/cyberbotics/pso_self-assembly_aws/commit/6d31419e7ae15d255b3758ddea045ef61d7126e8#r71882470) |
| **Gravity field** <br> The Gravity field in the WorldInfo node was a 3D vector before. It has been converted to a single float value. |       [`supervisor_track_LaLn`](https://github.com/cyberbotics/pso_self-assembly_aws/commit/9b76090af9b1793b1250c4b631654bbe3fea94bf#r71879753)<br> [`supervisor_track_LaLn`](https://github.com/cyberbotics/pso_self-assembly_aws/commit/9b76090af9b1793b1250c4b631654bbe3fea94bf#r71879844)<br> [`supervisor_track_LaLn`](https://github.com/cyberbotics/pso_self-assembly_aws/commit/9b76090af9b1793b1250c4b631654bbe3fea94bf#r71880073)<br> [`supervisor_track_LaLn`](https://github.com/cyberbotics/pso_self-assembly_aws/commit/9b76090af9b1793b1250c4b631654bbe3fea94bf#r71880102)<br> [`supervisor_track_LaLn`](https://github.com/cyberbotics/pso_self-assembly_aws/commit/9b76090af9b1793b1250c4b631654bbe3fea94bf#r71880120)<br> [`supervisor_track_LaLn`](https://github.com/cyberbotics/pso_self-assembly_aws/commit/9b76090af9b1793b1250c4b631654bbe3fea94bf#r71880133) |
| **New command to reload a simulation** <br> The previous command to reload a simulation was wb_supervisor_simulation_revert(). It has be changed to wb_supervisor_world_reload(). |       [`supervisor_track_LaLn`](https://github.com/cyberbotics/pso_self-assembly_aws/commit/9b76090af9b1793b1250c4b631654bbe3fea94bf#r71880323) |
| **Fixed a crash in the plugin** <br> The Parameters[] variable was declared as const but values are assigned further in the code, involving a crash at Webots startup. |       [`15Lilies`](https://github.com/cyberbotics/pso_self-assembly_aws/commit/b058b90f2307f7aae7d616e40a12fb2445197b88#r71883468) |
 
## 3 Amazon account
Create an account on the [AWS welcome page](https://aws.amazon.com/?nc1=h_ls).
* Click on _Create an AWS account_ <br>
![](https://github.com/cyberbotics/inspection_sim_aws/blob/main/images/create_account.png) 
* Enter your email, password and username
* Enter your personal informations
* Enter your credit card informations
* Confirm your identity using your phone number
* Choose a free or paying support plan
* Head to the management console<br>
![](https://github.com/cyberbotics/inspection_sim_aws/blob/main/images/manage_console.png) 
* Lastly, set your region on the upper-right corner of the console <br>
![](https://github.com/cyberbotics/inspection_sim_aws/blob/main/images/region_select1.png) 

## 4 Global cloud solution
### 4.1 Diagram
The global implementation in the Amazon cloud is shown in the diagram below.

<div align = center>

<img src="https://github.com/cyberbotics/pso_self-assembly_aws/blob/main/docs/images/aws_solution_diagram.png" width=700/>
  
</div>

Three services are involved in the final solution: Elastic Cloud Compute (EC2), Elastic File System (EFS) and AWS Batch. The simulation files are stored in an EFS file system, as well as log files resulting from a finished simulation. This storage can be accessed by the user through an EC2 instance, basically an OS based server, by mounting the file system to it. This way the user can edit the files and access to the results. AWS Batch uses Docker images to deploy container nodes to temporary server instances. The official Webots Docker image is used and retrieved by AWS Batch. AWS Batch is the core of the implementation, as it is responsible for running the multiple containers in parallel with the help of the EFS providing the simulation files. The user starts the distributed process directly from the AWS Batch console.

### 4.2 New file structure for AWS
The deployement of the distributed nodes on AWS Batch requires a few modifications to the file system structure. The new architecture is the following.

<div align = center>

<img src="https://github.com/cyberbotics/pso_self-assembly_aws/blob/main/docs/images/aws_file_structure.png" width=700/>
  
</div>

The strategy is to use the _multi-node parallel jobs_ feature of AWS Batch. It allows to start several nodes, including a main one and all other children. Each node gets an environment variable with its index number and one with the index of the main node. The main node runs the PSO algorithm while the children nodes each evaluate one particle of the swarm. Therefore, the number of nodes deployed is equal to (N+1), with N the number of particles in the swarm.

A new `run_experiment.sh` script is started in each node and is responsible for running the correct script in function of the node index. In the main node, the Python PSO script `PSO_tocluster.py` is started, while, in the children nodes, the `job_lily_parallel.sh` file is executed (see [comment1](https://github.com/cyberbotics/pso_self-assembly_aws/commit/1e7eaca17a795653d8397f23d95d22884b79f40e#r72407227), [comment2](https://github.com/cyberbotics/pso_self-assembly_aws/commit/1e7eaca17a795653d8397f23d95d22884b79f40e#r72407269) and [comment3](https://github.com/cyberbotics/pso_self-assembly_aws/commit/1e7eaca17a795653d8397f23d95d22884b79f40e#r72407324)).  

As can be observed, the original `job_lily_parallel.sub` file has been replaced by an equivalent `job_lily_parallel.sh` file. The global code is kept the same. The local Webots working directory is now a `tmp/job#_#` directory defined by the generation and particles indexes ([comment1](https://github.com/cyberbotics/pso_self-assembly_aws/commit/1e7eaca17a795653d8397f23d95d22884b79f40e#r72407091)). The command to start Webots is also adapted ([comment2](https://github.com/cyberbotics/pso_self-assembly_aws/commit/1e7eaca17a795653d8397f23d95d22884b79f40e#r72407126)). The script is still responsible for copying the `prob.txt` and `local_fitness.txt` files between the result directory and the temporary working directory.

The number of particles to be used in the PSO alogrithm is automatically defined by the number of nodes started from AWS Batch. To run PSO with 15 particles, 16 nodes should be executed. This functionality has been added in the following commits: [comment1](https://github.com/cyberbotics/pso_self-assembly_aws/commit/1e7eaca17a795653d8397f23d95d22884b79f40e#r72407059) and [comment2](https://github.com/cyberbotics/pso_self-assembly_aws/commit/1e7eaca17a795653d8397f23d95d22884b79f40e#r72665836). The minimum number of particles is 2, so at least 3 nodes must be started ([comment3](https://github.com/cyberbotics/pso_self-assembly_aws/commit/28f577b84f2e4af92329a915e981467582603391#r72407582)).

The communication between nodes is provided by the file system. When the `prob_#.txt` files are created by the PSO algorithm in the main node, the `run_experiment.sh` script in the children nodes detects it and runs `job_lily_parallel.sh` to start a Webots instance. In the same way, when a child node has finished its job, the `local_fitness_#.txt` file is copied back to the `Generation_#` directory and the PSO algorithm can tell that this particular child is ready for the next generation. The simplified detection in `PSO_tocluster.py` is done here: [comment1](https://github.com/cyberbotics/pso_self-assembly_aws/commit/9131699c7afbaeb770d5d3f4d5282633df812676#r72406859). In `run_experiment.sh`, the detection is done here: [comment2](https://github.com/cyberbotics/pso_self-assembly_aws/commit/1e7eaca17a795653d8397f23d95d22884b79f40e#r72667405). When a child node has finished its particle job, it turns to idle mode, increases the generation index and waits for the following iteration to run a new particle (see [comment3](https://github.com/cyberbotics/pso_self-assembly_aws/commit/1e7eaca17a795653d8397f23d95d22884b79f40e#r72667403)). 

Since the communication is based solely on the file system, the different runs of the PSO must be distinguished using different folders. The Python script is therefore responsible for creating a `Run_#` folder to store all `Generation_#` directories and the resulting files ([comment1](https://github.com/cyberbotics/pso_self-assembly_aws/commit/0f932b01e90a7a91cec78411ae12987715285be4#r72407963)). The paths of other scripts are also updated to remain consistent ([comment2](https://github.com/cyberbotics/pso_self-assembly_aws/commit/0f932b01e90a7a91cec78411ae12987715285be4#r72408012), [comment3](https://github.com/cyberbotics/pso_self-assembly_aws/commit/0f932b01e90a7a91cec78411ae12987715285be4#r72408041) and [comment4](https://github.com/cyberbotics/pso_self-assembly_aws/commit/0f932b01e90a7a91cec78411ae12987715285be4#r72408076)).


