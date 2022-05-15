// File:          bayes_bot_controller.cpp
// Date:
// Description:
// Author:
// Modifications:
#include <math.h>
#include <iostream>
#include <fstream>
#include <string>
#include <time.h>
#include <BetaCDF.hpp>
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

enum Side { LEFT, RIGHT };

static Supervisor *robot;
static Motor* motors[2]; //2
static DistanceSensor* distance_sensors[4]; //2
static PositionSensor* encoders[2]; 

//DEFAULT Algorithm parameters -> read in algorithm parameters from file / Part of the world file. 
static double alpha = 0;
static double beta = 0;
static int d_f = -1; 
static int tao = 10;
static double p_c = 0.5; //Credibility Threshold 
static bool u_plus = false; //Positive feedback 
static double comDist = 0.3;
static double qSize = 8;
static double close_distance = 50.0;

static int C = 0; //Observed Color
static int nRobot = 4;
static const std::string rovDef[4] = {"rov_0", "rov_1", "rov_2", "rov_3"};
static Node* rovNode[4];
static Field* rovData[4];
static Node* me;
static Field* myDataField;

//Robot parameters
static std::string name;
static double speed = 5.0;
static int rand_const_forward = 250; 
static int rand_const_turn = 100;
static double p;
static int direction = LEFT;
static bool r_walk = true;
static int forward_count;
static int turn_count;
static int collision_count;
static int control_count = 0;
static std::queue<int> commHistory;
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

#define STOP 1.0e-8
#define TINY 1.0e-30

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
  std::string color = robot->getCustomData();
  int iColor = color[0] - '0';
  return iColor;
}

static int checkQ(int who) {
  if (commHistory.empty()) {
    return 1;
  }
  if (commHistory.size() < qSize) {
     if (commHistory.front() == who) {
       commHistory.push(who);
       return 0;
     } else {
       commHistory.push(who);
       return 1;
     }
  } else {
     if (commHistory.front() == who) {
       commHistory.pop();
       commHistory.push(who);
       return 0;
     } else {
       commHistory.pop();
       commHistory.push(who);
       return 1;
     }
  }
}

static void getMessage() { 
  Node* me = robot->getSelf();
  Field *myDataField = me->getField("customData");
  std::string myData = myDataField->getSFString();
  if (checkQ(myData[1] - '0')) {
    int cPrime = myData[2] - '0';
    std::string newMessage = myData.substr(0,3);
    //std::cout << "Get Message: " << newMessage <<std::endl;
    myDataField->setSFString(newMessage);
    alpha = alpha + cPrime;
    beta = beta + (1 - cPrime);
  }
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
    if ((dist < comDist) && (dist != 0.0)) {
       //std::cout << "FOUND with distance: " << dist << std::endl;
       Field *otherDataField = rovNode[i]->getField("customData");
       std::string otherData = otherDataField->getSFString();

       std::string myData = myDataField->getSFString();
       
       std::string outbound;
       
       std::string otherColor = otherData.substr(0,1);
       std::string myID = name.substr(1,1);
       
       std::string cProb = otherData.substr(3,8);
       
       if (d_f != -1 && u_plus) { //CHECK CONVERSIONS
         outbound = otherColor + myID + std::to_string(d_f) + cProb;
       } else {
         outbound = otherColor+ myID + std::to_string(C) + cProb;
       }
       otherDataField->setSFString(outbound);
    }
  }
}

static void do_random_walk() {
  //std::cout << collision_count << " " << forward_count << " " << turn_count << std::endl;
  double distance_sensors_values[4];
  for (int i = 0; i < 4; i++){
    distance_sensors_values[i] = distance_sensors[i]->getValue();
  }
  
  // INCLUDE CODE FOR MORE DSENSORS
  if (distance_sensors_values[LEFT] < close_distance || distance_sensors_values[RIGHT] < close_distance || 
  distance_sensors_values[2] < close_distance || distance_sensors_values[3] < close_distance) {
    //std::cout << name << " Collision Avoidance" << std::endl;
    direction = distance_sensors_values[LEFT] < distance_sensors_values[RIGHT] ? RIGHT : LEFT;
    if ((std::abs(distance_sensors_values[LEFT] - distance_sensors_values[RIGHT]) < 0.35) || 
    (std::abs(distance_sensors_values[2] - distance_sensors_values[3]) < 0.35)) {
      direction = -1;
    } else if (distance_sensors_values[2] < distance_sensors_values[3]) {
      direction = RIGHT;
    } else if (distance_sensors_values[3] < distance_sensors_values[2]) {
      direction = LEFT;
    }
    if (collision_count == 0) {
      collision_count = 200;
    }
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
  }
  if (collision_count > 0) {
    collision_count = collision_count - 1;
    return;
  } else {
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
        r_walk = false;
        double dir = rand() / (float) RAND_MAX;
        if (dir > 0.5) {
          //std::cout << "RIGHT" << std::endl;
          direction = RIGHT;
        } else {
          //std::cout << "LEFT" << std::endl;
          direction = LEFT;
        } 
    }
  }
}


// P > 0.5 ==> MOSTLY BLACK
int main(int argc, char *argv[]) {
  // create the Robot instance.
  robot = new Supervisor();
  
  // get the time step of the current world.
  int timeStep = (int)robot->getBasicTimeStep();
    
  name = robot->getName();
  char seed = *argv[1];
  
  int finalSeed = seed - '0';
  int indiSeed = name[1] - '0';
  finalSeed = finalSeed + indiSeed;
  std::cout << "Robot Seed: " << finalSeed << std::endl;
  
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
  
  //Set up algorithm parameters from commmand line args


  //Main while loop
  while (robot->step(timeStep) != -1) {
    if (r_walk) {
      do_random_walk();
    } else {
      if ((control_count % tao) == 0) {
          C = getColor();
          alpha = alpha + C;
          beta = beta + (1 - C);
        }
        // RECEIVE MESSAGE
        getMessage(); 
        p = incbeta(alpha, beta, 0.5);
        std::cout << name << " Current CDF: " << p << " with ALPHA: " << alpha << " and BETA: "<< beta <<std::endl;
        std::string currentData = myDataField->getSFString();
        myDataField->setSFString(currentData + std::to_string(p));
        if ((d_f == -1) & u_plus) {
          if (p > p_c) {
            d_f = 0;
          } else if ((1 - p) > p_c) {
            d_f = 1;
          } 
        }
        putMessage();
        r_walk = true;
        control_count = control_count + 1; //NOTE: This means that the control_count is updated every "TIME_STEP" ticks in the world. 
    }
    //std::cout << name << " " << robot->getTime() << std::endl;
  }
  
  delete robot;
  //probData.close();
  return 0;
}