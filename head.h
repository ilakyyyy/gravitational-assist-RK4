#ifndef HEAD_H
#define HEAD_H

#include <stdio.h>
#include <math.h>
#include <time.h>
#include <stdlib.h>
#include <omp.h>

#define PI 3.141592653589793238462643383279502884197169399375105820974944592307816406286208998628034825
#define MAX_CHAR 128
#define EPSILON 0.00001 //Will be useful when comparing doubles, to avoid division by zero
#define DIM 2 //Careful if changing this; you'll need to redefine first loop in RunSimulation/7

//=======================================
//Initial constants, S.I.
//=======================================
#define G 6.67430e-11
#define N_BODIES 4

//CAREFUL IF CHANGING PERIHELION DATA!!!!

//Venus - perihelion data:
#define VENUS_RADIUS 1.0
#define COLLISION_DISTANCE 6152000.0 //Venus radius(6052km)+Atmosphere(let's make it ~100 km so as to not lose any energy to drag)
#define VENUS_MASS 4.87e24
#define VENUS_R0_P_X 1.082e11
#define VENUS_R0_P_Y 0.0
#define VENUS_V0_P_X 0.0
#define VENUS_V0_P_Y 35020.0
#define VENUS_INDEX 2

//Earth - initial phase = 0:
#define EARTH_RADIUS 1.0
#define EARTH_MASS 5.97e24
#define EARTH_R0_X 1.47e11
#define EARTH_R0_Y 0.0
#define EARTH_V0_X 0.0
#define EARTH_V0_Y 30300.0
#define EARTH_INDEX 3

//Sun:
#define SUN_RADIUS 1.0
#define SUN_MASS 1.989e30
#define SUN_R0_X 0.0
#define SUN_R0_Y 0.0
#define SUN_V0_X 0.0
#define SUN_V0_Y 0.0
#define SUN_INDEX 1

//Ship:
#define SHIP_MASS 2e4
#define SHIP_R0_X (1.47e11 * (1.0 - 1.0/999.0))
#define SHIP_R0_Y 0.0
#define SHIP_INDEX 0 //Careful if changing this value; change in RumSim Bodies array initialization

//=======================================
//Data Structures & Function Prototypes
//=======================================
typedef struct {
    char name[MAX_CHAR];
    double mass;
    double pos[2];
    double vel[2];
} Body;

//functions.c
double norm(double* vec, int n);
double sqnorm(double* vec, int n);
void vecminus(const double* vec2, const double* vec1, double* result, int n);
double CalculateHamiltonian(Body* bodies, int n);
double ShipHamiltonian(Body* bodies, int n);
double MinimumDistance(Body* bodies, int index);
void CalculateSweep(double min, double max, double* sweep, int n);
void RunSimulation(char* output_folder, double initial_v_ph, double initial_ship_v, double total_time, double factor, 
int sim_id, int skip, int fps, double precision_factor);

//RK4integrator.c
void GravityEngine(double dt, Body* bodies, int n);


#endif