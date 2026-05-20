import defs, graficar

def CalculateHamiltonian(bodies):
    n = len(bodies)
    T = 0.0
    for body in bodies:
        T += 0.5 * body.mass * np.linalg.norm(body.vel)**2
        
    V = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            r = np.linalg.norm(bodies[i].pos - bodies[j].pos)
            if r > 0:
                V += -G*bodies[i].mass*bodies[j].mass/r
                
    return T+V

def ShipHamiltonian(bodies):
    T = 0.5 * bodies[3].mass * np.linalg.norm(bodies[3].vel)**2
    V = 0.0
    for body in bodies:
        r = np.linalg.norm(body.pos-bodies[3].pos)
        if r > 0:
            V += -G*body.mass*bodies[3].mass/r
                
    return T+V

def CalculateSweep(min, max, nsim):
    sweep = np.zeros(nsim)
    rang = abs(max-min)
    if nsim == 1:
        sweep[0] = min + rang/2
    elif nsim > 1:
        step = rang/(nsim-1)
        for i in range(nsim):
            sweep[i] = min + step*i
    
    return(sweep)

def MinimumDistance(bodies, index):
    ship_pos = bodies[3].pos
    venus_pos = bodies[index].pos
    return(np.linalg.norm(ship_pos-venus_pos))

def RunSimulation(output_folder, initial_v_ph, initial_ship_v, total_time, factor, sim_id, skip, fps, gif, precision_factor):
    VENUS_R0 = np.linalg.norm(VENUS_R0_P)*np.array([math.cos(math.radians(initial_v_ph)),math.sin(math.radians(initial_v_ph))])
    VENUS_V0 = np.linalg.norm(VENUS_V0_P)*np.array([-math.sin(math.radians(initial_v_ph)),math.cos(math.radians(initial_v_ph))])

    SHIP_V0 = np.array([0.0, initial_ship_v])
    Earth = Body("Earth", EARTH_MASS, EARTH_R0, EARTH_V0)
    Sun = Body("Sun", SUN_MASS, SUN_R0, SUN_V0)
    Venus = Body("Venus", VENUS_MASS, VENUS_R0, VENUS_V0)
    Ship = Body("Ship", SHIP_MASS, SHIP_R0, SHIP_V0)
    bodies = np.array([Sun, Earth, Venus, Ship])


    history_list = []
    energy_history_list = []
    ship_energy_history_list = []
    time_history_list = []
    simulation_time = 0
    max_time = total_time*24*3600
    min_distance = float('inf')
    dt = 3600

    while simulation_time < max_time:

        energy_history_list.append(CalculateHamiltonian(bodies))
        ship_energy_history_list.append(ShipHamiltonian(bodies))

        venus_dist = MinimumDistance(bodies, 2)
        dt = factor*(venus_dist)**(1/3)
        if dt > 3600:
            dt = 3600
        if dt < 1:
            dt = 1
        if venus_dist < 1e9:
            dt = dt / precision_factor
        
        new_pos, new_vel = GravityEngine(dt, bodies)
        
        if venus_dist < min_distance:
            min_distance = venus_dist
        
        history_list.append(new_pos)
        time_history_list.append(simulation_time/24/3600)

        for j in range(len(bodies)):
            bodies[j].vel = new_vel[j]
            bodies[j].pos = new_pos[j]
        
        simulation_time += dt

    history = np.array(history_list)
    energy_history = np.array(energy_history_list)
    ship_energy_history = np.array(ship_energy_history_list)
    t_vector = np.array(time_history_list)

    final_ship_v = np.linalg.norm(bodies[3].vel)
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        # print(f"\nCreated folder: {output_folder}")

    # =========================================
    # Save Data
    # =========================================
    data_filename = os.path.join(output_folder, f"simulation_data_{sim_id+1}.npz")
    np.savez(data_filename, 
            history=history, 
            energy=energy_history, 
            time=t_vector, 
            total_time = max_time,
            venus_initial_phase = initial_v_ph,
            ship_initial_velocity = initial_ship_v,
            body_names=[b.name for b in bodies])
    
    txt_filename = os.path.join(output_folder, f"simulation_info_{sim_id+1}.txt")
    final_energy_error = (energy_history[-1] - energy_history[0]) / np.abs(energy_history[0])
    with open(txt_filename, "w") as f:
        f.write(f"SIMULATION REPORT - ID {sim_id+1}\n")
        f.write("====================================\n\n")
        
        f.write("Initial conditions:\n")
        f.write(f"  Venus Phase:       {initial_v_ph} degrees\n")
        f.write(f"  Ship Velocity:  {initial_ship_v} m/s\n")
        f.write(f"  Bodies:            {[b.name for b in bodies]}\n\n")
        
        f.write("Time settings:\n")
        f.write(f"  Total Steps:        {len(t_vector)}\n")
        
        f.write("Performance:\n")
        f.write(f"  Factor:  {factor}\n")
        f.write(f"  Precision Factor: {precision_factor}\n")
        f.write(f"  Relative Energy Error: {final_energy_error:.5e}\n")
        f.write(f"  Final Ship Velocity: {round(final_ship_v, 0)} m/s\n")
        f.write(f"  Minimum Ship Distance: {round(min_distance, 0)} m\n")


    # =========================================
    # Plot everything
    # =========================================
    GeneratePlots(output_folder, sim_id, history, energy_history, ship_energy_history, 
                  bodies, initial_v_ph, initial_ship_v, min_distance, final_ship_v, 
                  gif, skip, fps, factor)