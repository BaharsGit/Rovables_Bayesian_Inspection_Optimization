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
* 5 [Textures downloading](#5-textures-downloading)<br>
    * 5.1 [Without internet access](#51-without-internet-access)<br> 
    * 5.2 [With internet access](#52-with-internet-access)<br>
* 6 [Elastic File System (EFS)](#6-elastic-file-system-efs)<br>
    * 6.1. [Description](#61-description)<br>
    * 6.2. [Create a file system](#62-create-a-file-system)<br>
    * 6.3. [Enable NFS in your security group](#63-enable-nfs-in-your-security-group)<br>
    * 6.4. [EC2 Instance](#64-ec2-instance)<br>
    * 6.5. [Transfer files to EFS](#65-transfer-files-to-efs)<br>
    * 6.6. [Important information about EC2 instances](#66-important-information-about-ec2-instances)<br>
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
The original simulation was running on Webots 8.5.4, which was released early 2017. Therefore, a few modifications must be applied to the project to run on Webots R2022a. The changes are commented directly on the files in the commits of the repository. The following description of changes contains links to the various comments.

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
![](https://github.com/cyberbotics/pso_self-assembly_aws/blob/main/docs/images/create_account.png) 
* Enter your email, password and username
* Enter your personal informations
* Enter your credit card informations
* Confirm your identity using your phone number
* Choose a free or paying support plan
* Head to the management console<br>
![](https://github.com/cyberbotics/pso_self-assembly_aws/blob/main/docs/images/manage_console.png) 
* Lastly, set your region on the upper-right corner of the console <br>
![](https://github.com/cyberbotics/pso_self-assembly_aws/blob/main/docs/images/region_select1.png) 

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

## 5 Textures downloading
Webots downloads textures from Github when starting a world for the first time to save some space locally. This feature is problematic with the _multi-node parallel jobs_ feature of AWS Batch, as there is no internet access in the containers natively. In the Lily simulation, the Floor object is the only one requiring textures. The whole instructions explain the steps to follow for the two following possible implementations:
1. **No internet connection required**: the Floor object is deleted, as it is not needed at all in the simulation. Therefore, no texture and no internet connection is required in the nodes.
2. **Internet connection required**: the world is kept intact without any deletion. This option requires to configure internet access for the containers which costs 0.05$ per hour of usage. This option requires some additional implementation effort.

### 5.1 Without internet access
Deleting the floor object is very easy. It can be done by simply removing the few lines concerning the Floor object in `24Lilies_LaLn.wbt`. If this is the chosen option, you can go directly to section 6. If not, apply the instructions of section 5.2.

### 5.2 With internet access
The following steps taken from the [AWS documentation](https://docs.aws.amazon.com/batch/latest/userguide/create-public-private-vpc.html) must be applied. The goal is to create a Virtual Private Cloud (VPC) with one public and two private subnets. The public subnet gets a NAT gateway which allows internet access. Configuring AWS Batch later with this VPC will allow Webots to access the online textures.
* **Step 1**: Create an Elastic IP Address for your NAT Gateway. A NAT gateway requires an Elastic IP address in your public subnet, but the VPC wizard does not create one for you.
  * Open the Amazon VPC console at https://console.aws.amazon.com/vpc/.
  * In the left navigation pane, choose **Elastic IPs**.
  * Choose **Allocate new address**, 
  * Don't modify any settings and press **Allocate**.
  * Note the Allocation ID for your newly created Elastic IP address; you enter this later in the VPC wizard.

* **Step 2**: The VPC wizard automatically creates and configures most of your VPC resources for you.
  * Open the Amazon VPC console at https://console.aws.amazon.com/vpc/.
  * In the left navigation pane, disable **New VPC Experience**.
  * In the left navigation pane, choose **VPC Dashboard**.
  * Choose **Launch VPC Wizard**, **VPC with Public and Private Subnets**, **Select**.
  * For **VPC name**, give your VPC a unique name, like _internet-vpc_.
  * For **Availability Zone** of both subnets, choose **us-east-2a**.
  * For **Elastic IP Allocation ID**, choose the ID of the Elastic IP address that you created earlier.
  * Leave everything else unchange and choose **Create VPC**.

* **Step 3**: The new subnets don't have a public IP address which is mandatory for AWS Batch.
  * Open the Amazon VPC console at https://console.aws.amazon.com/vpc/.
  * In the left navigation pane, choose Subnets.
  * Select the public subnet for your VPC By default, the name created by the VPC wizard is Public subnet.
  * Choose Actions, Modify auto-assign IP settings.
  * Select the Enable auto-assign public IPv4 address check box, and then choose Save.

* **Step 4**: To improve availability of instances, add a new private subnet to your network.
  * Open the Amazon VPC console at https://console.aws.amazon.com/vpc/.
  * In the left navigation pane, choose **Subnets**.
  * Choose **Create Subnet**.
  * For **Subnet Name**, enter a name for your subnet, such as _Private subnet_.
  * For **VPC**, choose the VPC that you created earlier.
  * For **Availability Zone**, choose **us-east-2b**.
  * For **IPv4 CIDR block**, enter a valid CIDR block. For example, the wizard creates CIDR blocks in 10.0.0.0/24 and 10.0.1.0/24 by default. You could use 10.0.2.0/24 for your second private subnet.
  * Choose **Create Subnet**.

## 6 Elastic File System (EFS)
### 6.1 Description
The next step consists in using the Elastic File System (EFS) provided by Amazon to store the simulation files so that the container can access them at runtime.

EFS is a secure and fully managed file system. You can create multiple separate storages and scale as much as you want, without lowering the performances. Each file system can be accessed from many instances through the Network File System (NFS) protocol, which allows a computer to access external files over a network. EFS can be mounted on EC2 instances (see [6.4 EC2 Instances](#64-ec2-instance)) and Docker containers.

EFS are created in specific regions and must be assigned to a Virtual Private Cloud (VPC). VPCs can be defined in different regions and allow to create an isolated cloud environment for a user. To get access to a file system, a container or a EC2 instance must be configured in the same VPC. By default, a VPC is already created on a fresh AWS account. If you followed instructions of [5.2 With internet access](#52-with-internet-access), you have created a custom one for this project.

<div align = center>

  <img src="https://github.com/cyberbotics/pso_self-assembly_aws/blob/main/docs/images/efs_structure.png" width="600"/>
  
  source: [EFS - How it works ?](https://docs.aws.amazon.com/efs/latest/ug/how-it-works.html)
</div>

### 6.2 Create a file system
To create a file system head to [Elastic File System](https://us-east-2.console.aws.amazon.com/efs/get-started?region=us-east-2#/get-started) and click on _Create file system_.<br>
![](https://github.com/cyberbotics/pso_self-assembly_aws/blob/main/docs/images/efs_create.png)

In the pop-up window, indicate a name for your file system and select a VPC.<br>
<div align = center>
<img src="https://github.com/cyberbotics/pso_self-assembly_aws/blob/main/docs/images/efs_create_popup.png" width="500"/>
</div>

If you want to use internet in your containers, choose the newly created _internet-vpc_. If not, you can choose the default one.
![](https://github.com/cyberbotics/pso_self-assembly_aws/blob/main/docs/images/efs_internet_vpc.png)

Now, to access our file system from a local machine, the following workflow must be applied:
1. Enable NFS to the file system.
2. Create an Ubuntu EC2 instance.
3. Connect to the instance using SSH.
4. Mount the EFS on the instance.

### 6.3 Enable NFS in your security group
A created file system is automatically assigned to a default security group. Security groups act as firewalls to define authorized in and out connections and protocols. In our case, we need the NFS protocol to be activated to access the EFS via NFS from SSH or from the Docker container.

* Get to your [Security Groups](https://us-east-2.console.aws.amazon.com/vpc/home?region=us-east-2#securityGroups:) and click on your default security group. If you have multiple ones, choose the one associated with the VPC you have selected in the last step, when creating the file system.
    ![](https://github.com/cyberbotics/pso_self-assembly_aws/blob/main/docs/images/sg_default_list.png)
 
* Click on _Edit inbound rules_. <br>
    ![](https://github.com/cyberbotics/pso_self-assembly_aws/blob/main/docs/images/sg_edit_inbound.png)
* Click on _Add Rule_. <br>
    ![](https://github.com/cyberbotics/pso_self-assembly_aws/blob/main/docs/images/sg_add_rule.png)
* Add a new NFS rule as shown in the illustration below. (Source = Anywhere - IPv4) <br>
    ![](https://github.com/cyberbotics/pso_self-assembly_aws/blob/main/docs/images/sg_nfs_rule.png)
    
### 6.4 EC2 Instance
Elastic Compute Cloud (EC2) is one of the main services provided by AWS. It allows to create a virtual server which is hosted on EC2 to launch applications. Amazon offers all types of servers, with different operating systems, storage sizes, machine power and network infrastructure. Instances are created from Amazon Machine Images (AMI) which are provided by Amazon or can be found on the Marketplace. Example AMIs are different releases of Ubuntu or Windows or specific environments made available by other companies.

For this work, only a simple Ubuntu server is needed to mount a file system. Keep in mind that this part is only about accessing the file system from a local machine and not running containers on these instances. Running the simulations is discussed in a further section.

* To create an EC2 instance, head to [AWS EC2](https://us-east-2.console.aws.amazon.com/ec2/v2/home?region=us-east-2#Instances:sort=desc:instanceState) and click on launch instances.<br>
    ![](https://github.com/cyberbotics/inspection_sim_aws/blob/main/images/ec2_launch_instances.png)
* Choose Ubuntu 20.04 in the list of AMIs.<br>
    ![](https://github.com/cyberbotics/inspection_sim_aws/blob/main/images/ec2_ubuntu20.png)
* At step 2, choose a _t2.micro_ type of instance. We only need to mount a file system so no more resources are needed.<br>
    ![](https://github.com/cyberbotics/inspection_sim_aws/blob/main/images/ec2_instance_type.png)
* Step 3 (details) and step 4 (storage) can be left as default.
* Add a name tag to your instance, EFSMount for example.<br>
    ![](https://github.com/cyberbotics/inspection_sim_aws/blob/main/images/ec2_tag.png)
* Step 6 is about security groups. Create a new security group with a NFS rule accessible anywhere. This way the instance allows the NFS protocol to mount the EFS.<br>
    ![](https://github.com/cyberbotics/inspection_sim_aws/blob/main/images/ec2_security_group.png)
* Step 7 allows you to review your instance, simply click on the _Launch_ button.
* A pop-up window will show up asking you to configure a SSH key pair. Create a new RSA key pair, give it a name and download it using the corresponding button. The downloaded file will be useful to access the instance via SSH. Once done, launch the new instance. <br>
    <div align = center>
    <img src="https://github.com/cyberbotics/inspection_sim_aws/blob/main/images/ec2_ssh_key.png" width="500"/>
    </div>
    
* Your EC2 console should now contain a launched instance. Note the public IPv4 address needed for ssh connection. <br>
    ![](https://github.com/cyberbotics/inspection_sim_aws/blob/main/images/ec2_launched_instance.png)

### 6.5 Transfer files to EFS
Now that the Ubuntu server is active, a SSH connection can be established.
* Open a local terminal and get to the directory containing the .pem file.
``` console
cd /path/to/file.pem
```

* Change permissions of the file.
``` console
chmod 400 file.pem
```

* Connect to the EC2 instance using the pem file and the public IP address.
``` console
ssh -i file.pem ubuntu@<EC2-public-IPv4-address>
```

* _nfs-common_ is a package which allows the configuration of systems using the NFS protocol. Install _nfs-common_ with the following commands.
``` console
sudo apt install nfs-common
nfsstat --version
```

* Create a directory to mount the EFS on. Mount the file system to the newly created folder. The file system IP address can be found in the _Network_ tab of your EFS in the AWS console. There is no difference between the three addresses displayed.
``` console
mkdir efs
sudo mount -t nfs4 <fs_IPaddress>:/ efs
```

![](https://github.com/cyberbotics/inspection_sim_aws/blob/main/images/efs_network_tab.png)

* Update permisssion for the efs folder.
```console
sudo chown ubuntu efs
```

* You can now copy simulation files from your local machine to the EFS. Note that here the IP address is the one of the EC2 and not the one of the EFS directly.
``` console
scp -i file.pem -r ./path/to/aws_demo ubuntu@<EC2-public-IPv4-address>:~/efs/demo
```

Note that **the controllers cannot be compiled on the EC2 instance** (unless you install Webots on it, which is not necessarily the easiest option). Therefore, the best way to proceed is to modify and compile the controllers locally. Once the controller is built, the entire folder can be transferred to the EC2 instance via SSH using the corresponding command above.

### 6.6 Important information about EC2 instances
The only purpose of the EC2 instance here is to create a link to the EFS service and access the file system. The EC2 instance only needs to be started when the files need to be modified. It is not needed to run containers in parallel. Keeping even a small EC2 instance running costs money. Therefore, it is best to stop it when it is not needed. To do this, go to your [EC2 console](https://us-east-2.console.aws.amazon.com/ec2/v2/home?region=us-east-2#Instances:), select your running instance and stop it using the _Instance state_ drop-down menu and _Stop instance_ button.<br>

![](https://github.com/cyberbotics/inspection_sim_aws/blob/main/images/ec2_instance_state.png)<br>

The instance can be started again from this page when needed.





      
