// File:          bayes_fsm.cpp
// Date:
// Description:
// Author:
// Modifications:
#include <stdlib.h>
#include <math.h>
#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include <time.h>
#include <webots/Robot.hpp>
#include <webots/Motor.hpp>
#include <webots/Gyro.hpp>
#include <webots/Accelerometer.hpp>
#include <webots/Camera.hpp>
#include <webots/DistanceSensor.hpp>
#include <webots/Emitter.hpp>
#include <webots/Receiver.hpp>
#include <webots/Keyboard.hpp>
#include <webots/PositionSensor.hpp>
#include <webots/Supervisor.hpp>
#include <queue>
#include <vector>
#include <cmath>
// All the webots classes are defined in the "webots" namespace
using namespace webots;

//Initialize the parameters
#define TIME_STEP 8

//Finite State Machine Parameters
#define FSM_RW 0
#define FSM_CA 1
#define FSM_PAUSE 2
#define FSM_OBS 3
#define FSM_SEND 4
#define FSM_PULL 5
#define STOP 1.0e-8
#define TINY 1.0e-30

enum Side { LEFT, RIGHT };

//Webots Parameters
static Supervisor *robot;
static Motor* motors[2]; //2
static DistanceSensor* distance_sensors[4]; //2
static PositionSensor* encoders[2];
static Node* rovNode[4];
static Field* rovData[4];
static Node* me;
static Field* myDataField;
static Emitter* emitter;
static Receiver* receiver;
static int nRobot = 4;
static const std::string rovDef[4] = {"rov_0", "rov_1", "rov_2", "rov_3"};
char *noise_seed; 

//DEFAULT Algorithm parameters -> read in algorithm parameters from file / Part of the world file. 
static int nParam = 4;
static double alpha = 1; //Alpha Prior
static double beta = 1; //Beta Prior
static int d_f = -1; //Decision Flag
static int tao = 100; //Observation interval
static double p_c = 0.99; //Credibility Threshold 
static bool u_plus = true; //Positive feedback 
static double close_distance = 15.0; //Used to check collision avoidance
static int C = 0; //Observed Color
static int obs_hysteresis = 0; //Hysterisis 

//Robot Parameters
static int robotNum;
static int FSM_STATE = 0;
static std::string name;
static double speed = 10.0;
static int rand_const_forward = 750; //Range for random value to go forward 
static int rand_const_turn = 50; //Range for random value to turn
static int pause_time = 100;
static double p;
static int direction = LEFT;
static int forward_count;
static int pause_count;
static int turn_count;
static int control_count = 0;
static double decision_time = 0;
static int obs_initial = 0;

//Arena Parameters
int boxSize = 8;
int imageDim = 128;
std::vector<int> grid_x;
std::vector<int> grid_y;
 

//Function declarations
double incbeta(double a, double b, double x); //Beta function used for calculating posterior
static int getColor(void); //Check against grid arena to observe color
static void readArena(void); //Reads in arena file
static void readParameters(void); //Reads in prob.txt produced from PSO

int main(int argc, char **argv) {
  // create the Robot instance.
  robot = new Supervisor();
  
  // get the time step of the current world.
  int timeStep = (int)robot->getBasicTimeStep();
  
  name = robot->getName();
  
  robotNum = name[1] - '0';

  noise_seed = getenv("NOISE_SEED");
  if (noise_seed != NULL) {
    std::cout << "Noise Seed: " << *noise_seed - '0' << std::endl;
    srand(*noise_seed); // Initialize seed based on instance id from PSO
  } else {
    srand(*argv[1]); //During baseline set based off generated .wbt file
  }
  
  const char *motors_names[2] = {"left motor", "right motor"};
  const char *distance_sensors_names[4] = {"left distance sensor", "right distance sensor", "angle left distance sensor", "angle right distance sensor"};
  const char *encoder_names[2] = {"left encoder", "right encoder"};
  
  // create the magnetic force 
  Motor* electromagnet = robot->getMotor("electromagnet");
  electromagnet->setPosition(INFINITY);
  electromagnet->setVelocity(1);
  
  //Motors and Encoders
  for (int i = 0; i < 2; i++) {
    motors[i] = robot->getMotor(motors_names[i]);
    motors[i]->setPosition(INFINITY); // For linear mode 

    encoders[i] = robot->getPositionSensor(encoder_names[i]);
    encoders[i]->enable(TIME_STEP);
  }
  
  //Distance Sensors
  for (int i = 0; i < 4; i++) {
    distance_sensors[i] = robot->getDistanceSensor(distance_sensors_names[i]);
    distance_sensors[i]->enable(TIME_STEP);
  }
  
  //Robot nodes
  for (int i = 0; i < nRobot; i++) {
    rovNode[i] = robot->getFromDef(rovDef[i]);
    rovData[i] = rovNode[i]->getField("customData");
  }
  
  //Receiver
  receiver = robot->getReceiver("receiver");
  receiver->enable(TIME_STEP);
 
  //Emitter
  emitter = robot->getEmitter("emitter");
  
  me = robot->getSelf();
  myDataField = me->getField("customData");
  
  //Create an initial random forward and turn counter
  forward_count = rand() % rand_const_forward;
  turn_count = rand() % rand_const_turn;
  
  //Read in the 
  readArena();
  readParameters();
  
  C = getColor();
  
  p = incbeta(alpha, beta, 0.5);

  //Main while loop
  while (robot->step(timeStep) != -1) { 

    //Print statements every 8000 Simulation Steps
    if (control_count % 8000 == 0) {
      std::cout << "FSM State: " << FSM_STATE << " Robot " << robotNum << " Belief: " << p << " -> " << alpha << ", " << beta << std::endl;
    }

    //Distance Sensor values to be updated at each simulation step
    double distance_sensors_values[4];
    for (int i = 0; i < 4; i++){
      distance_sensors_values[i] = distance_sensors[i]->getValue();
    }

    //Main FSM Logic 
    switch(FSM_STATE) {

      //RANDOM WALK STATE
      case FSM_RW:
      { 

        //COLLISION AVOIDANCE -- Enter if any distance sensor reads less than "close_distance"
        if (distance_sensors_values[LEFT] < close_distance || distance_sensors_values[RIGHT] < close_distance || distance_sensors_values[2] < close_distance || distance_sensors_values[3] < close_distance) { 
          FSM_STATE = FSM_CA;
          break;
        }
        //OBSERVE COLOR 
        else if ((control_count + robotNum) % tao == 0) {
          pause_count = pause_time; //Reset the pause count
          FSM_STATE = FSM_PAUSE;
        } 

        //Random Walk Logic
        if (forward_count > 0) {
          motors[LEFT]->setVelocity(speed);
          motors[RIGHT]->setVelocity(speed);
          forward_count = forward_count - 1;
        } else if ((forward_count == 0) && (turn_count > 0)) {
          turn_count = turn_count - 1;
          if (direction == LEFT) {
            // set the speed to turn to the left
            motors[LEFT]->setVelocity(-speed);
            motors[RIGHT]->setVelocity(speed);
          } else {
            // set the speed to turn to the right
            motors[LEFT]->setVelocity(speed);
            motors[RIGHT]->setVelocity(-speed);
          }
        } else if((forward_count == 0) & (turn_count == 0)) {
            //Once done turning, randomize again to pick turn direction, forward, and turn
            forward_count = rand() % rand_const_forward;
            turn_count = rand() % rand_const_turn;
            double dir = rand() / (float) RAND_MAX;
            if (dir > 0.5) {
              direction = RIGHT;
            } else {
              direction = LEFT;
            } 
          }
        break;
      }

      //COLLISION AVOIDANCE STATE
      case FSM_CA:
      {
        //If nothing is in front, then go back to Random Walk
        if (distance_sensors_values[LEFT] > 130 && distance_sensors_values[RIGHT] > 130 && distance_sensors_values[2] > 130 && distance_sensors_values[3] > 130) { 
          FSM_STATE = FSM_RW;
          break;
        }

        direction = distance_sensors_values[LEFT] < distance_sensors_values[RIGHT] ? RIGHT : LEFT;
        
        if (((distance_sensors_values[LEFT] < 130) && (distance_sensors_values[RIGHT] < 130)) || ((distance_sensors_values[2] < 130) && (distance_sensors_values[3] < 130))) {
          direction = -1;
        } else if (distance_sensors_values[2] < distance_sensors_values[3]) {   
          direction = RIGHT;
        } else if (distance_sensors_values[3] < distance_sensors_values[2]) {
          direction = LEFT;
        } 
        
        //std::cout << robotNum << " "<< direction << std::endl;
        if (direction == LEFT) {
          // set the speed to turn to the left
          motors[LEFT]->setVelocity(-speed);
          motors[RIGHT]->setVelocity(speed);
        } else if (direction == RIGHT ){
          // set the speed to turn to the right
          motors[LEFT]->setVelocity(speed);
          motors[RIGHT]->setVelocity(-speed);
        } else if (direction == -1){
          // set the speed to go backwards
          motors[LEFT]->setVelocity(-speed);
          motors[RIGHT]->setVelocity(-speed);
        }
        break;
      }

      //PAUSE STATE
      case FSM_PAUSE:
      {
        //Stop to observe
        motors[LEFT]->setVelocity(0);
        motors[RIGHT]->setVelocity(0);
        if (pause_count == 0) {
          FSM_STATE = FSM_OBS;
        } else {
          pause_count = pause_count - 1;
        }
        break;
      }
      
      case FSM_OBS:
      {
        C = getColor();
        alpha = alpha + C;
        beta = beta + (1 - C);
        FSM_STATE = FSM_SEND;
        //std::cout <<"Robot " << robotNum << " Index " << control_count + robotNum << std::endl;
        break;
      }
      
      case FSM_SEND:
      {
        const int *message;
        if (d_f != -1 && u_plus) {
          message = &d_f;
        } else {
          message = &C;
        }
        emitter->send(message, 4);
        FSM_STATE = FSM_PULL;
        break;
      }
      
      case FSM_PULL:
      {
        while (receiver->getQueueLength() > 0) {
          const int *cPrime = (const int *)receiver->getData();
          alpha = alpha + *cPrime;
          beta = beta + (1 - *cPrime);         
          receiver->nextPacket();
        }
        
        p = incbeta(alpha, beta, 0.5);
        int currentObservationcount = alpha + beta;
        // Logic for first time making decision
        if ((d_f == -1) && u_plus) {

          //Set initial observation hysterisis state 
          if (obs_initial == 0 && (p > p_c || (1 - p) > p_c)) {
            obs_initial = currentObservationcount;
          }
          //Resets hysterisis state 
          else if (obs_initial != 0 && (p < p_c) && ((1-p) < p_c)) {
            obs_initial = currentObservationcount;
          } 
          //Hysteresis has been met, decision flag can be set
          else if ((p > p_c || (1 - p) > p_c) && (currentObservationcount - obs_initial >= obs_hysteresis) && obs_initial != 0) {
            if (p > p_c) {
              std::cout << "Positive Feedback - Black" << std::endl;
              d_f = 0;
            } else if ((1 - p) > p_c) {
              std::cout << robotNum << " Positive Feedback - White" << std::endl;
              d_f = 1;
            }

          //Mark decision times     
          decision_time = robot->getTime();
          std::cout << robotNum << " Decision time: " << decision_time << std::endl;
          obs_initial = 0; 
          }
        } else {
        
          // Check if decision is ever flipped
          if (((d_f == 1) && (p > p_c)) || ((d_f == 0) && ((1-p) > p_c))) {
            if (obs_initial == 0) obs_initial = currentObservationcount;
            if ((currentObservationcount - obs_initial >= obs_hysteresis) && obs_initial != 0) {
              decision_time = robot->getTime();
              std::cout << robotNum << " Reset Decision time: " << decision_time << std::endl;
              if (p > p_c) {
                std::cout << "Positive Feedback - Black" << std::endl;
                d_f = 0;
              } else if ((1 - p) > p_c) {
                std::cout << robotNum << " Positive Feedback - White" << std::endl;
                d_f = 1;
              }
            }  
          } else {
            obs_initial = 0;
          }  
        }
        FSM_STATE = FSM_RW;
        break;
      }
      
    }
    //Update robot custom data field with recent belief, and decision time (if available)
    std::string currentData = myDataField->getSFString();

    p = incbeta(alpha, beta, 0.5);   

    if (d_f == -1) {
      myDataField->setSFString(std::to_string(p) + "-");
    } else {
      myDataField->setSFString(std::to_string(p) + std::to_string(decision_time));
    }
    
    //Increment control count used with observation interval
    control_count = control_count + 1;
  }

  // Enter here exit cleanup code.
  delete robot;
  return 0;
}


/*
 * zlib License
 *
 * Regularized Incomplete Beta Function
 *
 * Copyright (c) 2016, 2017 Lewis Van Winkle
 * http://CodePlea.com
 *
 * This software is provided 'as-is', without any express or implied
 * warranty. In no event will the authors be held liable for any damages
 * arising from the use of this software.
 *
 * Permission is granted to anyone to use this software for any purpose,
 * including commercial applications, and to alter it and redistribute it
 * freely, subject to the following restrictions:
 *
 * 1. The origin of this software must not be misrepresented; you must not
 *    claim that you wrote the original software. If you use this software
 *    in a product, an acknowledgement in the product documentation would be
 *    appreciated but is nBE0ot required.e
 * 2. Altered source versions must be plainly marked as such, and must not be
 *    misrepresented as being the original software.
 * 3. This notice may not be removed or altered from any source distribution.
 */

double incbeta(double a, double b, double x) {
    if (x < 0.0 || x > 1.0) return 1.0/0.0;

    /*The continued fraction converges nicely for x < (a+1)/(a+b+2)*/
    if (x > (a+1.0)/(a+b+2.0)) {
        return (1.0-incbeta(b,a,1.0-x)); /*Use the fact that beta is symmetrical.*/
    }

    /*Find the first part before the continued fraction.*/
    const double lbeta_ab = lgamma(a)+lgamma(b)-lgamma(a+b);
    const double front = exp(log(x)*a+log(1.0-x)*b-lbeta_ab) / a;

    /*Use Lentz's algorithm to evaluate the continued fraction.*/
    double f = 1.0, c = 1.0, d = 0.0;

    int i, m;
    for (i = 0; i <= 200; ++i) {
        m = i/2;

        double numerator;
        if (i == 0) {
            numerator = 1.0; /*First numerator is 1.0.*/
        } else if (i % 2 == 0) {
            numerator = (m*(b-m)*x)/((a+2.0*m-1.0)*(a+2.0*m)); /*Even term.*/
        } else {
            numerator = -((a+m)*(a+b+m)*x)/((a+2.0*m)*(a+2.0*m+1)); /*Odd term.*/
        }

        /*Do an iteration of Lentz's algorithm.*/
        d = 1.0 + numerator * d;
        if (fabs(d) < TINY) d = TINY;
        d = 1.0 / d;

        c = 1.0 + numerator / c;
        if (fabs(c) < TINY) c = TINY;

        const double cd = c*d;
        f *= cd;

        /*Check for stop.*/
        if (fabs(1.0-cd) < STOP) {
            return front * (f-1.0);
        }
    }

    return 1.0/0.0; /*Needed more loops, did not converge.*/
}

static int getColor() {

  Field *meField = me->getField("translation");
  const double *meV = meField->getSFVec3f();
  double xPos = meV[2];
  double yPos = meV[0];

  for (int i = 0; i < (int) grid_x.size(); i++) {
      if ((xPos >= 1.0 * grid_x[i]/imageDim) && 
      (xPos <= (1.0 * grid_x[i] + boxSize)/imageDim) && 
      (yPos >= 1.0 *grid_y[i]/imageDim) && 
      (yPos <= (1.0 *grid_y[i] + boxSize)/imageDim)) { 
          return 1; //Returns 1 if the current robot is on a white square
      }
  }

  return 0;
}

static void readArena() {
  std::string filePath;
  if (noise_seed != NULL) {
    filePath = "boxrect_" + std::string(noise_seed) + ".csv";
  } else {
    filePath = "boxrect.csv";
  }
  std::ifstream file(filePath);

  while(!file.eof()){
    std::string line;
    std::getline(file, line);
    
    std::stringstream iss(line);
    
    for (int j = 0; j < 2; j++) {
      std::string val;
      std::getline (iss, val, ',');
      std::stringstream converter(val);
      std::cout << val << std::endl;
      //Add to X or Y vector depending on location
      if (j == 0) grid_x.push_back(std::stoi(val));
      if (j == 1) grid_y.push_back(std::stoi(val));
    }
  }
  file.close();
}

//Read in the parameters from prob.txt
static void readParameters() {
  char *pPath = getenv("WB_WORKING_DIR");
  char prob_name[256];
  sprintf(prob_name, "%s/prob.txt", pPath);
  
  //Dont set the parameters if the pointer is NULL
  if (pPath != NULL) {
    std::ifstream file(prob_name);
    
    double z;
    std::cout << "Reading in Parameters: " << std::endl;
    for (int i = 0; i < nParam; i++) {
      std::string line;
      std::getline(file, line);
      const char *cstr = line.c_str();
      z = std::atof(cstr);
      std::cout << z << std::endl;
      if (i == 0) tao = z;
      if (i == 1) alpha = round(z);
      if (i == 2) rand_const_forward = z;
      if (i == 3) obs_hysteresis = z;
    }
    
    file.close();
  }
  std::cout << "Tao: " << tao << std::endl;
  std::cout << "Alpha Prior: " << alpha << std::endl;
  std::cout << "Random Forward: " << rand_const_forward <<std::endl;  
  
  std::cout << "Positive Feedback: " << u_plus << std::endl;
  std::cout << "Credibility Thresdhold: " << p_c << std::endl;
  std::cout << "Close Distance: " << close_distance <<std::endl;
  // std::cout << "Random forward: " << rand_const_forward << std::endl;
  std::cout << "Random Turn: " << rand_const_turn << std::endl;
  std::cout << "Observation Hold: " << obs_hysteresis << std::endl;
  std::cout << "-----------------------------" << std::endl;
}