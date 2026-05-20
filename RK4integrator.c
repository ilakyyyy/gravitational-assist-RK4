#include "head.h"

void CalculateAccelerations(int n, double* masses, double* positions, double* accelerations){
    //Initialize to zero
    for (int i=0; i<n; i++){
        accelerations[2*i + 0] = 0.0;
        accelerations[2*i + 1] = 0.0;
    }

    //Pairwise gravitational acceleration
    for (int i=0; i<n; i++){
        for (int j=0; j<n; j++){
            if (i != j){ //Skip self-gravity calculation
                double rx = positions[2*i + 0] - positions[2*j + 0];
                double ry = positions[2*i + 1] - positions[2*j + 1];
                
                double norm = sqrt(rx*rx + ry*ry);
                
                if (norm > EPSILON){
                    double factor = -G * masses[j] / (norm * norm * norm);
                    accelerations[2*i + 0] += factor * rx;
                    accelerations[2*i + 1] += factor * ry;
                }
            }
        }
    }
}

void GravityEngine(double dt, Body* bodies, int n){
    double positions[2*n];
    double velocities[2*n];
    double masses[n];
    
    //Set to current state
    for (int i= 0; i<n; i++){
        positions[2*i + 0] = bodies[i].pos[0];
        positions[2*i + 1] = bodies[i].pos[1];
        velocities[2*i + 0] = bodies[i].vel[0];
        velocities[2*i + 1] = bodies[i].vel[1];
        masses[i] = bodies[i].mass;
    }
    
    //Arrays for RK4 "ghost" states
    double ghost_pos[2*n];
    double k1_v[2*n], k1_r[2*n];
    double k2_v[2*n], k2_r[2*n];
    double k3_v[2*n], k3_r[2*n];
    double k4_v[2*n], k4_r[2*n];

    //k1
    for (int i= 0; i<n; i++){
        k1_r[2*i + 0] = velocities[2*i + 0];
        k1_r[2*i + 1] = velocities[2*i + 1];
    }
    CalculateAccelerations(n, masses, positions, k1_v);

    //k2
    for (int i =0; i<n; i++){
        ghost_pos[2*i + 0] = positions[2*i + 0] + (k1_r[2*i + 0] * dt / 2.0);
        ghost_pos[2*i + 1] = positions[2*i + 1] + (k1_r[2*i + 1] * dt / 2.0);
        k2_r[2*i + 0] = velocities[2*i + 0] + (k1_v[2*i + 0] * dt / 2.0);
        k2_r[2*i + 1] = velocities[2*i + 1] + (k1_v[2*i + 1] * dt / 2.0);
    }
    CalculateAccelerations(n, masses, ghost_pos, k2_v);

    //k3
    for (int i= 0; i<n; i++){
        ghost_pos[2*i + 0] = positions[2*i + 0] + (k2_r[2*i + 0] * dt / 2.0);
        ghost_pos[2*i + 1] = positions[2*i + 1] + (k2_r[2*i + 1] * dt / 2.0);
        k3_r[2*i + 0] = velocities[2*i + 0] + (k2_v[2*i + 0] * dt / 2.0);
        k3_r[2*i + 1] = velocities[2*i + 1] + (k2_v[2*i + 1] * dt / 2.0);
    }
    CalculateAccelerations(n, masses, ghost_pos, k3_v);

    //k4
    for (int i= 0; i<n; i++){
        ghost_pos[2*i + 0] = positions[2*i + 0] + (k3_r[2*i + 0] * dt);
        ghost_pos[2*i + 1] = positions[2*i + 1] + (k3_r[2*i + 1] * dt);
        k4_r[2*i + 0] = velocities[2*i + 0] + (k3_v[2*i + 0] * dt);
        k4_r[2*i + 1] = velocities[2*i + 1] + (k3_v[2*i + 1] * dt);
    }
    CalculateAccelerations(n, masses, ghost_pos, k4_v);

    //Update positions & velocities
    for (int i= 0; i<n; i++){
        bodies[i].pos[0] = positions[2*i + 0] + (dt/6.0)*
        (k1_r[2*i + 0]+
        2.0*k2_r[2*i + 0]+
        2.0*k3_r[2*i + 0]+
        k4_r[2*i + 0]);

        bodies[i].pos[1] = positions[2*i + 1] + (dt/6.0)*
        (k1_r[2*i + 1]+
        2.0*k2_r[2*i + 1]+
        2.0*k3_r[2*i + 1]+
        k4_r[2*i + 1]);

        bodies[i].vel[0] = velocities[2*i + 0] + (dt/6.0)*
        (k1_v[2*i + 0]+
        2.0*k2_v[2*i + 0]+
        2.0*k3_v[2*i + 0]+
        k4_v[2*i + 0]);

        bodies[i].vel[1] = velocities[2*i + 1] + (dt/6.0)*
        (k1_v[2*i + 1]+
        2.0*k2_v[2*i + 1]+
        2.0*k3_v[2*i + 1]+
        k4_v[2*i + 1]);
    }
}