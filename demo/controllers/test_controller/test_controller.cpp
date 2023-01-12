// File:          bayes_bot_controller.cpp
// Date:
// Description:
// Author:
// Modifications:
#include <math.h>
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
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

enum Side { LEFT, RIGHT };

static Supervisor *robot;
static Motor* motors[2]; //2
static DistanceSensor* distance_sensors[4]; //2
static PositionSensor* encoders[2]; 

//DEFAULT Algorithm parameters -> read in algorithm parameters from file / Part of the world file. 
static double alpha = 0;
static double beta = 0;
static int d_f = -1; 
static int tao = 1;
static double p_c = 0.5; //Credibility Threshold 
static bool u_plus = false; //Positive feedback 
static double comDist = 1;
static double qSize = 2;
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


// static void do_random_walk() {
  // //std::cout << collision_count << " " << forward_count << " " << turn_count << std::endl;
  // double distance_sensors_values[4];
  // for (int i = 0; i < 4; i++){
    // distance_sensors_values[i] = distance_sensors[i]->getValue();
  // }
  
  //INCLUDE CODE FOR MORE DSENSORS
  // if (distance_sensors_values[LEFT] < close_distance || distance_sensors_values[RIGHT] < close_distance || 
  // distance_sensors_values[2] < close_distance || distance_sensors_values[3] < close_distance) {
    // //std::cout << name << " Collision Avoidance" << std::endl;
    // direction = distance_sensors_values[LEFT] < distance_sensors_values[RIGHT] ? RIGHT : LEFT;
    // if ((std::abs(distance_sensors_values[LEFT] - distance_sensors_values[RIGHT]) < 0.35) || 
    // (std::abs(distance_sensors_values[2] - distance_sensors_values[3]) < 0.35)) {
      // direction = -1;
    // } else if (distance_sensors_values[2] < distance_sensors_values[3]) {
      // direction = RIGHT;
    // } else if (distance_sensors_values[3] < distance_sensors_values[2]) {
      // direction = LEFT;
    // }
    // if (collision_count == 0) {
      // collision_count = 200;
    // }
    // if (direction == LEFT) {
      //set the speed to turn to the left
      // motors[LEFT]->setVelocity(-speed);
      // motors[RIGHT]->setVelocity(speed);
    // } else if (direction == RIGHT ){
      //set the speed to turn to the right
      // motors[LEFT]->setVelocity(speed);
      // motors[RIGHT]->setVelocity(-speed);
    // } else if (direction == -1){
      //set the speed to go backwards
      // motors[LEFT]->setVelocity(-speed);
      // motors[RIGHT]->setVelocity(-speed);
    // } 
  // }
  // if (collision_count > 0) {
    // collision_count = collision_count - 1;
    // return;
  // } else {
    // if (forward_count > 0) {
      // motors[LEFT]->setVelocity(speed);
      // motors[RIGHT]->setVelocity(speed);
      // forward_count = forward_count - 1;
    // } else if ((forward_count == 0) && (turn_count > 0)) {
      // turn_count = turn_count - 1;
      // if (direction == LEFT) {
        //set the speed to turn to the left
        // motors[LEFT]->setVelocity(-speed);
        // motors[RIGHT]->setVelocity(speed);
      // } else {
        //set the speed to turn to the right
        // motors[LEFT]->setVelocity(speed);
        // motors[RIGHT]->setVelocity(-speed);
      // }
    // } else if((forward_count == 0) & (turn_count == 0)) {
        // //Once done turning check distance sensors to pick turn direction.
        // forward_count = rand() % rand_const_forward;
        // turn_count = rand() % rand_const_turn;
        // r_walk = false;
        // double dir = rand() / (float) RAND_MAX;


// P > 0.5 ==> MOSTLY BLACK
int main(int argc, char *argv[]) {
  // create the Robot instance.
  robot = new Supervisor();
  
  // get the time step of the current world.
  int timeStep = (int)robot->getBasicTimeStep();

  
  const char *motors_names[2] = {"left motor", "right motor"};
  const char *distance_sensors_names[4] = {"left distance sensor", "right distance sensor", "angle left distance sensor", "angle right distance sensor"};
  const char *encoder_names[2] = {"left encoder", "right encoder"};
  
  // create the magnetic force 
  Motor* electromagnet = robot->getMotor("electromagnet");
  electromagnet->setPosition(INFINITY);
  electromagnet->setVelocity(1);
  

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
  // for (int i = 0; i < nRobot; i++) {
    // rovNode[i] = robot->getFromDef(rovDef[i]);
    // rovData[i] = rovNode[i]->getField("customData");
  // }
  
  me = robot->getSelf();
  myDataField = me->getField("customData");
  
  // forward_count = rand() % rand_const_forward;
  // turn_count = rand() % rand_const_turn;
  
  //Set up algorithm parameters from commmand line args


  //Main while loop
  while (robot->step(timeStep) != -1) {
    std::cout << *(me->getVelocity()) << std::endl;
    motors[LEFT]->setVelocity(speed);
    motors[RIGHT]->setVelocity(speed);
  }
  
  delete robot;
  //probData.close();
  return 0;
}