import old_python.defs as defs, old_python.RK4integrator as RK4integrator, old_python.functions as functions, old_python.graficar as graficar

#Initial parameters, S.I.:
#Ship:
SHIP_MASS = 2e4
SHIP_R0 = np.array([1.47e11*(1-1/999), 0])

#Lots of simulations:
# skip = 500
# fps = 6

#Not many simulations - precision:
skip = 300
fps = 80

#3-4 min to compile with dt = 120s, total_t = 3650d:
# skip = 3600
# fps = 30

# Degrees
min_v_phase = -0.005
max_v_phase = 0.005
min_s_vel = 25.201667e3
max_s_vel = 25.201667e3
# m/s

total_t = 600 #days
#lower values = more precision
factor = 0.6
#higher values = more precision (will divide dt by it when closer than 10^9km)
precision_factor = 1
total_sims = 1
create_gif = True

output_folder = os.path.join("simulation_results", f"Sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}_n{total_sims}_T{total_t}_f{factor}")

for i in tqdm(range(total_sims)):
    #I just learnt there's a function, np.linspace that does this:
    # venus_phases = CalculateSweep(min_v_phase, max_v_phase, total_sims)
    # ship_velocities = CalculateSweep(min_s_vel, max_s_vel, total_sims)
    venus_phases = np.linspace(min_v_phase, max_v_phase, total_sims)
    ship_velocities = np.linspace(min_s_vel, max_s_vel, total_sims)

    RunSimulation(output_folder, venus_phases[i], ship_velocities[i], total_t, factor, i, skip, fps, create_gif, precision_factor)