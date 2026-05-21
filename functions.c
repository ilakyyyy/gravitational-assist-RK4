#include "head.h"

//Helper functions
double norm(double* vec, int n) {
    double sum = 0.0;
    for(int i=0; i<n; i++) {
        sum += vec[i]*vec[i];
    }
    return(sqrt(sum));
}
double sqnorm(double* vec, int n) {
    double sum = 0.0;
    for(int i=0; i<n; i++) {
        sum += vec[i]*vec[i];
    }
    return(sum);
}
void vecminus(const double* vec2, const double* vec1, double* result, int n) {
    for(int i=0; i<n; i++) result[i] = vec2[i]-vec1[i];
}

double CalculateHamiltonian(Body* bodies, int n) {
    double T, V;
    T = V = 0.0;
    double r[DIM];
    for(int i=0; i<n; i++) {
        T += 0.5 * bodies[i].mass*sqnorm(bodies[i].vel, DIM);
        for(int j=i+1; j<n; j++) {//Avoid counting pairs twice
            vecminus(bodies[i].pos, bodies[j].pos, r, DIM);
            V += -G * bodies[i].mass*bodies[j].mass/norm(r, DIM);
        }
    }
    return(T+V);
}

double ShipHamiltonian(Body* bodies, int n) {
    double T, V, r[DIM];
    T = V = 0.0;
    T = 0.5 * bodies[SHIP_INDEX].mass*sqnorm(bodies[SHIP_INDEX].vel, DIM);
    for(int i=0; i<n; i++) {
        if(i!=SHIP_INDEX) {
            vecminus(bodies[i].pos, bodies[SHIP_INDEX].pos, r, DIM);
            V+= -G * bodies[i].mass*bodies[SHIP_INDEX].mass / norm(r, DIM);
        }
    }
    return(T+V);
}

double MinimumDistance(Body* bodies, int index) {
    double r[DIM];
    vecminus(bodies[SHIP_INDEX].pos, bodies[index].pos, r, DIM);
    return(norm(r, DIM));
}

void CalculateSweep(double min, double max, double* sweep, int n) {
    double range = max - min;
    if (n==1) {
        *sweep = min; // Matching np.linspace behavior for n=1
        return;
    }
    double step = range/(n-1);
    for(int i=0; i<n; i++) *(sweep+i) = min+step*i;
}

void RunSimulation(char* output_folder, double initial_v_ph, double initial_ship_v, double total_time, double factor, 
int sim_id, int skip, int fps, double precision_factor) {
    //Convert phase to radians
    double phase_rad = initial_v_ph * (PI / 180.0);
    double Venus_R0_X = VENUS_R0_P_X * cos(phase_rad);
    double Venus_R0_Y = VENUS_R0_P_X * sin(phase_rad);
    double Venus_V0_X = VENUS_V0_P_Y * -sin(phase_rad);
    double Venus_V0_Y = VENUS_V0_P_Y * cos(phase_rad);

    //Initialize bodies array
    Body bodies[N_BODIES] = {
        [SHIP_INDEX]  = {"Ship",  SHIP_MASS,  {SHIP_R0_X, SHIP_R0_Y},   {0.0, 0.0}},
        [SUN_INDEX]   = {"Sun",   SUN_MASS,   {SUN_R0_X, SUN_R0_Y},     {SUN_V0_X, SUN_V0_Y}},
        [VENUS_INDEX] = {"Venus", VENUS_MASS, {0.0, 0.0},               {0.0, 0.0}},
        [EARTH_INDEX] = {"Earth", EARTH_MASS, {EARTH_R0_X, EARTH_R0_Y}, {EARTH_V0_X, EARTH_V0_Y}}
    };
    
    //Assign the variables generated dynamically so as to keep the compiler happy
    bodies[SHIP_INDEX].vel[1] = initial_ship_v;
    bodies[VENUS_INDEX].pos[0] = Venus_R0_X;
    bodies[VENUS_INDEX].pos[1] = Venus_R0_Y;
    bodies[VENUS_INDEX].vel[0] = Venus_V0_X;
    bodies[VENUS_INDEX].vel[1] = Venus_V0_Y;

    double sim_time = 0.0, dt;
    double max_time = total_time * 24.0 * 3600.0;
    double min_distance = 1e30; //Initialize to a very large number
    
    // Prepare output file paths
    char bin_filename[256];
    char txt_filename[256];
    snprintf(bin_filename, sizeof(bin_filename), "%s/simulation_data_%d.bin", output_folder, sim_id+1);
    snprintf(txt_filename, sizeof(txt_filename), "%s/simulation_info_%d.txt", output_folder, sim_id+1);
    
    FILE* bin_file = fopen(bin_filename, "wb");
    if (bin_file == NULL) {
        printf("Couldn't create output file %s; kake sure the output folder exists.\n", bin_filename);
        return;
    }
    
    long int steps = 0;
    double initial_energy = CalculateHamiltonian(bodies, N_BODIES);
    double final_energy = initial_energy;

    //=======================================
    //Main Simulation Loop
    //=======================================
    while (sim_time < max_time) {
        double current_energy = CalculateHamiltonian(bodies, N_BODIES);
        double current_ship_energy = ShipHamiltonian(bodies, N_BODIES);
        final_energy = current_energy;

        double venus_dist = MinimumDistance(bodies, VENUS_INDEX);
        if (venus_dist < min_distance) {
            min_distance = venus_dist;
        }

        if (venus_dist <= COLLISION_DISTANCE) {
            fclose(bin_file);
            remove(bin_filename);
            
            char new_folder[MAX_CHAR * 2 + 32];
            snprintf(new_folder, sizeof(new_folder), "%s_COLLISION", output_folder);
            rename(output_folder, new_folder);
            return;
        }

        //11 doubles per step:
        //time_days, total_energy, ship_energy, ship_x, ship_y, sun_x, sun_y, venus_x, venus_y, earth_x, earth_y
        double row_data[3+ N_BODIES*2];
        row_data[0] = sim_time/(24.0 * 3600.0); //conversion of time (s) -> (d)
        row_data[1] = current_energy;
        row_data[2] = current_ship_energy;
        for (int i = 0; i < N_BODIES; i++) {
            row_data[3 + 2*i + 0] = bodies[i].pos[0];//x_pos
            row_data[3 + 2*i + 1] = bodies[i].pos[1];//y_pos
        }
        fwrite(row_data, sizeof(double), 3+N_BODIES*2, bin_file);
        steps++;

        //Adaptive step size based on current distance to Venus
        dt = factor * pow(venus_dist, 1.0/3.0);
        if (dt > 3600.0) dt = 3600.0;
        if (dt < 1.0) dt = 1.0;
        if (venus_dist < 1e9) dt /= precision_factor;

        GravityEngine(dt, bodies, N_BODIES);
        sim_time += dt;
    }
    fclose(bin_file);
    
    //=======================================
    //Write Text Info Report
    //=======================================
    FILE* txt_file = fopen(txt_filename, "w");
    if (txt_file == NULL) {
        printf("Couldn't create output file %s; kake sure the output folder exists.\n", txt_filename);
        return;
    }
    double final_ship_v = norm(bodies[SHIP_INDEX].vel, DIM);
    double final_energy_error = (final_energy - initial_energy)/fabs(initial_energy);
    
    fprintf(txt_file, "SIMULATION REPORT - ID %d\n=======================================\n\n", sim_id + 1);
    fprintf(txt_file, "Initial conditions:\n  Venus Phase:       %f degrees\n  Ship Velocity:     %f m/s\n  Bodies:            ['Ship', 'Sun', 'Venus', 'Earth']\n\n", initial_v_ph, initial_ship_v);
    fprintf(txt_file, "Time settings:\n  Total Steps:       %ld\n\nPerformance:\n  Factor:            %f\n  Precision Factor:  %f\n  Relative Energy Error: %.5e\n  Final Ship Velocity:   %.0f m/s\n  Minimum Ship Distance: %.0f m\n", steps, factor, precision_factor, final_energy_error, final_ship_v, min_distance);
    fclose(txt_file);

    return;
}