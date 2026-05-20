#include "head.h"

int main() {
    //=======================================
    //Initial parameters
    //=======================================
    int skip = 300;
    int fps = 80;
    
    double min_v_phase = -0.005;
    double max_v_phase = 0.005;
    double min_ship_vel = 25.201667e3;
    double max_ship_vel = 25.201667e3;
    
    double total_t = 600.0;//days
    double factor = 0.6;//lower values => more precision
    double precision_factor = 1.0;//will divite dt by it when closer than 1e9km
    int total_sims = 1;



    double venus_phases[total_sims];
    double ship_velocities[total_sims];
    CalculateSweep(min_v_phase, max_v_phase, venus_phases, total_sims);
    CalculateSweep(min_ship_vel, max_ship_vel, ship_velocities, total_sims);

    //=======================================
    // Main Execution Loop
    //=======================================
    time_t start_time = time(NULL);
    for (int i=0; i<total_sims; i++) {
        char current_output_folder[MAX_CHAR];
        snprintf(current_output_folder, MAX_CHAR, "simulation_results/sim_%d", i + 1);

        double completion = (i * 100.0) / total_sims;
        if (i == 0) printf("[%3lf%%] ETA: Calculating...    | Running Sim ID %d / %d (Phase: %.4f, Vel: %.0f), output: %s\n", completion, i + 1, total_sims, venus_phases[i], ship_velocities[i], current_output_folder);
        else {
            time_t current_time = time(NULL);
            long double elapsed = difftime(current_time, start_time);
            long double eta = (elapsed/i)*(total_sims-i);
            int eta_mins = ((int)eta)/60;
            int eta_secs = ((int)eta)%60;
            
            printf("[%3lf%%] ETA: %02dm %02ds | Running Sim ID %d / %d (Phase: %.4f, Vel: %.0f), output: %s\n", completion, eta_mins, eta_secs, i + 1, total_sims, venus_phases[i], ship_velocities[i], current_output_folder);
        }
        
        RunSimulation(current_output_folder, venus_phases[i], ship_velocities[i], total_t, factor, i, skip, fps, precision_factor);
    }
    time_t end_time = time(NULL);
    double total_elapsed = difftime(end_time, start_time);
    printf("[100%%] All simulations completed successfully in %02dm %02ds.\n", ((int)total_elapsed) / 60, ((int)total_elapsed) % 60);
    return(0);
}