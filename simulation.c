#include "head.h"
#include <string.h>

int main() {
    //=======================================
    //Initial parameters
    //=======================================
    int skip = 100;
    int fps = 80;
    
    double min_v_phase = -0.0032;
    double max_v_phase = -0.0035;
    double min_ship_vel = 25.201667e3;
    double max_ship_vel = 25.201667e3;
    
    double total_t = 1200.0;//days
    double factor = 0.005;//lower values => more precision
    double precision_factor = 80.0;//will divite dt by it when closer than 1e9km
    double max_dt = 10;
    double min_dt = 0.001;
    int total_sims = 20;



    //malloc
    double* venus_phases;
    venus_phases = malloc(total_sims*sizeof(double));
    CalculateSweep(min_v_phase, max_v_phase, venus_phases, total_sims);

    double* ship_velocities;
    ship_velocities = malloc(total_sims*sizeof(double));
    CalculateSweep(min_ship_vel, max_ship_vel, ship_velocities, total_sims);

    //=======================================
    // Main Execution Loop
    //=======================================
    time_t start_time = time(NULL);
    int completed = 0;
    int valid_completed = 0;

    //read .txt from python
    char base_folder[MAX_CHAR] = "simulation_results";
    FILE* config_file = fopen("batch_path.txt", "r");
    if (config_file != NULL) {
        fscanf(config_file, "%s", base_folder);
        fclose(config_file);
    }

    //schedule(dynamic) ensures threads take on a new sim when they finish one
    #pragma omp parallel for schedule(dynamic)
    for (int i=0; i<total_sims; i++) {
        char current_output_folder[MAX_CHAR * 2];
        snprintf(current_output_folder, sizeof(current_output_folder), "%s/sim_%d", base_folder, i+1);

        int status = RunSimulation(current_output_folder, venus_phases[i], ship_velocities[i], total_t, factor, i, skip, fps, precision_factor, max_dt, min_dt);

        #pragma omp critical 
        {
            completed++;
            if (status == 1) {
                valid_completed++;
            }
            
            double completion = (completed*100.0)/total_sims;
            time_t current_time = time(NULL);
            double elapsed = difftime(current_time, start_time);
            
            //Exclude collisions from counting towards ETA
            double eta = 0.0;
            if (valid_completed > 0) {
                double time_per_valid = elapsed/valid_completed;
                eta = time_per_valid*(total_sims-completed);
            }
            
            printf("[%3.0f%%] ETA: %02dm %02ds | Completed Sim ID %d / %d\n", completion, ((int)eta)/60, ((int)eta)%60, i+1, total_sims);
        }
    }
    time_t end_time = time(NULL);
    double total_elapsed = difftime(end_time, start_time);
    printf("[100%%] All simulations completed successfully in %02dm %02ds.\n", ((int)total_elapsed)/60, ((int)total_elapsed)%60);

    free(venus_phases);
    free(ship_velocities);
    return(0);
}