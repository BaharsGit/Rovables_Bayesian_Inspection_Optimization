/*
 * File:         spervisor_track.c
 * Description:  Supervisor to track robots
 * Author:       EDM
 Edited: Hala Khodr: PSO Algorithm. 
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>
#include <webots/robot.h>
#include <webots/supervisor.h>
#include <webots/emitter.h>

double sim_time;

int time_step;
#define N_ROBOTS 15
#define ROBOT_DIST 0.05						// minimun initial distance between robots is 5 cm
#define ARENA_R 0.2						// maximum radius of initial position of robots is arena_radius - 3 cm
#define SQ(x)                   ((x)*(x))

#define MAX_TIME 			4*3600//2*3600 // seconds
#define LOG_START_TIME	0.0				// Start logging after some time, to discard transient state
#define LOG_END_TIME	(LOG_START_TIME+MAX_TIME)				// log for some time
#define NUM_OF_RUNS 2

double time_st, time_end, time_temp = 0;

#define N_MACRO_CONFIGS 	5 //6
#define N_SIDES				4 // 4 sides for lily robots
#define N_REPS				10

time_t T;
static WbNodeRef robot_node[N_ROBOTS];
static WbNodeRef world_node;
static WbFieldRef robot_field_pos[N_ROBOTS];
static WbFieldRef robot_field_orient[N_ROBOTS];
static WbFieldRef robot_field_data[N_ROBOTS];

static WbFieldRef gravity_field;
static const double *position;
static const char *data;

static char ack_name[256];

static char fitness_repeat_name[256];
static char local_fitness_name[256];
static char prob_name[256];
static char repeat_counter_name[256];


static FILE *ack;
static FILE *read_fitness_local;
static FILE *read_prob;
static FILE *read_repeat;
static FILE *read_fitness_repeat;


// macro states variables
static int labels[N_ROBOTS]; 				// labels of each lily unit
static int labels_prev[N_ROBOTS];
static int macro_state[N_MACRO_CONFIGS];	// macro state of system
static int macro_state_prev[N_MACRO_CONFIGS]; // prev macro state
static int macro_state_labels_unique[N_MACRO_CONFIGS] = { 0,2,4,6,8 }; //{ 0,2,4,6,8,10 }; // unique labels that indicate configuration types
static int macro_state_labels_unique_size[N_MACRO_CONFIGS] = { 1,2,3,4,5 }; //{ 1,2,3,4,5,6 };

// main supervisor functions

static bool supervisor_init(void);
bool init_success;
static int supervisor_step(void);
static void position_init(void);
int incons = 0;

bool label_change();

void label_init();
void macro_position_init();
bool reenableGravity();
bool disableGravity();
bool check_consistency();
static bool inconsistent;

/////////////////////////////
//fitness variables here 
double getfitness();
#define MAX_YIELD N_ROBOTS/N_MACRO_CONFIGS
static double deltaT[MAX_YIELD] ;//= { 3600,3600,3600,3600 };
void reinitialize_delta();
/////////////////////////////////


//////////////////////////////////
//prob variables goes here 
#define PROB_SIZE 3 //4
//#define nb_prob 9
//#define repeat 4
double prob_this[PROB_SIZE];
//static int prob_test[nb_prob]={RAND_MAX/1000,RAND_MAX/625,RAND_MAX/125,RAND_MAX/25,RAND_MAX/10,RAND_MAX/5,(RAND_MAX/5)*2,RAND_MAX/2,(RAND_MAX/5)*4};
/////////////////////////////


/////////////////////////////////
//PSO//

#define PSO_W  -0.1832 // parameter w in PSO
#define PSO_PW 0.5287 // parameter pw in PSO
#define PSO_NW 3.1913 // parameter nw in PSO

#define PSO_S 1 //Swarm size 
#define NB_RUN 1 // the number of run
#define NOISE_RESISTANT 1 // enables the node resistant version of PSO
#define repetition 2 // If noise resistant how many iterations? 
#define MAX_PROB 1
static int repeated;
////////////////////////////////

////////////////////////////////////
//Optimization functions and variables 
double prob[PSO_S][PROB_SIZE];
double prob_w[PSO_S][PROB_SIZE];
double local_best[PSO_S][PROB_SIZE];
double global_best[PROB_SIZE];
double fitness_local[PSO_S];   //
double fitness_local_prev[PSO_S];//
double fitness_repeat[repetition];
double fitness_best = (double)RAND_MAX;//
void run();
void evaluate();
int init_prob(void);
double rand01();
void initialize_local();
///////////////////////////////////
///to read record/////

int run_repeat = 0;

int done=0;
//////////////////////
static int print_counter = 0;
// main 

int main()
{
	srand(time(&T));
	time_st = 0;
	time_end = LOG_END_TIME;

	// initialize Webots
	wb_robot_init();

	// get simulation step in milliseconds
	time_step = wb_robot_get_basic_time_step();
        
       
       reinitialize_delta();
         
	//emitter = wb_robot_get_device("supervisor_emitter");
	int i;
         
	for (i = 0; i < N_ROBOTS; ++i) {
		char robot_def[128];
		sprintf(robot_def, "LILY%d", i);
		robot_node[i] = wb_supervisor_node_get_from_def(robot_def);
		robot_field_pos[i] = wb_supervisor_node_get_field(robot_node[i], "translation");
		robot_field_orient[i] = wb_supervisor_node_get_field(robot_node[i], "rotation");
	}
         
	//initilization
	init_success = supervisor_init();
	
	
	int init_probab=init_prob();
	if (!init_probab) {
        	wb_supervisor_simulation_quit(EXIT_FAILURE);
        	wb_robot_cleanup();
        	return 1;
       }
      
       read_repeat = fopen(repeat_counter_name, "r");
       if(read_repeat!=NULL)
         {
         fscanf(read_repeat,"%d",&run_repeat);
         fclose(read_repeat);
	}
      
	////////////////////////
	//For Noise Resistant 

	if (!NOISE_RESISTANT)
		repeated = 1;
	else
		repeated = repetition;
		
		
	read_fitness_repeat = fopen(fitness_repeat_name, "r");
	if(read_fitness_repeat!=NULL)
    	{for(i=0;i<repeated;i++)
        	fscanf(read_fitness_repeat,"%lf",&fitness_repeat[i]);
      fclose(read_repeat);
       }
       
	//////////////////////////////////////////////////////////////////////////////////////////////  
       run();

	//set Repetition number 
	read_repeat = fopen(repeat_counter_name, "w");
	fprintf(read_repeat, "%d ", (run_repeat) % (repeated));
	fclose(read_repeat);

	if (run_repeat == repeated) {
          	done=1;

		//Set individual number 
		//read_individual = fopen(individual_counter_name, "w");
		//fprintf(read_individual, "%d ", (run_individual) % PSO_S);
		//fclose(read_individual);
	}

	//save fitness repeat 
	read_fitness_repeat = fopen(fitness_repeat_name, "w");
	for (i = 0; i < repeated; i++)
	{
		fprintf(read_fitness_repeat, "%lf \n", fitness_repeat[i]);
	}
	fclose(read_fitness_repeat);
	///////////////////////////////////
          
          if(done==1){
	//Set fitness_local  
	read_fitness_local = fopen(local_fitness_name, "w");
	//read_fitness_local_prev = fopen(local_prev_name, "w");
	for (i = 0; i < PSO_S; i++)
	{
		fprintf(read_fitness_local, "%lf \n", fitness_local[i]);
		//fprintf(read_fitness_local_prev, "%lf \n", fitness_local_prev[i]);
	}
	fclose(read_fitness_local);
	//fclose(read_fitness_local_prev);

       ack=fopen(ack_name,"w");
       fprintf(ack,"SUCCESS");
       fclose(ack);
	/////////////////////////////////////

		printf("EXITING\n");
		wb_robot_step(0);
		wb_supervisor_simulation_quit(EXIT_SUCCESS);
		wb_robot_cleanup();
		
       
		
	}
	//
	 //printf("exiting \n");

	else
	{
		printf("reverting \n");
		wb_supervisor_simulation_revert();
		wb_robot_step(time_step);
		// cleanup Webots
		wb_robot_cleanup();
	}
       
       
	return 0;  // ignored
}


static bool supervisor_init(void) {
	int ii,i,j;
	const double grav[3] = { 0,0,0 };
	char robot_def[128];
	char* pPath;
	srand(time(&T));
	for (j = 0; j <=N_ROBOTS; j++) {
            	ii=j%N_ROBOTS;
		sprintf(robot_def, "LILY%d", ii);
		robot_node[ii] = wb_supervisor_node_get_from_def(robot_def);
		robot_field_pos[ii] = wb_supervisor_node_get_field(robot_node[ii], "translation");
		robot_field_orient[ii] = wb_supervisor_node_get_field(robot_node[ii], "rotation");
		robot_field_data[ii] = wb_supervisor_node_get_field(robot_node[ii], "la_ln");
		data = wb_supervisor_field_get_sf_string(robot_field_data[ii]);
		int e[PROB_SIZE];
		int offset;
                  
                  for(i=0;i<PROB_SIZE;i++)
                  {
                      sscanf(data," %d%n",&e[i],&offset);
                      data+=offset;
                  }
                  
  		sscanf(data, "%x",&labels[ii]);

	}
	printf("labels %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d \n", labels[0], labels[1], labels[2], labels[3], labels[4], labels[5], labels[6], labels[7], labels[8], labels[9], labels[10], labels[11], labels[12], labels[13], labels[14]);
	// disable gravity (for proper initialization)
	world_node = wb_supervisor_node_get_from_def("LiliesWorld");
	gravity_field = wb_supervisor_node_get_field(world_node, "gravity");
	wb_supervisor_field_set_sf_vec3f(gravity_field, grav);

	pPath = getenv("WB_WORKING_DIR");
	if (pPath != NULL)
		//if (0)
	{
		printf("The current path is: %s\n", pPath);
		strcat(ack_name, "ack.txt");
		sprintf(ack_name, "%s/ack.txt", pPath);
               sprintf(prob_name, "%s/prob.txt", pPath);
		sprintf(repeat_counter_name, "%s/repeat_counter.txt", pPath);
		sprintf(fitness_repeat_name, "%s/fitness_repeat.txt", pPath);
		sprintf(local_fitness_name, "%s/local_fitness.txt", pPath); 
	}
	else
	{
		strcpy(ack_name, "./ack.txt");
              strcpy(repeat_counter_name, "./repeat_counter.txt");
              strcpy(local_fitness_name, "./local_fitness.txt");
              strcpy(prob_name, "./prob.txt");
              strcpy(fitness_repeat_name, "./fitness_repeat.txt");
	}
	position_init();

	return true;
}

static int supervisor_step(void) {
	int ii,j;
	int return_flag = 0;
	for (j = 0; j <=N_ROBOTS; j++) {
            	ii=j%N_ROBOTS;
		position = wb_supervisor_field_get_sf_vec3f(robot_field_pos[ii]);
		data = wb_supervisor_field_get_sf_string(robot_field_data[ii]);
		sim_time = wb_robot_get_time();
		
		// update all labels
		labels_prev[ii] = labels[ii];
		int e[PROB_SIZE];
		int offset;
                  int i;
                  
                  for(i=0;i<PROB_SIZE;i++)
                  {
                      sscanf(data," %d%n",&e[i],&offset);
                      data+=offset;
                  }
                  
  		sscanf(data, "%x",&labels[ii]);
  		
         }
	inconsistent=!check_consistency();
         
	//////////////////////////////////////////////////////////////////////////////////////////////////////
	if (macro_state[N_MACRO_CONFIGS-1] == MAX_YIELD) { // for 24 lily robots
		return_flag = 1;
		deltaT[MAX_YIELD-1] = sim_time - getfitness() + deltaT[MAX_YIELD-1];
		
		printf("lilies in final final configuration for 24 robots\n");
	}
	if (sim_time > print_counter*720){
	printf("time %f \n", sim_time);
        	printf("macro state %d %d %d %d %d \n", macro_state[0], macro_state[1], macro_state[2], macro_state[3], macro_state[4]);
	//printf("labels %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d \n", labels[0], labels[1], labels[2], labels[3], labels[4], labels[5], labels[6], labels[7], labels[8], labels[9], labels[10], labels[11], labels[12], labels[13], labels[14]);
  	printf("deltaT %f %f %f \n", deltaT[0], deltaT[1], deltaT[2]);
  	print_counter = print_counter +1; 
  	}
	if (sim_time > time_end) { return_flag = 1; printf("Time ended\n"); }
	return return_flag;
}

static void position_init(void) {
	double pos_x[N_ROBOTS], pos_y[N_ROBOTS], set_pos[3];
	int i, j, collision;

	for (i = 0; i < N_ROBOTS; i++) {
		collision = 1;
		do {
			pos_x[i] = ARENA_R*2.0*((double)rand() / (double)RAND_MAX - 0.5);
			pos_y[i] = ARENA_R*2.0*((double)rand() / (double)RAND_MAX - 0.5);
			if (SQ(pos_x[i]) + SQ(pos_y[i]) < SQ(ARENA_R)) {	// if inside arena check collision between robots
				collision = 0;
				for (j = 0; j < i ; j++) {
					if (SQ(pos_x[i] - pos_x[j]) + SQ(pos_y[i] - pos_y[j]) < SQ(ROBOT_DIST)) {	// if robots are too close generate a new value
						collision = 1;
					}
				}
			}
		} while (collision);
		set_pos[0] = pos_x[i];
		set_pos[1] = 0.435;
		set_pos[2] = pos_y[i];
		wb_supervisor_field_set_sf_vec3f(robot_field_pos[i], set_pos);
		wb_robot_step(time_step);
		
	}
	printf("Done Init \n");
}



bool reenableGravity() {
	const double grav[3] = { 0,-9.81,0 };
	world_node = wb_supervisor_node_get_from_def("LiliesWorld");
	gravity_field = wb_supervisor_node_get_field(world_node, "gravity");
	wb_supervisor_field_set_sf_vec3f(gravity_field, grav);

	return true;
}

bool disableGravity() {
	const double grav[3] = { 0,0,0 };
	world_node = wb_supervisor_node_get_from_def("LiliesWorld");
	gravity_field = wb_supervisor_node_get_field(world_node, "gravity");
	wb_supervisor_field_set_sf_vec3f(gravity_field, grav);

	return true;
}


//checking if labels are consistent for chain 
bool check_consistency() {
	int tmp_macro_state[N_MACRO_CONFIGS] = { 0 };
	int i;
	for (i = 0; i < N_ROBOTS; i++)
	{
		int l = 0;
		while (l < N_MACRO_CONFIGS)
		{
			if (labels[i] == macro_state_labels_unique[l])
			{
				tmp_macro_state[l] = tmp_macro_state[l] + 1;

				break;
			}
			l = l + 1;
		}

	}
	int k, sum = 0;
	for (k = 1; k <= N_MACRO_CONFIGS; k++)
	{
		macro_state[k - 1] = tmp_macro_state[k - 1];
		sum = sum + tmp_macro_state[k - 1] * macro_state_labels_unique_size[k - 1];
	}
	// printf("SUM %d \n",sum);
	if (sum != N_ROBOTS)
		return 0;
	else
		return 1;

}

double getfitness()
{
	double fitness = 0;
	int i;
	for (i = 0; i < MAX_YIELD; i++)
		fitness = fitness + deltaT[i];
	return fitness;
}

void reinitialize_delta()
{
	int i = 0;
	for (; i < MAX_YIELD; i++)
		deltaT[i] = MAX_TIME;
}

bool label_change() {
	// 0: equal labels, 1: change of labels
	int i = 0;
	while (i < N_ROBOTS) {
		if (labels[i] - labels_prev[i]) {
			return 1;
		};
		i++;
	}
	return 0;
}

double average(double *fitness_repeat)
{

	double av = 0;
	int i = 0;
	for (; i < repeated; i++)
		av = av + fitness_repeat[i];

	return av / repeated;
}

/////////////////////////////////////EVALUTION FUNCTION//////////////////////////////////////////////////
void run() {
	printf("---\n");
	printf("starting ... \n");
	int i;
		 // update prob
	for (i = 0; i < PROB_SIZE; i++)
	{
		prob_this[i] = prob[0][i];
	}
	//printf("Prob of particle %d size: %d run number %d\n",j,i,k);
	evaluate();

	//printf("inconsistent: %d\n", inconsistent);
	fitness_repeat[run_repeat] = getfitness();
	run_repeat = (run_repeat + 1);
	if (run_repeat == repeated) {

		fitness_local[0] = average(fitness_repeat);
	}



}
//////////////////////////////////////////////////////////////////////////////////////////////////////////////       
//////////////////////////////////////EVALUATE INDIVIDUAL//////////////////////////////////////////////////
void evaluate() {

	printf("*** Started 24Lilies ***\n");
	bool gravityEnabled = false;
	disableGravity();
	int n;
	
	//setting the probabilities 
	for (n = 0; n < N_ROBOTS; ++n)
	{
		char label_field[256];
		   ///update my label 
                  
                  int index=0;
                  int i;
                  for(i=0;i<PROB_SIZE;i++)
                     index+=sprintf(&label_field[index],"%d ",(int)(RAND_MAX*prob_this[i]));
                  strcat(label_field,"0 0 0 0");
                  wb_supervisor_field_set_sf_string(robot_field_data[n], label_field);

	}
	
	//position_init();
	double t = 0;


	do {
		if (supervisor_step() == 1) break;
                 
		//reenable gravity
		if (t > 2.0 && gravityEnabled == false) {
			gravityEnabled = reenableGravity();
		}

	   //update deltaT for fitness calculation 
		if (macro_state[N_MACRO_CONFIGS-1] - macro_state_prev[N_MACRO_CONFIGS-1] != 0)
		{

			if (macro_state[N_MACRO_CONFIGS-1] == 1)
				deltaT[macro_state[N_MACRO_CONFIGS-1] - 1] = t;
			else
			{
				int i;
				double prev_time = 0;
				for (i = 0; i < macro_state[N_MACRO_CONFIGS-1] - 1; i++)
					prev_time = prev_time + deltaT[i];
				deltaT[macro_state[N_MACRO_CONFIGS-1] - 1] = t - prev_time;
			}
			printf("deltaT %f %f %f \n", deltaT[0], deltaT[1], deltaT[2]);

		}

		int i;
		for (i = 0; i < N_MACRO_CONFIGS; i++)
			macro_state_prev[i] = macro_state[i];
		//////////////////////////////////////////////////////////////////////////////////////////////////

		t += time_step / 1000.0;
		
	} while (wb_robot_step(time_step) != -1 && t < MAX_TIME && init_success == true);
         
	double fitness = getfitness();//macro_state[2];
	printf("fitness: %g\n", fitness);
       printf("deltaT %f %f %f \n", deltaT[0], deltaT[1], deltaT[2]);

}

int init_prob(void) {

	read_prob = fopen(prob_name, "r");
	if(read_prob==NULL) 
          	return 0;
       int n=0;
	int i = 0;
	for (; i < PSO_S; i++) {
		for (n = 0; n < PROB_SIZE; n++)
		{
			fscanf(read_prob, "%lf", &prob[i][n]);
		}
	}
	fclose(read_prob);

	printf("initialization to previous values.\n");
	return 1;
}




double rand01()
{
	return (((double)rand()) / RAND_MAX);
}


