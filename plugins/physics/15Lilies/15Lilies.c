/*
 * File: lily_robot_physics.c
 * Date: 12 Oct 2015
 */

#include <math.h>
#include <stdlib.h>
#include <time.h>

#include <ode/ode.h>
#include <plugins/physics.h>

/* general */
#define N_ROBOTS 15
#define DEBUG 1

#define X 0
#define Y 1
#define Z 2

// GEOMETRY DEFINITION
#define LILY_SIZE_X 0.035

#define LILY_SIZE_Y 0.035
#define LILY_SIZE_Z 0.035
#define LILY_VOLUME (LILY_SIZE_X * LILY_SIZE_Y * LILY_SIZE_Z)
#define R_BALL 0.02
#define WATER_LEVEL 0.1
const double WATER_DENSITY = 1000.0; /* [kg/m³] */
const double GRAVITY = 9.81;         /* [m/s²] */

/* some arithmetics */
#define SIGN(x) ((x) < 0.0 ? -1.0 : 1.0)
#define SQ(x) ((x) * (x))
#define CYLINDER_VOLUME(r, h) (M_PI * SQ(r) * (h))

/* global variables */
static dBodyID lily_robots[N_ROBOTS];
static int physics_enabled =
    1; /* disable this plugin if geoms or bodies are not found, necessary to
          avoid Webots crashing */
static int i, j;

static pthread_mutex_t mutex;

/* Flow speed and drag */
#define SCALE 1
#define DIVISIONS 50
//#define K_FLOW 1
//#define K_flow_rand 1
#define ARENA_R 0.3
#define DRAG_POINTS 16
#define MIN_FLOW 0.000001
#define DRAG_COEF 1
//#define RAND_FORCE_AMPLITUDE 0*0.0001 // 5.5mN for lighter Lily modules, Lily
// robots are heavier #define RAND_FORCEx
//(SCALE*SCALE*SCALE*RAND_FORCE_AMPLITUDE)
#define VEL_FIELD_FILE_NAME                                                    \
  "flow_vel_23.txt" //"vel_field_total_100_-50.txt" //"flow_vel.txt" //
#define VEL_STD_FIELD_FILE_NAME "flow_vel_std_23.txt"
//#define Parameters "prob.txt"

static double VX[DIVISIONS][DIVISIONS];
static double VY[DIVISIONS][DIVISIONS];

static double VX_STD[DIVISIONS][DIVISIONS];
static double VY_STD[DIVISIONS][DIVISIONS];

double K_FLOW;
double K_flow_rand;
double RAND_FORCEx;
double RAND_FORCEy;
static char Parameters[256];

/* general ODE objects that will be provided by Webots */
static dWorldID world = NULL;
dSpaceID space = NULL;
dJointGroupID contact_joint_group = NULL;

/* Local Functions Declarations */
static dBodyID getBody(const char *def);
static void getFlowVelocity(const dReal *position, dReal *flow_vel);
// static void computeArchimedes(dReal elevation,dBodyID robot);
static void computeDrag(const dReal *position_vect, const dReal *lin_velocity,
                        dBodyID robot);
static void computeDrag_randn(const dReal *position_vect,
                              const dReal *lin_velocity, dBodyID robot);
static dReal calcCosAngle(dVector3 surf_norm, dVector3 field);
static void addRandomForce(dBodyID robot);
static double randn(double mean, double std);
static void getFlowVelocity_randn(const dReal *position, dReal *flow_vel);

static void addRandomForce_radial(dBodyID robot, const dReal *p);

/* Global Functions Definitions */

void webots_physics_step() {
  const dReal *lin_velocity, *position_vect, *position_vect2;

  // connect pieces that are close together to allow attachment
  if (dWebotsGetTime() / 1000.0 < 2.0) {
    for (i = 0; i < N_ROBOTS; i++) {
      position_vect = dBodyGetPosition(lily_robots[i]);
      for (j = 0; j < N_ROBOTS; j++) {
        if (j != i) {
          // dWebotsConsolePrintf("%f
          // %f\n",sqrt(SQ(position_vect2[0]-position_vect[0]) +
          // SQ(position_vect2[2]-position_vect[2])),sqrt(SQ(-0.005)+SQ(0.0175)));
          position_vect2 = dBodyGetPosition(lily_robots[j]);
          if (sqrt(SQ(position_vect2[0] - position_vect[0]) +
                   SQ(position_vect2[1] - position_vect[1])) < 0.05) {
            dBodySetLinearVel(lily_robots[i],
                              (position_vect2[0] - position_vect[0]),
                              (position_vect2[1] - position_vect[1]), 0);
            // dWebotsConsolePrintf("hallo\n");
          }
        }
      }
    }
  } else {
    for (i = 0; i < N_ROBOTS; i++) {
      lin_velocity = dBodyGetLinearVel(lily_robots[i]);
      position_vect = dBodyGetPosition(lily_robots[i]);
      // dWebotsConsolePrintf("lin_velocity of robot %d: %f, %f, %f \n", i,
      // lin_velocity[X], lin_velocity[Y],lin_velocity[Z]);
      /// compute and add Archimedes force ///
      // computeArchimedes(position_vect[Y],lily_robots[i]);

      dVector3 flow, v_rel;
      getFlowVelocity(position_vect, flow); // get flow velocity at the point
      v_rel[X] = (lin_velocity[X] - flow[X]) /
                 SCALE; // relative velocity of flow to robot
      v_rel[Y] = (lin_velocity[Y] - flow[Y]) / SCALE;
      v_rel[Z] = (lin_velocity[Z] - flow[Z]) / SCALE;

      // dWebotsConsolePrintf("flow_velocity: %f, %f, %f \n", flow[X], flow[Y],
      // flow[Z]); dWebotsConsolePrintf("rel_velocity: %f, %f, %f \n", v_rel[X],
      // v_rel[Y], v_rel[Z]);

      // dBodySetLinearVel  (lily_robots[i], v_rel[X], v_rel[Y], v_rel[Z]);
      // dBodySetLinearVel  (lily_robots[i], flow[X], flow[Y], flow[Z]);

      /// compute and add drag forces ///
      // computeDrag(position_vect,lin_velocity, lily_robots[i]);
      computeDrag_randn(position_vect, lin_velocity, lily_robots[i]);
      /// add random force ///
      // addRandomForce_radial(lily_robots[i],position_vect);
      addRandomForce(lily_robots[i]);
    }
  }
}

void webots_physics_init(dWorldID world_, dSpaceID space_,
                         dJointGroupID contactJointGroup_) {

  pthread_mutex_init(&mutex,
                     NULL); // needed to run with multi-threaded version of ODE

  int n, m;
  FILE *fid;
  FILE *fid2;
  FILE *fid3;
  /* stores Webots supplied objects */
  world = world_;
  space = space_;
  contact_joint_group = contactJointGroup_;

  srand(time(NULL));

  for (i = 0; i < N_ROBOTS; ++i) {
    char robot_name[128];
    sprintf(robot_name, "LILY%d", i); // robot DEF should start from LILY0
    lily_robots[i] = getBody(robot_name);
    addRandomForce(lily_robots[i]);
  }
  /* Initialize velocity field */
  fid = fopen(VEL_FIELD_FILE_NAME, "r");
  // dWebotsConsolePrintf("FID: %d\n",fid);
  for (m = 0; m < DIVISIONS; m++) {
    for (n = 0; n < DIVISIONS; n++) {
      fscanf(fid, "%lf,", &(VY[n][m]));
      VY[n][m] = -VY[n][m];
      // dWebotsConsolePrintf("Flow fieldX[%d][%d]: %f\n",m,n,VY[n][m]);
    }
  }
  for (m = 0; m < DIVISIONS; m++) {
    for (n = 0; n < DIVISIONS; n++) {
      fscanf(fid, "%lf,", &(VX[n][m]));
      VX[n][m] = -VX[n][m];
      // dWebotsConsolePrintf("Flow fieldZ[%d][%d]: %f\n",m,n,VZ[n][m]);
    }
  }
  fclose(fid);

  /* Initialize velocity field */
  fid2 = fopen(VEL_STD_FIELD_FILE_NAME, "r");
  // dWebotsConsolePrintf("FID: %d\n",fid);
  for (m = 0; m < DIVISIONS; m++) {
    for (n = 0; n < DIVISIONS; n++) {
      fscanf(fid2, "%lf,", &(VY_STD[n][m]));
      // dWebotsConsolePrintf("Flow fieldX[%d][%d]: %f\n",m,n,VX[n][m]);
    }
  }
  for (m = 0; m < DIVISIONS; m++) {
    for (n = 0; n < DIVISIONS; n++) {
      fscanf(fid2, "%lf,", &(VX_STD[n][m]));
      // dWebotsConsolePrintf("Flow fieldZ[%d][%d]: %f\n",m,n,VZ[n][m]);
    }
  }
  fclose(fid2);
  char *pPath;
  pPath = getenv("WB_WORKING_DIR");
  if (pPath != NULL)
  // if (0)
  {
    printf("The current path is: %s\n", pPath);
    sprintf(Parameters, "%s/prob.txt", pPath);
  } else {
    strcpy(Parameters, "./prob.txt");
  }
  // printf("%s\n", Parameters);
  fid3 = fopen(Parameters, "r");
  fscanf(fid3, "%lf,", &K_FLOW);
  fscanf(fid3, "%lf,", &K_flow_rand);
  fscanf(fid3, "%lf,", &RAND_FORCEx);
  // fscanf(fid3,"%lf,",&RAND_FORCEy);
  RAND_FORCEx = RAND_FORCEx * 0.0001;
  RAND_FORCEy = RAND_FORCEx * 0.0001; /**/
  fclose(fid3);
}

/* Local Functions Definitions */

static dBodyID getBody(const char *def) {
  dBodyID body = dWebotsGetBodyFromDEF(def);
  if (!body) {
    dWebotsConsolePrintf("Warning: robot %s not found", def);
    dWebotsConsolePrintf("Physics plugin will be disabled ...");
    physics_enabled = 0;
  }
#ifdef DEBUG
  else {
    dWebotsConsolePrintf("Robot %s successfully found!", def);
  }
#endif
  return body;
}

static void getFlowVelocity(const dReal *position, dReal *flow_vel) {
  int x_index, y_index;

  x_index =
      DIVISIONS - (int)((double)DIVISIONS * (position[X] / SCALE + ARENA_R) /
                        (2.0 * ARENA_R));
  y_index =
      DIVISIONS - (int)((double)DIVISIONS * (position[Y] / SCALE + ARENA_R) /
                        (2.0 * ARENA_R));
  // dWebotsConsolePrintf("Indexes:[%d][%d]\n",x_index,y_index);
  if (x_index < 0 || x_index > (DIVISIONS - 1) || y_index < 0 ||
      y_index > (DIVISIONS - 1)) {
    flow_vel[X] = 0.0;
    flow_vel[Y] = 0.0;
  } else {
    flow_vel[X] = K_FLOW * VX[y_index][x_index];
    flow_vel[Y] = K_FLOW * VY[y_index][x_index];
  }
  flow_vel[Z] = 0.0;
  // dWebotsConsolePrintf("Flow speed: %f %f
  // %f\n",flow_vel[X],flow_vel[Y],flow_vel[Z]);
}
static void getFlowVelocity_randn(const dReal *position, dReal *flow_vel) {
  int x_index, y_index;

  x_index =
      DIVISIONS - (int)((double)DIVISIONS * (position[X] / SCALE + ARENA_R) /
                        (2.0 * ARENA_R));
  y_index =
      DIVISIONS - (int)((double)DIVISIONS * (position[Y] / SCALE + ARENA_R) /
                        (2.0 * ARENA_R));
  // dWebotsConsolePrintf("Indexes:[%d][%d]\n",x_index,z_index);
  if (x_index < 0 || x_index > (DIVISIONS - 1) || y_index < 0 ||
      y_index > (DIVISIONS - 1)) {
    flow_vel[X] = 0.0;
    flow_vel[Y] = 0.0;
    dWebotsConsolePrintf("Flow speed: %f %f %f\n", flow_vel[X], flow_vel[Y],
                         flow_vel[Z]);
  } else {
    flow_vel[X] =
        K_FLOW * randn(VX[y_index][x_index], VX_STD[y_index][x_index]);
    flow_vel[Y] =
        K_FLOW * randn(VY[y_index][x_index], VY_STD[y_index][x_index]);
  }
  flow_vel[Z] = 0.0;
  // dWebotsConsolePrintf("Flow speed: %f %f
  // %f\n",flow_vel[X],flow_vel[Y],flow_vel[Z]);
}

static void computeDrag(const dReal *position_vect, const dReal *lin_velocity,
                        dBodyID robot) {
  int i, side;
  dVector3 p, p_world, flow, surf_normal, v_rel, v_point, f_drag;
  dReal face_area, drag_abs, v_abs_sq, cos_angle;

  // drag on bottom face added to center of mass
  f_drag[Z] = -SIGN(lin_velocity[Z]) * 0.5 * WATER_DENSITY * LILY_SIZE_X *
              LILY_SIZE_Y * SQ(lin_velocity[Z] / SCALE);
  dBodyAddForce(robot, 0, 0, f_drag[Z] * SCALE * SCALE);

  // drag on side faces
  for (side = 0; side < 4; side++) {
    for (i = 0; i < DRAG_POINTS; i++) {
      switch (side) {
      case 0:
        p[X] = LILY_SIZE_X / 2.0;
        p[Y] = LILY_SIZE_Y / 2.0 - LILY_SIZE_Y / 2.0 / (double)DRAG_POINTS -
               (double)i * LILY_SIZE_Y / (double)DRAG_POINTS;
        p[Z] = LILY_SIZE_Z / 2.0;
        surf_normal[X] = -1.0;
        surf_normal[Y] = 0.0;
        surf_normal[Z] = 0.0;
        face_area = LILY_SIZE_X * LILY_SIZE_Z / DRAG_POINTS;
        break;
      case 1:
        p[X] = LILY_SIZE_X / 2.0 - LILY_SIZE_X / 2.0 / (double)DRAG_POINTS -
               (double)i * LILY_SIZE_X / (double)DRAG_POINTS;
        p[Y] = LILY_SIZE_Y / 2.0;
        p[Z] = LILY_SIZE_Z / 2.0;
        surf_normal[X] = 0.0;
        surf_normal[Y] = -1.0;
        surf_normal[Z] = 0.0;
        face_area = LILY_SIZE_Y * LILY_SIZE_Z / DRAG_POINTS;
        break;
      case 2:
        p[X] = -LILY_SIZE_X / 2.0;
        p[Y] = LILY_SIZE_Y / 2.0 - LILY_SIZE_Y / 2.0 / (double)DRAG_POINTS -
               (double)i * LILY_SIZE_Y / (double)DRAG_POINTS;
        p[Z] = LILY_SIZE_Z / 2.0;
        surf_normal[X] = 1.0;
        surf_normal[Y] = 0.0;
        surf_normal[Z] = 0.0;
        face_area = LILY_SIZE_X * LILY_SIZE_Z / DRAG_POINTS;
        break;
      case 3:
        p[X] = LILY_SIZE_X / 2.0 - LILY_SIZE_X / 2.0 / (double)DRAG_POINTS -
               (double)i * LILY_SIZE_X / (double)DRAG_POINTS;
        p[Y] = -LILY_SIZE_Y / 2.0;
        p[Z] = LILY_SIZE_Z / 2.0;
        surf_normal[X] = 0.0;
        surf_normal[Y] = 1.0;
        surf_normal[Z] = 0.0;
        face_area = LILY_SIZE_Y * LILY_SIZE_Z / DRAG_POINTS;
        break;
      default:
        dWebotsConsolePrintf("Fatal error calculating drag");
        break;
      }
      dBodyGetRelPointPos(robot, p[X] * SCALE, p[Y] * SCALE, p[Z] * SCALE,
                          p_world); // get point in world coordinates
      dBodyGetPointVel(robot, p_world[X], p_world[Y], p_world[Z],
                       v_point); // get point velocity
      // dWebotsConsolePrintf("getFlowVelocity called in next line");
      getFlowVelocity(p_world, flow); // get flow velocity at the point
      v_rel[X] =
          flow[X] - v_point[X] / SCALE; // relative velocity of flow to robot
      v_rel[Y] = flow[Y] - v_point[Y] / SCALE;
      v_rel[Z] = flow[Z] - v_point[Z] / SCALE;
      v_abs_sq = SQ(v_rel[X]) + SQ(v_rel[Y]) +
                 SQ(v_rel[Z]);       // relative velocity absolute value squared
      if (sqrt(v_abs_sq) < MIN_FLOW) // if flow is zero no drag calc is required
        return;
      dBodyVectorToWorld(
          robot, surf_normal[X], surf_normal[Y], surf_normal[Z],
          surf_normal); // rotate surface_normal to world coord system
      cos_angle =
          calcCosAngle(surf_normal, v_rel); // angle between flow and surface
      drag_abs = 0.5 * DRAG_COEF * WATER_DENSITY * v_abs_sq * face_area *
                 cos_angle; // absolute value of the drag force (except for the
                            // cosine which reflects the orientation)
      // int forceScale = SCALE*100;
      int forceScale = SCALE * 1;
      f_drag[X] = K_flow_rand * forceScale * drag_abs * v_rel[X] /
                  sqrt(v_abs_sq); // drag force acts in a direction opposite to
                                  // oncoming flow velocity
      f_drag[Y] =
          K_flow_rand * forceScale * drag_abs * v_rel[Y] / sqrt(v_abs_sq);
      f_drag[Z] =
          K_flow_rand * forceScale * drag_abs * v_rel[Z] / sqrt(v_abs_sq);
      // f_drag[Z]= SCALE*SCALE*SCALE*SCALE* drag_abs*v_rel[Z]/sqrt(v_abs_sq);
      dBodyAddForceAtPos(robot, f_drag[X], f_drag[Y], f_drag[Z], p_world[X],
                         p_world[Y], p_world[Z]);
      // dWebotsConsolePrintf("Drag: %f %f %f",f_drag[X],f_drag[Y],f_drag[Z]);
      // dWebotsConsolePrintf("Flow speed: %f %f %f\n",flow[X],flow[Y],flow[Z]);
      // dWebotsConsolePrintf("lin_vel: %f %f
      // %f",lin_velocity[X],lin_velocity[Y],lin_velocity[Z]);
      // dWebotsConsolePrintf("Cos_angle: %f",cos_angle);
      // dWebotsConsolePrintf("Normal: %f %f
      // %f",surf_normal[X],surf_normal[Y],surf_normal[Z]);
      // dWebotsConsolePrintf("Vrel: %f %f %f",v_rel[X],v_rel[Y],v_rel[Z]);
      // dWebotsConsolePrintf("p_world: %f %f
      // %f",p_world[X],p_world[Y],p_world[Z]); dWebotsConsolePrintf("p_rel: %f
      // %f %f",p[X],p[Y],p[Z]);
    }
  }
  // dWebotsConsolePrintf("lin_vel: %f %f
  // %f",lin_velocity[X],lin_velocity[Y],lin_velocity[Z]);
}

static void computeDrag_randn(const dReal *position_vect,
                              const dReal *lin_velocity, dBodyID robot) {
  int i, side;
  dVector3 p, p_world, flow, surf_normal, v_rel, v_point, f_drag;
  dReal face_area, drag_abs, v_abs_sq, cos_angle;

  // drag on bottom face added to center of mass
  f_drag[Z] = -SIGN(lin_velocity[Z]) * 0.5 * WATER_DENSITY * LILY_SIZE_X *
              LILY_SIZE_Y * SQ(lin_velocity[Z] / SCALE);
  dBodyAddForce(robot, 0, 0, f_drag[Z] * SCALE * SCALE);

  // drag on side faces
  for (side = 0; side < 4; side++) {
    for (i = 0; i < DRAG_POINTS; i++) {
      switch (side) {
      case 0:
        p[X] = LILY_SIZE_X / 2.0;
        p[Y] = LILY_SIZE_Y / 2.0 - LILY_SIZE_Y / 2.0 / (double)DRAG_POINTS -
               (double)i * LILY_SIZE_Y / (double)DRAG_POINTS;
        p[Z] = LILY_SIZE_Z / 2.0;
        surf_normal[X] = -1.0;
        surf_normal[Y] = 0.0;
        surf_normal[Z] = 0.0;
        face_area = LILY_SIZE_X * LILY_SIZE_Z / DRAG_POINTS;
        break;
      case 1:
        p[X] = LILY_SIZE_X / 2.0 - LILY_SIZE_X / 2.0 / (double)DRAG_POINTS -
               (double)i * LILY_SIZE_X / (double)DRAG_POINTS;
        p[Y] = LILY_SIZE_Y / 2.0;
        p[Z] = LILY_SIZE_Z / 2.0;
        surf_normal[X] = 0.0;
        surf_normal[Y] = -1.0;
        surf_normal[Z] = 0.0;
        face_area = LILY_SIZE_Y * LILY_SIZE_Z / DRAG_POINTS;
        break;
      case 2:
        p[X] = -LILY_SIZE_X / 2.0;
        p[Y] = LILY_SIZE_Y / 2.0 - LILY_SIZE_Y / 2.0 / (double)DRAG_POINTS -
               (double)i * LILY_SIZE_Y / (double)DRAG_POINTS;
        p[Z] = LILY_SIZE_Z / 2.0;
        surf_normal[X] = 1.0;
        surf_normal[Y] = 0.0;
        surf_normal[Z] = 0.0;
        face_area = LILY_SIZE_X * LILY_SIZE_Z / DRAG_POINTS;
        break;
      case 3:
        p[X] = LILY_SIZE_X / 2.0 - LILY_SIZE_X / 2.0 / (double)DRAG_POINTS -
               (double)i * LILY_SIZE_X / (double)DRAG_POINTS;
        p[Y] = -LILY_SIZE_Y / 2.0;
        p[Z] = LILY_SIZE_Z / 2.0;
        surf_normal[X] = 0.0;
        surf_normal[Y] = 1.0;
        surf_normal[Z] = 0.0;
        face_area = LILY_SIZE_Y * LILY_SIZE_Z / DRAG_POINTS;
        break;
      default:
        dWebotsConsolePrintf("Fatal error calculating drag");
        break;
      }
      dBodyGetRelPointPos(robot, p[X] * SCALE, p[Y] * SCALE, p[Z] * SCALE,
                          p_world); // get point in world coordinates
      dBodyGetPointVel(robot, p_world[X], p_world[Y], p_world[Z],
                       v_point); // get point velocity
      // dWebotsConsolePrintf("world coordinates %f %f
      // %f\n",p_world[X],p_world[Y],p_world[Z]);
      // dWebotsConsolePrintf("getFlowVelocity called in next line");
      getFlowVelocity_randn(p_world, flow); // get flow velocity at the point
      v_rel[X] =
          flow[X] - v_point[X] / SCALE; // relative velocity of flow to robot
      v_rel[Y] = flow[Y] - v_point[Y] / SCALE;
      v_rel[Z] = flow[Z] - v_point[Z] / SCALE;
      v_abs_sq = SQ(v_rel[X]) + SQ(v_rel[Y]) +
                 SQ(v_rel[Z]);       // relative velocity absolute value squared
      if (sqrt(v_abs_sq) < MIN_FLOW) // if flow is zero no drag calc is required
        return;
      dBodyVectorToWorld(
          robot, surf_normal[X], surf_normal[Y], surf_normal[Z],
          surf_normal); // rotate surface_normal to world coord system
      cos_angle =
          calcCosAngle(surf_normal, v_rel); // angle between flow and surface
      drag_abs = 0.5 * DRAG_COEF * WATER_DENSITY * v_abs_sq * face_area *
                 cos_angle; // absolute value of the drag force (except for the
                            // cosine which reflects the orientation)
      // int forceScale = SCALE*100;
      int forceScale = SCALE * 1;
      f_drag[X] = K_flow_rand * forceScale * drag_abs * v_rel[X] /
                  sqrt(v_abs_sq); // drag force acts in a direction opposite to
                                  // oncoming flow velocity
      f_drag[Y] =
          K_flow_rand * forceScale * drag_abs * v_rel[Y] / sqrt(v_abs_sq);
      f_drag[Z] =
          K_flow_rand * forceScale * drag_abs * v_rel[Z] / sqrt(v_abs_sq);
      // f_drag[Z]= SCALE*SCALE*SCALE*SCALE* drag_abs*v_rel[Z]/sqrt(v_abs_sq);
      dBodyAddForceAtPos(robot, f_drag[X], f_drag[Y], f_drag[Z], p_world[X],
                         p_world[Y], p_world[Z]);
      // dWebotsConsolePrintf("Drag: %f %f %f",f_drag[X],f_drag[Y],f_drag[Z]);
      // dWebotsConsolePrintf("Flow speed: %f %f %f\n",flow[X],flow[Y],flow[Z]);
      // dWebotsConsolePrintf("lin_vel: %f %f
      // %f",lin_velocity[X],lin_velocity[Y],lin_velocity[Z]);
      // dWebotsConsolePrintf("Cos_angle: %f",cos_angle);
      // dWebotsConsolePrintf("Normal: %f %f
      // %f",surf_normal[X],surf_normal[Y],surf_normal[Z]);
      // dWebotsConsolePrintf("Vrel: %f %f %f",v_rel[X],v_rel[Y],v_rel[Z]);
      // dWebotsConsolePrintf("p_world: %f %f
      // %f",p_world[X],p_world[Y],p_world[Z]); dWebotsConsolePrintf("p_rel: %f
      // %f %f",p[X],p[Y],p[Z]);
    }
  }
  // dWebotsConsolePrintf("lin_vel: %f %f
  // %f",lin_velocity[X],lin_velocity[Y],lin_velocity[Z]);
}

static dReal calcCosAngle(dVector3 surf_norm, dVector3 field) {
  dReal dot, abs;
  dot = surf_norm[X] * field[X] + surf_norm[Y] * field[Y] +
        surf_norm[Z] * field[Z];
  if (dot < 0.0)
    dot = 0.0; // only take into account flow going into the faces of the cube,
               // not going out from them
  abs = sqrt(SQ(field[X]) + SQ(field[Y]) + SQ(field[Z]));
  return dot / abs;
}

static void addRandomForce(dBodyID robot) {
  double rnd_f_x, rnd_f_y;
  rnd_f_x = randn(0, RAND_FORCEx);
  rnd_f_y = randn(0, RAND_FORCEy);
  dBodyAddForce(robot, rnd_f_x, rnd_f_y, 0.0);
  // dWebotsConsolePrintf("rnd_f = (%f;%f)", rnd_f_x,rnd_f_z);
}
/// Radial random force

static void addRandomForce_radial(dBodyID robot, const dReal *p) {
  double rnd_f;
  // rnd_f = fabs(randn(0,RAND_FORCE));
  rnd_f = randn(0, RAND_FORCEx);
  dBodyAddForce(robot, -rnd_f * p[X] / sqrt(SQ(p[X]) + SQ(p[Y]) + SQ(p[Z])),
                -rnd_f * p[Y] / sqrt(SQ(p[X]) + SQ(p[Y]) + SQ(p[Z])), 0.0);

  // dWebotsConsolePrintf("rnd_f = (%f)", rnd_f);
}

/* Gaussian random number generator using the Marsaglia polar method */
static double randn(double mean, double std) {
  double u1, u2, s;
  double x;

  do {
    u1 = 2.0 * ((double)rand() / (double)RAND_MAX - 0.5); // u1=U[-1,1]
    u2 = 2.0 * ((double)rand() / (double)RAND_MAX - 0.5); // u2=U[-1,1]
    s = u1 * u1 + u2 * u2;
  } while (s >= 1);

  x = sqrt(-2 * log(s) / s) * u1;

  return mean + std * x;
}

int webots_physics_collide(dGeomID g1, dGeomID g2) {
  /*
   * This function needs to be implemented if you want to overide Webots
   * collision detection. It must return 1 if the collision was handled and 0
   * otherwise. Note that contact joints should be added to the
   * contactJointGroup, e.g. n = dCollide(g1, g2, MAX_CONTACTS,
   * &contact[0].geom, sizeof(dContact));
   *   ...
   *   dJointCreateContact(world, contactJointGroup, &contact[i])
   *   dJointAttach(contactJoint, body1, body2);
   *   ...
   */
  return 0;
}

void webots_physics_cleanup() {
  pthread_mutex_destroy(&mutex);
  /*
   * Here you need to free any memory you allocated in above, close files, etc.
   * You do not need to free any ODE object, they will be freed by Webots.
   */
}
