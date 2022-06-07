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
#include <webots/Keyboard.hpp>
#include <webots/PositionSensor.hpp>
#include <webots/Supervisor.hpp>
#include <queue>
#include <vector>
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
static int nRobot = 4;
static const std::string rovDef[4] = {"rov_0", "rov_1", "rov_2", "rov_3"}; 

//DEFAULT Algorithm parameters -> read in algorithm parameters from file / Part of the world file. 
static int nParam = 5;
static double alpha = 0;
static double beta = 0;
static int d_f = -1; 
static int tao = 200;
static double p_c = 0.5; //Credibility Threshold 
static bool u_plus = false; //Positive feedback 
static double comDist = 1;
static double close_distance = 30.0;
static int C = 0; //Observed Color

//Robot Parameters
static int robotNum;
static int msg_count = 0;
static int FSM_STATE = 0;
static std::string name;
static double speed = 5.0;
static int rand_const_forward = 250; //Range for random value to go forward
static int rand_const_turn = 100; //Range for random value to turn
static int pause_time = 25;
static double p;
static char out;
static int direction = LEFT;
static int forward_count;
static int pause_count;
static int turn_count;
static int control_count = 0;

//Arena Parameters
int boxSize = 4;
int imageDim = 128;
int rowCount = 564; // THIS MUST BE CHANGED EVERYTIME A NEW ARENA IS CREATED
int grid[564][2]; 

//Function declarations
double incbeta(double a, double b, double x);
double getEuclidean(double meX, double meY, double otherX, double otherY);
static int getColor(void);
static void getMessage(void);
static void putMessage(void);
static void readArena(void);
static void readParameters(void);

int main(int argc, char **argv) {
  // create the Robot instance.
  robot = new Supervisor();
  
  // get the time step of the current world.
  int timeStep = (int)robot->getBasicTimeStep();
    
  name = robot->getName();
  char seed = *argv[1];
  
  int finalSeed = seed - '0';
  robotNum = name[1] - '0';
  finalSeed = finalSeed + robotNum;
  //std::cout << "Robot Seed: " << finalSeed << std::endl;
  
  srand(seed + name[1]); // Initialize seed based on the robot name.
  
  const char *motors_names[2] = {"left motor", "right motor"};
  const char *distance_sensors_names[4] = {"left distance sensor", "right distance sensor", "angle left distance sensor", "angle right distance sensor"};
  const char *encoder_names[2] = {"left encoder", "right encoder"};
  
  // create the magnetic force 
  Motor* electromagnet = robot->getMotor("electromagnet");
  electromagnet->setPosition(INFINITY);
  electromagnet->setVelocity(1);
  
  //Output data file for analysis
  std::ofstream probData;
  std::string fileName = name + "_data.csv";
  probData.open(fileName);
  
  //Device Tags
  for (int i = 0; i < 2; i++) {
    
    motors[i] = robot->getMotor(motors_names[i]);
    (motors[i])->setPosition(INFINITY); // For linear mode 

    encoders[i] = robot->getPositionSensor(encoder_names[i]);
    encoders[i]->enable(TIME_STEP);
  }
  
  for (int i = 0; i < 4; i++) {
    distance_sensors[i] = robot->getDistanceSensor(distance_sensors_names[i]);
    distance_sensors[i]->enable(TIME_STEP);
  }
  
  //Robot nodes
  for (int i = 0; i < nRobot; i++) {
    rovNode[i] = robot->getFromDef(rovDef[i]);
    rovData[i] = rovNode[i]->getField("customData");
  }
  
  me = robot->getSelf();
  myDataField = me->getField("customData");
  
  forward_count = rand() % rand_const_forward;
  turn_count = rand() % rand_const_turn;
  
  readArena();
  readParameters();
  
  C = getColor();

  //Main while loop
  while (robot->step(timeStep) != -1) { 
    // Start robots one after the other
      //std::cout << name << " start controller" << std::endl;
    std::cout <<  "Robot " << robotNum << "-> FSM State: " << FSM_STATE << " Belief: " << p << " with Alpha: " << alpha << " Beta: " << beta <<std::endl;
    //std::cout << alpha << " " << beta << std::endl;
    double distance_sensors_values[4];
    for (int i = 0; i < 4; i++){
      distance_sensors_values[i] = distance_sensors[i]->getValue();
    }
    //std::cout << "Robot: " << name << " in state: " << FSM_STATE << std::endl;

    //FSM 
    switch(FSM_STATE) {

      //RANDOM WALK STATE
      case FSM_RW:
      { 
        //std::cout << "RW" << std::endl;
        if (control_count % tao == 0) {
          pause_count = pause_time;
          FSM_STATE = FSM_PAUSE;
        } else if (distance_sensors_values[LEFT] < close_distance || distance_sensors_values[RIGHT] < close_distance || distance_sensors_values[2] < close_distance || distance_sensors_values[3] < close_distance) { 
          FSM_STATE = FSM_CA;
          break;
        }
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
            //Once done turning check distance sensors to pick turn direction.
            forward_count = rand() % rand_const_forward;
            turn_count = rand() % rand_const_turn;
            double dir = rand() / (float) RAND_MAX;
            if (dir > 0.5) {
              //std::cout << "RIGHT" << std::endl;
              direction = RIGHT;
            } else {
              //std::cout << "LEFT" << std::endl;
              direction = LEFT;
            } 
          }
        break;
      }

      //COLLISION AVOIDANCE STATE
      case FSM_CA:
      {
        
        if (control_count % tao == 0) {
          pause_count = pause_time;
          FSM_STATE = FSM_PAUSE;
        } else if (distance_sensors_values[LEFT] > 130 && distance_sensors_values[RIGHT] > 130 && distance_sensors_values[2] > 130 && distance_sensors_values[3] > 130) { 
          FSM_STATE = FSM_RW;
          break;
        }
        direction = distance_sensors_values[LEFT] < distance_sensors_values[RIGHT] ? RIGHT : LEFT;
        
        if ((distance_sensors_values[LEFT] < 150) && (distance_sensors_values[RIGHT] < 150) && (distance_sensors_values[2] < 150) && (distance_sensors_values[3] < 150)) {
          direction = -1;
        } else if (distance_sensors_values[2] < distance_sensors_values[3]) {   
          direction = RIGHT;
        } else if (distance_sensors_values[3] < distance_sensors_values[2]) {
          direction = LEFT;
        } 
        
        //std::cout << direction << std::endl;
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
        break;
      }
      
      case FSM_SEND:
      {
        // Update custom data one by one but wait until all robots finish to move to next state.
        //std::cout << msg_count << std::endl;
        if (msg_count == robotNum) {
          //std::cout << "FSM_SEND " << robotNum << std::endl;
          putMessage();
          FSM_STATE = FSM_SEND;
          msg_count = msg_count + 1;
        } else {
          // Move on to next robot to push msg.
          //std::cout << "FSM_SEND ELSE" << std::endl;
          msg_count = msg_count + 1;
          FSM_STATE = FSM_SEND;
        }
        
        //
        if (msg_count > (nRobot-1)) {
          //std::cout << "FSM_PULL" << std::endl;
          //std::cout << "TO PULL" << std::endl;
          msg_count = 0;
          FSM_STATE = FSM_PULL;
        }
        break;
      }
      
      case FSM_PULL:
      {
        getMessage();
        FSM_STATE = FSM_RW;
        std::string currentData = myDataField->getSFString();
        myDataField->setSFString(currentData.substr(0,4) + std::to_string(p));
        //std::cout << "Controller Read: " << currentData << std::endl;
        break;
      }
      
    }
    p = incbeta(alpha, beta, 0.5);
    //std::cout << name << " Current CDF: " << p << " with ALPHA: " << alpha << " and BETA: "<< beta <<std::endl;
    
    if ((d_f == -1) & u_plus) {
      if (p > p_c) {
        d_f = 0;
      } else if ((1 - p) > p_c) {
        d_f = 1;
      } 
    }
    
    control_count = control_count + 1;
    //std::cout << "Alpha: " << alpha << " Beta: " << beta << std::endl;
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
 *    appreciated but is nBE0ot required.
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

double getEuclidean(double meX, double meY, double otherX, double otherY) {
  return sqrt(pow(meX - otherX, 2) + pow(meY - otherY, 2));
}


static int getColor() {
  // std::string color = robot->getCustomData();
  // int iColor = color[0] - '0';
  // return iColor;
  Field *meField = me->getField("translation");
  const double *meV = meField->getSFVec3f();
  double xPos = meV[2];
  double yPos = meV[0];
  for (int i = 0; i < rowCount; i++) {
      if ((xPos >= 1.0 * grid[i][0]/imageDim) && 
      (xPos <= (1.0 * grid[i][0] + boxSize)/imageDim) && 
      (yPos >= 1.0 *grid[i][1]/imageDim) && 
      (yPos <= (1.0 *grid[i][1] + boxSize)/imageDim)) { 
          return 1; //Returns 1 if the current robot is on a white square
      }
  }
  //print(xPos, yPos)
  return 0;
}

// static int checkQ(int who) {
  // if (commHistory.empty()) {
    // return 1;
  // }
  // if (commHistory.size() < qSize) {
     // if (commHistory.front() == who) {
       // commHistory.push(who);
       // return 0;
     // } else {
       // commHistory.push(who);
       // return 1;
     // }
  // } else {
     // if (commHistory.front() == who) {
       // commHistory.pop();
       // commHistory.push(who);
       // return 0;
     // } else {
       // commHistory.pop();
       // commHistory.push(who);
       // return 1;
     // }
  // }
// }

static void getMessage() {
  int cPrime;
  Node* me = robot->getSelf();
  Field *myDataField = me->getField("customData");
  std::string myData = myDataField->getSFString();
  for (int i = 0; i < nRobot; i++) {
    if (i != robotNum) {
      cPrime = myData[i] - '0';
      //std::cout << cPrime << std::endl;
      alpha = alpha + cPrime;
      beta = beta + (1 - cPrime);
    }
  }
  //std::string newMessage = myData.substr(0,3);
  //std::cout << "Get Message: " << newMessage <<std::endl;
  // myDataField->setSFString(newMessage + myData.substr(3,8));
 
}


static void putMessage() { // color, id, df/C'
  Field *meField = me->getField("translation");
  const double *meV = meField->getSFVec3f();
  //Iterate through to find distance.
  for (int i = 0; i < nRobot; i++) {
    Field *otherField = rovNode[i]->getField("translation");
    const double *otherV = otherField->getSFVec3f();
    double dist = getEuclidean(meV[0], meV[2], otherV[0], otherV[1]);
    //std::cout << "Euclidean Distance: " << dist << std::endl;
    if ((dist < comDist) && (dist != 0.0) && (i != robotNum)) {
       //std::cout << "FOUND with distance: " << dist << std::endl;
       Field *otherDataField = rovNode[i]->getField("customData");
       std::string otherData = otherDataField->getSFString();
       //std::cout << "Other Data: " << otherData << std::endl;

       std::string myData = myDataField->getSFString();
       
       std::string outbound;
       std::string cProb = otherData.substr(4,8);
       
       if (d_f != -1 && u_plus) {
         out = d_f + '0';
         otherData[robotNum] = out;
         //outbound = ack + myID + std::to_string(d_f) + cProb;
       } else {
         out = '0' + C;
         //std::cout << "Output char: " << out << " With int: " << C <<  " at location: " << index << std::endl;
         otherData[robotNum] = out;
         //outbound = ack+ myID + std::to_string(C) + cProb;
         //std::cout << outbound << std::endl;
       }
       otherDataField->setSFString(otherData);
       //std::cout << robotNum << " Sent to: " << i << " Color:" << out << "with Data: " << otherData << std::endl;
    }
  }
}

static void readArena() {
  std::ifstream file("boxrect.csv");
  
  for (int i = 0; i < rowCount; i++) {
    std::string line;
    std::getline(file, line);
    
    std::stringstream iss(line);
    
    for (int j = 0; j < 2; j++) {
      std::string val;
      std::getline (iss, val, ',');
      std::stringstream converter(val);
      converter >> grid[i][j];
    }
  }
  
  file.close();
}

//Read in the parameters from prob.txt
static void readParameters() {
  char *pPath = getenv("WB_WORKING_DIR");
  //printf("The current path is: %s\n", pPath);
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
      if (i == 0) {
        if (z > 0.5) u_plus = true;
        else u_plus = false;
      }
      
      if (i == 1) p_c = z;
      if (i == 2) close_distance = z;
      if (i == 3) rand_const_forward = z;
      if (i == 4) rand_const_turn = z;
    }
    
    std::cout << "Positive Feedback: " << u_plus << std::endl;
    std::cout << "Credibility Thresdhold: " << p_c << std::endl;
    std::cout << "Close Distance: " << close_distance <<std::endl;
    std::cout << "Random forward: " << rand_const_forward << std::endl;
    std::cout << "Random Turn: " << rand_const_turn << std::endl;
    
    file.close();
  }
}