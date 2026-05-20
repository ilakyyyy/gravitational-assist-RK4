import old_python.defs as defs

# Gravity engine:
# It should take everything before and change everything

# First step: Build the acceleration function (positions -> accelerations)
# Second step: 
# Positions: 1 - Body index; 2 - coord

def CalculateAcceleration(target_pos, att_pos, att_mass):
    r = target_pos - att_pos
    norm = np.linalg.norm(r)
    if norm == 0:
        # print(f"Division by 0!")
        return(np.zeros(2))
    else:
        acc = -G*att_mass*r/(norm**3)
        return(acc)

def TensorialTotalAcceleration(positions, masses, n):
    acc_tensor = np.zeros((n, 2))
    for i in range(n):
        for j in range(n):
            acc_tensor[i, :] += CalculateAcceleration(positions[i], positions[j], masses[j])
    return(acc_tensor)

#For one instant of time
def GravityEngine(dt, bodies):
    n = len(bodies)
    # Sun = bodies[0]
    # Earth = bodies[1]
    # Venus = bodies[2]
    positions = np.zeros((n, 2))
    velocities = np.zeros((n, 2))
    masses = np.zeros(n)
    for i in range(n):
        body = bodies[i]
        positions[i, :] = body.pos
        velocities[i, :] = body.vel
        masses[i] = body.mass
    
    # RK-4 Engine:
    # Calculate k1:
    k1_v = np.zeros((n, 2))
    k1_r = np.zeros((n, 2))

    k1_r = velocities
    k1_v = TensorialTotalAcceleration(positions, masses, n)


    # Calculate k2:
    k2_v = np.zeros((n, 2))
    k2_r = np.zeros((n, 2))
    k2_r_ghost = np.zeros((n, 2))
    
    k2_r_ghost = positions + (k1_r * dt/2)
    k2_r = velocities + (k1_v * dt/2)
    k2_v = TensorialTotalAcceleration(k2_r_ghost, masses, n)


    #Calculate k3:
    k3_v = np.zeros((n, 2))
    k3_r = np.zeros((n, 2))
    k3_r_ghost = np.zeros((n, 2))

    k3_r_ghost = positions + (k2_r* dt/2)
    k3_r = velocities + (k2_v * dt/2)
    k3_v = TensorialTotalAcceleration(k3_r_ghost, masses, n)
        

    #Calculate k4:
    k4_v = np.zeros((n, 2))
    k4_r = np.zeros((n, 2))
    k4_r_ghost = np.zeros((n, 2))

    k4_r_ghost = positions + (k3_r * dt)
    k4_r = velocities + (k3_v * dt)
    k4_v = TensorialTotalAcceleration(k4_r_ghost, masses, n)

    #Calculate new positions & velocities:
    new_positions = positions + dt/6*(k1_r+2*k2_r+2*k3_r+k4_r)
    new_velocities = velocities + dt/6*(k1_v+2*k2_v+2*k3_v+k4_v)
    return(new_positions, new_velocities)